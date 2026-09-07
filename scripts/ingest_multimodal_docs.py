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

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
    "chunks_deduplicated": 0,
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
    elif "3_funcionarios_gestion" in path_str or "administrativo" in path_str:
        return {"audience": "administrativo", "doc_type": "gestion_interna", "source": file_path.name}
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
# UTILIDADES DE PERSISTENCIA INCREMENTAL Y CHUNKS EN CHROMADB
# =============================================================================

def get_existing_sources(vector_store: Chroma) -> set:
    """Retorna el conjunto de nombres de archivos ('source') ya indexados en ChromaDB."""
    try:
        results = vector_store._collection.get(include=["metadatas"])
        metas = results.get("metadatas", []) or []
        sources = {m.get("source") for m in metas if m and "source" in m}
        return sources
    except Exception as exc:
        logger.warning(f"No se pudieron consultar metadatos existentes en ChromaDB: {exc}")
        return set()


def delete_document_chunks(vector_store: Chroma, doc_source: str) -> int:
    """Elimina de ChromaDB todos los fragmentos cuyo metadato 'source' coincida con doc_source."""
    try:
        collection = vector_store._collection
        results = collection.get(where={"source": doc_source})
        existing_ids = results.get("ids", [])
        if existing_ids:
            collection.delete(ids=existing_ids)
            logger.info(f"🗑️ Eliminados {len(existing_ids)} fragmentos de '{doc_source}' en ChromaDB.")
            return len(existing_ids)
        else:
            logger.debug(f"No se encontraron fragmentos previos para '{doc_source}'.")
            return 0
    except Exception as exc:
        logger.warning(f"Error al eliminar fragmentos de '{doc_source}': {exc}")
        return 0


def generate_deterministic_chunk_ids(chunks: List[Document]) -> List[str]:
    """
    Genera IDs deterministas para cada chunk en formato:
    f"{file_stem}_p{page_num}_c{chunk_idx}"
    """
    import re
    ids = []
    page_chunk_counts = {}

    for chunk in chunks:
        source_name = chunk.metadata.get("source", "doc")
        file_stem = Path(source_name).stem
        clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", file_stem)

        page_num = (
            chunk.metadata.get("page_number")
            or chunk.metadata.get("slide_number")
            or 1
        )

        key = (source_name, page_num)
        chunk_idx = page_chunk_counts.get(key, 0)
        page_chunk_counts[key] = chunk_idx + 1

        chunk_id = f"{clean_stem}_p{page_num}_c{chunk_idx}"
        ids.append(chunk_id)

    return ids


# =============================================================================
# DETECCIÓN DE REDUNDANCIA Y CONTROL DE ADMISIÓN (PRE-FLIGHT CHECK)
# =============================================================================

def calculate_chunk_redundancy(
    chunks: List[Document],
    vector_store: Chroma,
    embeddings: HuggingFaceEmbeddings,
    threshold: float = 0.88,
    exclude_source: Optional[str] = None,
    batch_size: int = 32
) -> dict:
    """
    Evalúa la redundancia semántica de una lista de fragmentos contra ChromaDB.
    Usa embeddings normalizados: Similitud Coseno = 1.0 - distancia.
    """
    total_chunks = len(chunks)
    if total_chunks == 0:
        return {
            "total_chunks": 0,
            "redundant_count": 0,
            "novel_count": 0,
            "redundancy_ratio": 0.0,
            "overlapping_sources": {},
            "redundant_indices": set(),
            "novel_indices": set(),
            "chunk_results": []
        }

    try:
        col = vector_store._collection
        col_count = col.count()
    except Exception:
        col = None
        col_count = 0

    if col_count == 0 or col is None:
        return {
            "total_chunks": total_chunks,
            "redundant_count": 0,
            "novel_count": total_chunks,
            "redundancy_ratio": 0.0,
            "overlapping_sources": {},
            "redundant_indices": set(),
            "novel_indices": set(range(total_chunks)),
            "chunk_results": [{"chunk": c, "similarity": 0.0, "matched_source": None, "is_redundant": False} for c in chunks]
        }

    texts = [c.page_content for c in chunks]
    chunk_embeddings = embeddings.embed_documents(texts)

    redundant_indices = set()
    novel_indices = set()
    overlapping_sources = {}
    chunk_results = []

    n_results = min(5 if exclude_source else 1, col_count)

    for start_idx in range(0, total_chunks, batch_size):
        batch_embs = chunk_embeddings[start_idx:start_idx + batch_size]
        batch_chunks = chunks[start_idx:start_idx + batch_size]

        try:
            results = col.query(
                query_embeddings=batch_embs,
                n_results=n_results,
                include=["distances", "metadatas"]
            )
        except Exception as exc:
            logger.warning(f"Error consultando ChromaDB para redundancia: {exc}")
            continue

        for i, chunk in enumerate(batch_chunks):
            global_idx = start_idx + i
            distances = results["distances"][i] if i < len(results["distances"]) else []
            metadatas = results["metadatas"][i] if i < len(results["metadatas"]) else []

            best_dist = 999.0
            best_meta = {}
            for dist, meta in zip(distances, metadatas):
                src = meta.get("source") if meta else ""
                if exclude_source and src == exclude_source:
                    continue
                best_dist = dist
                best_meta = meta or {}
                break

            similarity = max(0.0, 1.0 - best_dist) if best_dist < 900.0 else 0.0
            matched_src = best_meta.get("source", "desconocido") if best_meta else None

            is_redundant = (similarity >= threshold) and (matched_src is not None)

            if is_redundant:
                redundant_indices.add(global_idx)
                if matched_src not in overlapping_sources:
                    overlapping_sources[matched_src] = {
                        "count": 0,
                        "max_similarity": 0.0,
                        "sample_snippet": chunk.page_content[:100].strip()
                    }
                overlapping_sources[matched_src]["count"] += 1
                overlapping_sources[matched_src]["max_similarity"] = max(
                    overlapping_sources[matched_src]["max_similarity"],
                    similarity
                )
            else:
                novel_indices.add(global_idx)

            chunk_results.append({
                "chunk": chunk,
                "similarity": similarity,
                "matched_source": matched_src,
                "is_redundant": is_redundant
            })

    redundancy_ratio = (len(redundant_indices) / total_chunks) * 100.0 if total_chunks > 0 else 0.0

    return {
        "total_chunks": total_chunks,
        "redundant_count": len(redundant_indices),
        "novel_count": len(novel_indices),
        "redundancy_ratio": redundancy_ratio,
        "overlapping_sources": overlapping_sources,
        "redundant_indices": redundant_indices,
        "novel_indices": novel_indices,
        "chunk_results": chunk_results
    }


def print_redundancy_report(
    target_name: str,
    report: dict,
    threshold: float = 0.88
) -> None:
    """Imprime en consola un reporte visual con semáforo sobre la redundancia del documento."""
    total = report["total_chunks"]
    redundant = report["redundant_count"]
    novel = report["novel_count"]
    ratio = report["redundancy_ratio"]
    overlaps = report["overlapping_sources"]

    sorted_sources = sorted(overlaps.items(), key=lambda x: x[1]["count"], reverse=True)

    print("\n" + "=" * 70)
    print(" 🔍 AUDITORÍA DE REDUNDANCIA DOCUMENTAL (PRE-INGESTA) - UNIMON")
    print("=" * 70)
    print(f" Documento evaluado:     {target_name}")
    print(f" Fragmentos generados:   {total}")
    print(f" Umbral de redundancia:  >= {threshold:.0%} de similitud semántica")
    print("-" * 70)
    print(" 📊 BALANCE DE CONTENIDO:")
    print(f"   • Fragmentos Nuevos (Aportan valor):       {novel:>3} ({100.0 - ratio:>5.1f}%)")
    print(f"   • Fragmentos Redundantes (Ya indexados):   {redundant:>3} ({ratio:>5.1f}%)")
    print("-" * 70)

    if ratio < 25.0:
        print(" 🟢 DIAGNÓSTICO: [BAJA REDUNDANCIA / CONOCIMIENTO NUEVO]")
        print("    El documento contiene principalmente procedimientos o datos no registrados.")
        print("    💡 Recomendación: Aprobado para indexación normal sin riesgo de saturación.")
    elif ratio < 70.0:
        print(" 🟡 DIAGNÓSTICO: [REDUNDANCIA MODERADA / SOLAPAMIENTO PARCIAL]")
        print("    El documento comparte bases normativas o encabezados con otros existentes,")
        print("    pero incluye secciones nuevas y específicas.")
        print("    💡 Recomendación: Utiliza el flag '--deduplicate' para omitir los fragmentos")
        print("       duplicados y guardar exclusivamente el contenido novedoso.")
    else:
        print(" 🔴 DIAGNÓSTICO: [ALTA REDUNDANCIA / DOCUMENTO DUPLICADO O VERSIÓN ANTERIOR]")
        print("    Más del 70% del documento ya se encuentra cubierto por la base de datos.")
        print("    💡 Recomendación:")
        print("       - Si es una versión actualizada (ej. 2024 que reemplaza 2023):")
        print("         Elimina primero el documento viejo con '--delete-doc <archivo_viejo>'")
        print("         antes de cargar este.")
        print("       - Si no es una versión nueva, descarta la indexación para evitar saturación.")

    if sorted_sources:
        print("\n 📁 Documentos existentes que ya contienen esta información:")
        for idx, (src_name, info) in enumerate(sorted_sources[:5], 1):
            pct_overlap = (info["count"] / total) * 100.0 if total > 0 else 0.0
            print(f"    {idx}. {src_name}")
            print(f"       Coincidencia: {info['count']} fragmentos ({pct_overlap:.1f}% del documento)")
            print(f"       Similitud máxima observada: {info['max_similarity'] * 100.0:.1f}%\n")

    print("=" * 70 + "\n")


def audit_chroma_database_redundancy(
    vector_store: Chroma,
    embeddings: HuggingFaceEmbeddings,
    threshold: float = 0.88,
    min_overlap_chunks: int = 2
) -> None:
    """
    Escanea la base de datos ChromaDB completa y detecta pares de documentos existentes
    que tienen alta redundancia entre sí.
    """
    print("\n" + "=" * 70)
    print(" 📋 AUDITORÍA GLOBAL DE REDUNDANCIA EN CHROMADB - UNISIMON")
    print("=" * 70)

    try:
        col = vector_store._collection
        count = col.count()
        print(f" Total de fragmentos indexados en la colección: {count}")
        if count == 0:
            print(" La base de datos está vacía. No hay fragmentos que auditar.")
            print("=" * 70 + "\n")
            return

        all_data = col.get(include=["metadatas", "documents"])
        metadatas = all_data.get("metadatas", []) or []
        documents = all_data.get("documents", []) or []
        ids = all_data.get("ids", []) or []

        docs_by_source = {}
        for doc_id, meta, text in zip(ids, metadatas, documents):
            src = meta.get("source", "desconocido") if meta else "desconocido"
            if src not in docs_by_source:
                docs_by_source[src] = []
            docs_by_source[src].append({"id": doc_id, "text": text, "meta": meta})

        total_sources = len(docs_by_source)
        print(f" Documentos fuente registrados: {total_sources}")
        print(f" Umbral de solapamiento semántico: >= {threshold:.0%}")
        print("-" * 70)
        print(" Analizando solapamiento cruzado entre documentos...")

        overlap_matrix = {}

        for src, chunk_list in tqdm(docs_by_source.items(), desc="Auditoría de Colección", unit="doc"):
            sample_texts = [c["text"] for c in chunk_list]
            sample_embeddings = embeddings.embed_documents(sample_texts)
            res = col.query(
                query_embeddings=sample_embeddings,
                n_results=min(5, count),
                include=["distances", "metadatas"]
            )
            for distances, metas in zip(res["distances"], res["metadatas"]):
                for dist, meta in zip(distances, metas):
                    other_src = meta.get("source") if meta else None
                    if not other_src or other_src == src:
                        continue
                    sim = 1.0 - dist
                    if sim >= threshold:
                        pair = tuple(sorted([src, other_src]))
                        if pair not in overlap_matrix:
                            overlap_matrix[pair] = {"count": 0, "max_sim": 0.0}
                        overlap_matrix[pair]["count"] += 1
                        overlap_matrix[pair]["max_sim"] = max(overlap_matrix[pair]["max_sim"], sim)

        significant_overlaps = [
            (pair, data) for pair, data in overlap_matrix.items()
            if data["count"] >= min_overlap_chunks
        ]
        significant_overlaps.sort(key=lambda x: x[1]["count"], reverse=True)

        if not significant_overlaps:
            print("\n ✅ No se encontraron pares de documentos con redundancia crítica.")
        else:
            print(f"\n ⚠️ Se detectaron {len(significant_overlaps)} pares con solapamiento significativo (>= {min_overlap_chunks} chunks):\n")
            for idx, ((doc_a, doc_b), data) in enumerate(significant_overlaps, 1):
                len_a = len(docs_by_source.get(doc_a, []))
                len_b = len(docs_by_source.get(doc_b, []))
                print(f" {idx:2d}. [{data['max_sim']*100:.1f}% similitud máx | {data['count']} fragmentos solapados]")
                print(f"     • Doc A ({len_a} chunks): {doc_a}")
                print(f"     • Doc B ({len_b} chunks): {doc_b}")

        print("\n" + "=" * 70 + "\n")
    except Exception as exc:
        logger.error(f"Error durante la auditoría global de ChromaDB: {exc}", exc_info=True)


# =============================================================================
# ORQUESTADOR PRINCIPAL DE INGESTA MULTIMODAL E INCREMENTAL
# =============================================================================

def ingest_multimodal(
    docs_path: Optional[str] = None,
    chroma_path: Optional[str] = None,
    model_name: Optional[str] = None,
    file_path: Optional[str] = None,
    incremental: bool = False,
    delete_doc: Optional[str] = None,
    wipe_db: bool = False,
    check_redundancy: bool = False,
    deduplicate: bool = False,
    similarity_threshold: float = 0.88,
    audit_db: bool = False
) -> bool:
    """
    Pipeline de ingesta multimodal con soporte para:
    - Auditoría de redundancia (--check-redundancy): evaluación previa segura (dry-run).
    - Deduplicación activa (--deduplicate): descarta chunks redundantes antes del upsert.
    - Auditoría global de BD (--audit-db): detecta solapamiento entre documentos cargados.
    - Ingesta incremental (--incremental): procesa solo documentos no indexados.
    - Ingesta de archivo único (--file <ruta>): agrega o actualiza solo ese archivo.
    - Eliminación de documento (--delete-doc <nombre>): borra todos los chunks del archivo.
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
    logger.info(" INGESTA MULTIMODAL E INCREMENTAL - UNISIMON COLOMBIA")
    logger.info("=" * 70)
    logger.info(f"Directorio de Documentos: {docs_dir.resolve()}")
    logger.info(f"Directorio de ChromaDB:   {chroma_dir.resolve()}")
    logger.info(f"Modelo de Embeddings:     {embedding_model_name}")
    logger.info(f"Modelo de Visión (LLM):   {vision_model}")
    logger.info(f"Ollama URL:               {ollama_url}")

    # Inicializar modelo de embeddings (GPU si disponible)
    logger.info(f"Inicializando modelo de embeddings '{embedding_model_name}'...")
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
        model_kwargs={"device": device, "local_files_only": True},
        encode_kwargs={"normalize_embeddings": True}
    )

    chroma_dir.mkdir(parents=True, exist_ok=True)

    # 1. CASO: Eliminación explícita de documento
    if delete_doc:
        logger.info(f"Eliminando documento '{delete_doc}' de ChromaDB...")
        vector_store = Chroma(
            persist_directory=str(chroma_dir),
            embedding_function=embeddings
        )
        deleted = delete_document_chunks(vector_store, delete_doc)
        logger.info(f"✅ Operación de borrado completada: {deleted} fragmentos eliminados.")
        return True

    # 2. CASO: Limpieza forzada de base vectorial previa si se solicita wipe
    if wipe_db and chroma_dir.exists():
        logger.info(f"Limpiando base vectorial completa previa en '{chroma_dir}'...")
        try:
            shutil.rmtree(chroma_dir)
            logger.info("Directorio ChromaDB previo eliminado con éxito.")
        except Exception as exc:
            logger.warning(f"No se pudo eliminar directorio completo ({exc}), se procederá a sobrescribir.")
        chroma_dir.mkdir(parents=True, exist_ok=True)

    vector_store = Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=embeddings
    )

    # 2.1 CASO: Auditoría global de redundancia en la base de datos existente
    if audit_db:
        audit_chroma_database_redundancy(
            vector_store=vector_store,
            embeddings=embeddings,
            threshold=similarity_threshold
        )
        return True

    # 3. Determinar lista de archivos a procesar
    if file_path:
        target = Path(file_path)
        if not target.exists():
            logger.error(f"El archivo especificado no existe: {target.resolve()}")
            return False
        if target.suffix.lower() not in (".pdf", ".pptx"):
            logger.error(f"Formato no soportado para archivo individual: {target.name}")
            return False
        all_files = [target]
        logger.info(f"🎯 Modo Archivo Único: Procesando únicamente '{target.name}'")
    else:
        if not docs_dir.exists():
            logger.info(f"Creando directorio de documentos: {docs_dir}")
            docs_dir.mkdir(parents=True, exist_ok=True)

        pdf_files = sorted(docs_dir.rglob("*.pdf"))
        pptx_files = sorted(docs_dir.rglob("*.pptx"))
        all_files = sorted(pdf_files + pptx_files)

        if not all_files:
            logger.warning(
                f"[!] No se encontraron archivos PDF ni PPTX en '{docs_dir}' ni en sus subcarpetas.\n"
                f"Asegúrate de colocar los documentos institucionales en '{docs_dir}'."
            )
            return False

        logger.info(f"Archivos totales en disco: {len(pdf_files)} PDF(s) + {len(pptx_files)} PPTX = {len(all_files)} total")

        if incremental and not wipe_db:
            existing_sources = get_existing_sources(vector_store)
            logger.info(f"🔄 Modo Incremental: {len(existing_sources)} documento(s) ya presentes en ChromaDB.")
            all_files = [f for f in all_files if f.name not in existing_sources]
            if not all_files:
                logger.info("✅ Todos los documentos ya se encuentran indexados en ChromaDB. No hay archivos nuevos por procesar.")
                return True
            logger.info(f"Archivos nuevos a indexar ({len(all_files)}): {[f.name for f in all_files]}")

    # 4. Verificar disponibilidad del modelo de visión
    use_vision, active_vision_model = check_vision_model_available(ollama_url, vision_model)
    if use_vision:
        if active_vision_model != vision_model:
            logger.info(f"⚠️ Modelo primario '{vision_model}' no disponible. Usando fallback: '{active_vision_model}'")
        logger.info(f"✅ Vision-LLM '{active_vision_model}' operativo. Se interpretarán imágenes incrustadas.")
        vision_model = active_vision_model
    else:
        logger.warning(
            f"⚠️ Ningún Vision-LLM disponible en Ollama. "
            f"La ingesta continuará con extracción de texto plano únicamente (sin interpretación visual)."
        )

    # 5. Procesar los archivos seleccionados
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

    logger.info(f"Total de documentos/páginas extraídas antes de chunking: {len(all_documents)}")

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

    # 7. Si se solicitó auditoría previa de redundancia (Dry-Run / Pre-Flight Check)
    if check_redundancy:
        logger.info("🔍 Ejecutando auditoría de redundancia previa a la ingesta (Dry-Run)...")
        for f in all_files:
            file_chunks = [c for c in chunks if c.metadata.get("source") == f.name]
            if not file_chunks:
                continue
            rep = calculate_chunk_redundancy(
                chunks=file_chunks,
                vector_store=vector_store,
                embeddings=embeddings,
                threshold=similarity_threshold,
                exclude_source=f.name
            )
            print_redundancy_report(f.name, rep, threshold=similarity_threshold)
        logger.info("✅ Auditoría de redundancia completada. No se modificó la base de datos ChromaDB.")
        return True

    # 8. Deduplicación activa durante la ingesta (si se solicitó --deduplicate)
    if deduplicate:
        logger.info(f"🛡️ Modo Deduplicación Activa (Umbral >= {similarity_threshold:.0%}): Filtrando fragmentos redundantes...")
        filtered_chunks = []
        total_deduped = 0
        for f in all_files:
            file_chunks = [c for c in chunks if c.metadata.get("source") == f.name]
            if not file_chunks:
                continue
            rep = calculate_chunk_redundancy(
                chunks=file_chunks,
                vector_store=vector_store,
                embeddings=embeddings,
                threshold=similarity_threshold,
                exclude_source=f.name
            )
            novel = [c for idx, c in enumerate(file_chunks) if idx not in rep["redundant_indices"]]
            deduped_count = rep["redundant_count"]
            total_deduped += deduped_count
            if deduped_count > 0:
                logger.info(
                    f"   • '{f.name}': {len(novel)}/{len(file_chunks)} fragmentos novedosos conservados "
                    f"({deduped_count} redundantes descartados)."
                )
            filtered_chunks.extend(novel)

        stats["chunks_deduplicated"] = total_deduped
        chunks = filtered_chunks
        stats["chunks_generated"] = len(chunks)

        if not chunks:
            logger.warning("⚠️ Todos los fragmentos procesados superaron el umbral de redundancia con documentos ya existentes.")
            logger.warning("   No se indexó ningún fragmento para evitar saturación de la base vectorial.")
            return True

    # 9. Limpiar chunks anteriores de los archivos a procesar para evitar huérfanos
    for f in all_files:
        delete_document_chunks(vector_store, f.name)

    # 10. Indexar con upsert determinista en ChromaDB
    texts = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]
    ids = generate_deterministic_chunk_ids(chunks)

    logger.info(f"Generando embeddings e indexando {len(chunks)} fragmentos con upsert en ChromaDB...")
    embeddings_list = embeddings.embed_documents(texts)
    vector_store._collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings_list
    )

    elapsed_time = time.time() - start_time

    # 11. Reporte final
    logger.info("=" * 70)
    logger.info(" [ÉXITO] INGESTA COMPLETADA")
    logger.info("=" * 70)
    logger.info(f" • Archivos procesados:       {stats['files_processed']} ({stats['files_failed']} con error)")
    logger.info(f" • Páginas PDF extraídas:      {stats['pages_extracted']}")
    logger.info(f" • Diapositivas PPTX extraídas:{stats['slides_extracted']}")
    logger.info(f" • Imágenes interpretadas:     {stats['images_described']} ({stats['images_skipped']} descartadas por tamaño)")
    dedup_info = f" ({stats['chunks_deduplicated']} descartados por redundancia)" if stats.get("chunks_deduplicated", 0) > 0 else ""
    logger.info(f" • Fragmentos indexados:        {stats['chunks_generated']}{dedup_info}")
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
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline de Ingesta Multimodal e Incremental de Documentos en ChromaDB (UniMon)"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Ruta de un archivo individual (.pdf o .pptx) para procesar e indexar"
    )
    parser.add_argument(
        "--incremental", "-i",
        action="store_true",
        help="Escanear data/docs/ e indexar únicamente documentos que no existan en ChromaDB"
    )
    parser.add_argument(
        "--delete-doc", "-d",
        type=str,
        default=None,
        help="Eliminar todos los fragmentos de un documento específico por su nombre (ej. P-GT-01_Mantenimiento.pdf)"
    )
    parser.add_argument(
        "--wipe", "-w",
        action="store_true",
        help="Forzar eliminación completa de la base de datos ChromaDB antes de reindexar"
    )
    parser.add_argument(
        "--check-redundancy", "-c",
        action="store_true",
        help="Auditoría previa (Dry-Run): evalúa la redundancia del/los documento(s) contra ChromaDB sin alterar la base"
    )
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Filtrar y descartar fragmentos redundantes durante la ingesta, guardando solo contenido novedoso"
    )
    parser.add_argument(
        "--similarity-threshold", "-t",
        type=float,
        default=0.88,
        help="Umbral de similitud semántica para clasificar un fragmento como redundante (por defecto: 0.88 / 88%%)"
    )
    parser.add_argument(
        "--audit-db",
        action="store_true",
        help="Escanear toda la base de datos ChromaDB y reportar pares de documentos existentes con alta redundancia mutua"
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default=None,
        help="Ruta personalizada del directorio de documentos"
    )
    parser.add_argument(
        "--chroma-dir",
        type=str,
        default=None,
        help="Ruta personalizada de persistencia de ChromaDB"
    )

    args = parser.parse_args()

    success = ingest_multimodal(
        docs_path=args.docs_dir,
        chroma_path=args.chroma_dir,
        file_path=args.file,
        incremental=args.incremental,
        delete_doc=args.delete_doc,
        wipe_db=args.wipe,
        check_redundancy=args.check_redundancy,
        deduplicate=args.deduplicate,
        similarity_threshold=args.similarity_threshold,
        audit_db=args.audit_db
    )
    sys.exit(0 if success else 1)

