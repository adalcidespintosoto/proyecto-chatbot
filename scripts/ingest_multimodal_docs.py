"""
Pipeline de Ingesta Multimodal con Vision-LLM para UniMon (Universidad Simón Bolívar).

Procesa documentos PDF y PowerPoint (.pptx) con interpretación visual de imágenes incrustadas
(capturas de pantalla, diagramas de flujo, tablas visuales) mediante un Vision-LLM local
(llama3.2-vision:11b vía Ollama).

Funcionalidades:
- Extracción de texto plano + tablas de PDFs y presentaciones PPTX.
- Interpretación semántica de imágenes incrustadas con Vision-LLM.
- Rasterización de páginas escaneadas (PDFs sin texto seleccionable).
- Chunking con solapamiento y persistencia en ChromaDB con embeddings en GPU.
- Reporte de progreso con tqdm y manejo robusto de errores por archivo.

Uso:
    python scripts/ingest_multimodal_docs.py
"""

import os
import sys
import io
import time
import base64
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Tuple

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
import pymupdf as fitz
from PIL import Image
from tqdm import tqdm
from pptx import Presentation
from pptx.util import Emu
from pptx.enum.shapes import MSO_SHAPE_TYPE

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from app.config import get_settings

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("unimon.ingest_multimodal")

# Contadores globales para el reporte final
stats = {
    "files_processed": 0,
    "files_failed": 0,
    "pages_extracted": 0,
    "slides_extracted": 0,
    "images_described": 0,
    "images_skipped": 0,
    "chunks_generated": 0,
    "vision_errors": 0,
}

# Prompt institucional para interpretación visual de imágenes
VISION_PROMPT = (
    "Analiza detalladamente esta imagen de documentación técnica de TI institucional. "
    "- Si es una captura de pantalla de software (Kactus, Seven, GLPI, Windows, portales web, etc.): "
    "describe la ventana activa, menús, botones seleccionados, campos completados y el procedimiento exacto que se muestra. "
    "- Si es un diagrama de flujo o mapa de procesos: describe la secuencia lógica, decisiones, roles y pasos de inicio a fin. "
    "- Si es una tabla: transcribe las columnas, filas y datos relevantes. "
    "- Si contiene texto o mensajes de error: transcribe literalmente los textos clave. "
    "Sé conciso, técnico y estructurado. Responde en español."
)


# =============================================================================
# UTILIDADES Y METADATOS
# =============================================================================

def get_metadata_from_path(file_path: Path) -> dict:
    """Mapea automáticamente los metadatos institucionales según la ubicación del archivo."""
    path_str = str(file_path).lower()
    if "1_estudiantes" in path_str:
        return {"audience": "estudiante", "doc_type": "autoservicio", "source": file_path.name}
    elif "2_profesores" in path_str:
        return {"audience": "profesor", "doc_type": "autoservicio", "source": file_path.name}
    elif "3_funcionarios_gestion" in path_str:
        return {"audience": "funcionario", "doc_type": "gestion_interna", "source": file_path.name}
    elif "4_general_normativa" in path_str:
        return {"audience": "general", "doc_type": "normativa", "source": file_path.name}
    elif "5_admin_ti" in path_str:
        return {"audience": "admin_ti", "doc_type": "gestion_interna", "source": file_path.name}
    return {"audience": "general", "doc_type": "autoservicio", "source": file_path.name}


def normalize_image(image_bytes: bytes, max_size: int = 1024, quality: int = 85) -> bytes:
    """
    Normaliza una imagen redimensionándola y comprimiéndola para no saturar VRAM.
    Retorna bytes JPEG comprimidos.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Convertir a RGB si es necesario (RGBA, paleta, etc.)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        # Redimensionar manteniendo proporciones
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
        # Comprimir a JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()
    except Exception as exc:
        logger.warning(f"Error al normalizar imagen: {exc}")
        return image_bytes


def is_significant_image(image_bytes: bytes, min_kb: int = 15) -> bool:
    """Determina si una imagen es lo suficientemente grande para ser relevante (no un icono)."""
    return len(image_bytes) >= min_kb * 1024


# =============================================================================
# VISION-LLM: INTERPRETACIÓN VISUAL DE IMÁGENES
# =============================================================================

def describe_image_with_vllm(
    image_bytes: bytes,
    filename: str = "image",
    ollama_url: str = "http://localhost:11434",
    vision_model: str = "llama3.2-vision:11b",
    timeout: float = 120.0,
    max_image_size: int = 1024
) -> Optional[str]:
    """
    Envía una imagen al Vision-LLM de Ollama y retorna la descripción textual generada.
    Normaliza la imagen antes del envío para optimizar el uso de VRAM.
    Retorna None si el modelo no está disponible o falla.
    """
    try:
        # Normalizar imagen
        normalized = normalize_image(image_bytes, max_size=max_image_size)
        img_b64 = base64.b64encode(normalized).decode("utf-8")

        payload = {
            "model": vision_model,
            "prompt": VISION_PROMPT,
            "images": [img_b64],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 512
            }
        }

        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{ollama_url}/api/generate", json=payload)

        if response.status_code == 200:
            data = response.json()
            description = data.get("response", "").strip()
            if description:
                logger.debug(f"[Vision-LLM] Imagen '{filename}' descrita ({len(description)} chars)")
                stats["images_described"] += 1
                return description
            else:
                logger.warning(f"[Vision-LLM] Respuesta vacía para imagen '{filename}'")
                stats["vision_errors"] += 1
                return None
        else:
            logger.warning(f"[Vision-LLM] HTTP {response.status_code} al describir '{filename}': {response.text[:200]}")
            stats["vision_errors"] += 1
            return None

    except httpx.ConnectError:
        logger.warning(f"[Vision-LLM] No se pudo conectar a Ollama en {ollama_url}. Continuando sin interpretación visual.")
        stats["vision_errors"] += 1
        return None
    except Exception as exc:
        logger.warning(f"[Vision-LLM] Error al describir imagen '{filename}': {exc}")
        stats["vision_errors"] += 1
        return None


def check_vision_model_available(ollama_url: str, vision_model: str) -> Tuple[bool, str]:
    """
    Verifica si el modelo de visión funciona en Ollama haciendo un smoke test real.
    Intenta el modelo primario, y si falla, prueba fallbacks automáticos.
    Retorna (disponible: bool, modelo_funcional: str).
    """
    FALLBACK_MODELS = [vision_model, "llava:7b", "llava:13b", "llava-llama3:8b"]

    # Crear una imagen de prueba mínima (1x1 pixel rojo)
    test_img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    buffer = io.BytesIO()
    test_img.save(buffer, format="JPEG", quality=50)
    test_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    for model in FALLBACK_MODELS:
        try:
            logger.info(f"[Vision-LLM] Probando modelo '{model}'...")
            payload = {
                "model": model,
                "prompt": "Describe this image in one sentence.",
                "images": [test_b64],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 20}
            }
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(f"{ollama_url}/api/generate", json=payload)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("response", "").strip():
                    logger.info(f"[Vision-LLM] ✅ Modelo '{model}' funciona correctamente.")
                    return True, model
                else:
                    logger.warning(f"[Vision-LLM] Modelo '{model}' respondió vacío.")
            else:
                error_msg = resp.text[:150]
                logger.warning(f"[Vision-LLM] Modelo '{model}' HTTP {resp.status_code}: {error_msg}")
        except httpx.ConnectError:
            logger.warning(f"[Vision-LLM] No se pudo conectar a Ollama en {ollama_url}.")
            return False, vision_model
        except Exception as exc:
            logger.warning(f"[Vision-LLM] Error probando '{model}': {exc}")

    return False, vision_model


# =============================================================================
# PARSER DE POWERPOINT (.pptx)
# =============================================================================

def process_pptx(
    filepath: Path,
    ollama_url: str,
    vision_model: str,
    vision_timeout: float,
    max_image_size: int,
    min_image_kb: int,
    use_vision: bool = True
) -> List[Document]:
    """
    Procesa un archivo PowerPoint extrayendo texto, tablas, notas e imágenes por diapositiva.
    Retorna una lista de Documents de LangChain con metadatos enriquecidos.
    """
    documents = []
    source_name = filepath.name

    try:
        prs = Presentation(str(filepath))
    except Exception as exc:
        logger.error(f"[PPTX] Error al abrir '{source_name}': {exc}")
        stats["files_failed"] += 1
        return documents

    total_slides = len(prs.slides)
    logger.info(f"[PPTX] Procesando '{source_name}': {total_slides} diapositiva(s)")

    for slide_idx, slide in enumerate(prs.slides, 1):
        parts = []
        slide_images_descriptions = []

        # --- Extraer texto de formas ---
        for shape in slide.shapes:
            # Texto de formas con text_frame
            if shape.has_text_frame:
                text = shape.text_frame.text.strip()
                if text:
                    parts.append(text)

            # Tablas estructuradas
            if shape.has_table:
                table = shape.table
                table_text = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    table_text.append(" | ".join(row_cells))
                if table_text:
                    parts.append("[Tabla]\n" + "\n".join(table_text))

            # Imágenes incrustadas
            if use_vision and hasattr(shape, "image") and shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    img_bytes = shape.image.blob
                    if is_significant_image(img_bytes, min_kb=min_image_kb):
                        img_name = f"{source_name}_slide{slide_idx}_img"
                        description = describe_image_with_vllm(
                            img_bytes, img_name,
                            ollama_url=ollama_url,
                            vision_model=vision_model,
                            timeout=vision_timeout,
                            max_image_size=max_image_size
                        )
                        if description:
                            slide_images_descriptions.append(f"[Imagen: {description}]")
                    else:
                        stats["images_skipped"] += 1
                except Exception as exc:
                    logger.debug(f"[PPTX] No se pudo extraer imagen de slide {slide_idx}: {exc}")

        # --- Extraer notas del orador ---
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes_text = slide.notes_slide.notes_text_frame.text.strip()
            if notes_text:
                parts.append(f"[Notas del Orador] {notes_text}")

        # --- Ensamblar contenido de la diapositiva ---
        if slide_images_descriptions:
            parts.extend(slide_images_descriptions)

        full_content = "\n\n".join(parts).strip()
        if full_content:
            meta = get_metadata_from_path(filepath)
            meta.update({
                "slide_number": slide_idx,
                "total_slides": total_slides,
                "type": "presentation",
                "has_images": len(slide_images_descriptions) > 0
            })
            doc = Document(
                page_content=full_content,
                metadata=meta
            )
            documents.append(doc)
            stats["slides_extracted"] += 1

    return documents


# =============================================================================
# PARSER DE PDF (.pdf)
# =============================================================================

def process_pdf(
    filepath: Path,
    ollama_url: str,
    vision_model: str,
    vision_timeout: float,
    max_image_size: int,
    min_image_kb: int,
    use_vision: bool = True
) -> List[Document]:
    """
    Procesa un archivo PDF extrayendo texto seleccionable e imágenes por página.
    Si una página no tiene texto (escaneada), la rasteriza y la envía al Vision-LLM.
    Retorna una lista de Documents de LangChain con metadatos enriquecidos.
    """
    documents = []
    source_name = filepath.name

    try:
        pdf_doc = fitz.open(str(filepath))
    except Exception as exc:
        logger.error(f"[PDF] Error al abrir '{source_name}': {exc}")
        stats["files_failed"] += 1
        return documents

    total_pages = len(pdf_doc)
    logger.info(f"[PDF] Procesando '{source_name}': {total_pages} página(s)")

    for page_idx in range(total_pages):
        page = pdf_doc[page_idx]
        parts = []
        page_images_descriptions = []

        # --- Extraer texto seleccionable ---
        text = page.get_text("text").strip()
        if text:
            parts.append(text)

        # --- Extraer e interpretar imágenes incrustadas ---
        if use_vision:
            image_list = page.get_images(full=True)
            for img_info in image_list:
                xref = img_info[0]
                try:
                    base_image = pdf_doc.extract_image(xref)
                    if base_image:
                        img_bytes = base_image.get("image", b"")
                        if is_significant_image(img_bytes, min_kb=min_image_kb):
                            img_name = f"{source_name}_page{page_idx + 1}_xref{xref}"
                            description = describe_image_with_vllm(
                                img_bytes, img_name,
                                ollama_url=ollama_url,
                                vision_model=vision_model,
                                timeout=vision_timeout,
                                max_image_size=max_image_size
                            )
                            if description:
                                page_images_descriptions.append(f"[Imagen: {description}]")
                        else:
                            stats["images_skipped"] += 1
                except Exception as exc:
                    logger.debug(f"[PDF] No se pudo extraer imagen xref={xref} en página {page_idx + 1}: {exc}")

            # --- Rasterizar página completa si no hay texto nativo (escaneada) ---
            if not text and not page_images_descriptions:
                try:
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("jpeg")
                    img_name = f"{source_name}_page{page_idx + 1}_raster"
                    description = describe_image_with_vllm(
                        img_bytes, img_name,
                        ollama_url=ollama_url,
                        vision_model=vision_model,
                        timeout=vision_timeout,
                        max_image_size=max_image_size
                    )
                    if description:
                        page_images_descriptions.append(f"[Página Escaneada: {description}]")
                except Exception as exc:
                    logger.debug(f"[PDF] No se pudo rasterizar página {page_idx + 1}: {exc}")

        # --- Ensamblar contenido de la página ---
        if page_images_descriptions:
            parts.extend(page_images_descriptions)

        full_content = "\n\n".join(parts).strip()
        if full_content:
            meta = get_metadata_from_path(filepath)
            meta.update({
                "page_number": page_idx + 1,
                "total_pages": total_pages,
                "type": "pdf_document",
                "has_images": len(page_images_descriptions) > 0
            })
            doc = Document(
                page_content=full_content,
                metadata=meta
            )
            documents.append(doc)
            stats["pages_extracted"] += 1

    pdf_doc.close()
    return documents


# =============================================================================
# ORQUESTADOR PRINCIPAL DE INGESTA MULTIMODAL
# =============================================================================

def ingest_multimodal(docs_path: str = None, chroma_path: str = None, model_name: str = None) -> bool:
    """
    Pipeline completo de ingesta multimodal:
    1. Escanea ./data/docs/ recursivamente buscando .pdf y .pptx
    2. Procesa cada archivo con interpretación visual (Vision-LLM)
    3. Aplica chunking con solapamiento
    4. Genera embeddings en GPU y persiste en ChromaDB
    5. Imprime reporte resumen de la ingesta
    """
    settings = get_settings()
    docs_dir = Path(docs_path or settings.docs_dir)
    chroma_dir = Path(chroma_path or settings.chroma_db_dir)
    embedding_model_name = model_name or settings.embedding_model
    ollama_url = settings.ollama_base_url
    vision_model = settings.vision_model
    vision_timeout = settings.vision_timeout
    max_image_size = settings.vision_max_image_size
    min_image_kb = settings.vision_min_image_kb

    # Resetear contadores
    for key in stats:
        stats[key] = 0

    logger.info("=" * 70)
    logger.info(" INGESTA MULTIMODAL DE DOCUMENTOS INSTITUCIONALES - UNISIMON COLOMBIA")
    logger.info("=" * 70)
    logger.info(f"Directorio de Documentos: {docs_dir.resolve()}")
    logger.info(f"Directorio de ChromaDB:   {chroma_dir.resolve()}")
    logger.info(f"Modelo de Embeddings:     {embedding_model_name}")
    logger.info(f"Modelo de Visión (LLM):   {vision_model}")
    logger.info(f"Ollama URL:               {ollama_url}")

    # 1. Asegurar existencia del directorio de documentos
    if not docs_dir.exists():
        logger.info(f"Creando directorio de documentos: {docs_dir}")
        docs_dir.mkdir(parents=True, exist_ok=True)

    # 2. Escanear archivos soportados (.pdf y .pptx) recursivamente
    pdf_files = sorted(docs_dir.rglob("*.pdf"))
    pptx_files = sorted(docs_dir.rglob("*.pptx"))
    all_files = sorted(pdf_files + pptx_files)

    if not all_files:
        logger.warning(
            f"[!] No se encontraron archivos PDF ni PPTX en '{docs_dir}' ni en sus subcarpetas.\n"
            f"Asegúrate de colocar los documentos institucionales en '{docs_dir}'."
        )
        return False

    logger.info(f"Archivos encontrados: {len(pdf_files)} PDF(s) + {len(pptx_files)} PPTX = {len(all_files)} total")
    for idx, f in enumerate(all_files, 1):
        try:
            rel_path = f.relative_to(docs_dir)
        except ValueError:
            rel_path = f.name
        logger.info(f"  [{idx}/{len(all_files)}] {rel_path} ({f.stat().st_size / 1024:.1f} KB)")

    # 3. Verificar disponibilidad del modelo de visión (con smoke test y fallback automático)
    use_vision, active_vision_model = check_vision_model_available(ollama_url, vision_model)
    if use_vision:
        if active_vision_model != vision_model:
            logger.info(f"⚠️ Modelo primario '{vision_model}' no disponible. Usando fallback: '{active_vision_model}'")
        logger.info(f"✅ Vision-LLM '{active_vision_model}' operativo. Se interpretarán imágenes incrustadas.")
        vision_model = active_vision_model
    else:
        logger.warning(
            f"⚠️ Ningún Vision-LLM disponible en Ollama. "
            f"La ingesta continuará con extracción de texto plano únicamente (sin interpretación visual). "
            f"Para habilitar visión, ejecuta: ollama pull llava:7b"
        )

    # 4. Limpiar base vectorial previa
    if chroma_dir.exists():
        logger.info(f"Limpiando base vectorial previa en '{chroma_dir}'...")
        try:
            shutil.rmtree(chroma_dir)
            logger.info("Directorio ChromaDB previo eliminado con éxito.")
        except Exception as exc:
            logger.warning(f"No se pudo eliminar directorio completo ({exc}), se procederá a sobrescribir.")

    chroma_dir.mkdir(parents=True, exist_ok=True)

    # 5. Procesar todos los archivos con barra de progreso
    all_documents: List[Document] = []
    start_time = time.time()

    for filepath in tqdm(all_files, desc="📂 Procesando documentos", unit="archivo"):
        try:
            ext = filepath.suffix.lower()
            if ext == ".pdf":
                docs = process_pdf(
                    filepath,
                    ollama_url=ollama_url,
                    vision_model=vision_model,
                    vision_timeout=vision_timeout,
                    max_image_size=max_image_size,
                    min_image_kb=min_image_kb,
                    use_vision=use_vision
                )
            elif ext == ".pptx":
                docs = process_pptx(
                    filepath,
                    ollama_url=ollama_url,
                    vision_model=vision_model,
                    vision_timeout=vision_timeout,
                    max_image_size=max_image_size,
                    min_image_kb=min_image_kb,
                    use_vision=use_vision
                )
            else:
                logger.warning(f"Formato no soportado: {filepath.name}")
                continue

            all_documents.extend(docs)
            stats["files_processed"] += 1
        except Exception as exc:
            logger.error(f"❌ Error procesando '{filepath.name}': {exc}")
            stats["files_failed"] += 1

    if not all_documents:
        logger.error("No se generaron documentos para indexar. Revisa los archivos fuente.")
        return False

    logger.info(f"Total de documentos extraídos antes de chunking: {len(all_documents)}")

    # 6. Fragmentar documentos (chunking con solapamiento)
    chunk_size = 800
    chunk_overlap = 150
    logger.info(f"Fragmentando documentos (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(all_documents)
    stats["chunks_generated"] = len(chunks)
    logger.info(f"Total de fragmentos generados: {stats['chunks_generated']}")

    # 7. Inicializar modelo de embeddings (GPU si disponible)
    logger.info(f"Cargando modelo de embeddings '{embedding_model_name}'...")

    # Detectar dispositivo disponible
    device = "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_mem / (1024 ** 3)
            logger.info(f"🖥️ GPU detectada: {gpu_name} ({vram_gb:.1f} GB VRAM) — Embeddings en CUDA")
        else:
            logger.info("GPU CUDA no disponible. Embeddings en CPU.")
    except ImportError:
        logger.info("PyTorch no instalado. Embeddings en CPU.")

    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_model_name,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True}
    )

    # 8. Indexar y persistir en ChromaDB
    logger.info(f"Generando embeddings e indexando {stats['chunks_generated']} fragmentos en ChromaDB...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(chroma_dir)
    )

    elapsed_time = time.time() - start_time

    # 9. Reporte final
    logger.info("=" * 70)
    logger.info(" [ÉXITO] INGESTA MULTIMODAL COMPLETADA")
    logger.info("=" * 70)
    logger.info(f" • Archivos procesados:       {stats['files_processed']} ({stats['files_failed']} con error)")
    logger.info(f" • Páginas PDF extraídas:      {stats['pages_extracted']}")
    logger.info(f" • Diapositivas PPTX extraídas:{stats['slides_extracted']}")
    logger.info(f" • Imágenes interpretadas:     {stats['images_described']} ({stats['images_skipped']} descartadas por tamaño)")
    logger.info(f" • Errores de Vision-LLM:      {stats['vision_errors']}")
    logger.info(f" • Fragmentos indexados:        {stats['chunks_generated']}")
    logger.info(f" • Tiempo total:               {elapsed_time:.1f} segundos ({elapsed_time / 60:.1f} min)")
    logger.info(f" • Base vectorial en:          {chroma_dir.resolve()}")
    logger.info(f" • Dispositivo de embeddings:  {device.upper()}")
    if use_vision:
        logger.info(f" • Vision-LLM utilizado:       {vision_model}")
    else:
        logger.info(f" • Vision-LLM:                 NO DISPONIBLE (solo texto plano)")
    logger.info("=" * 70)

    return True


if __name__ == "__main__":
    success = ingest_multimodal()
    sys.exit(0 if success else 1)
