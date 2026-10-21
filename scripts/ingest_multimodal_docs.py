"""Extract PDF/PPTX content and provide Chroma helpers used by Markdown ingestion."""

import os
import sys
import io
import json
import base64
import re
import hashlib
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

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
    "Describe toda la información visible de esta imagen; no la descartes por parecer decorativa o poco técnica. "
    "- Si es una captura de pantalla de software o interfaz web (Kactus, Seven, GLPI, Windows, Teams, etc.): "
    "transcribe los nombres legibles de ventanas, menús, botones, campos y opciones; no inventes pasos que no aparezcan. "
    "- Si es un diagrama, flujo o mapa de procesos: describe la secuencia lógica y los pasos representados de inicio a fin. "
    "- Si contiene tablas o texto legible: transcribe el texto y los datos de forma estructurada. "
    "- Si es una fotografía, logotipo, banner u otra imagen sin texto técnico, describe objetivamente lo que se ve "
    "y señala que no contiene instrucciones legibles. "
    "No infieras universidad, país, ciudad, identidad de personas ni significado de logotipos o fotografías. "
    "Nunca respondas que la imagen no es relevante ni devuelvas una salida vacía. Responde en español."
)
NON_RELEVANT_IMAGE_SENTINEL = "[IMAGEN_NO_RELEVANTE]"


class ImageProcessingError(RuntimeError):
    """Raised when an image cannot be represented faithfully in extracted text."""


# =============================================================================
# UTILIDADES Y METADATOS
# =============================================================================

def get_metadata_from_path(file_path: Path) -> dict:
    """Mapea automáticamente los metadatos institucionales según la ubicación del archivo."""
    path_str = str(file_path).lower()
    name_str = file_path.name.lower()
    
    # Inferencia de Category basada en nombre de archivo (prioritario para filtro RAG)
    category = "general"
    if any(w in name_str for w in ["pago", "factura", "cartera", "tesorer", "credito", "financier", "liquidaci", "volante", "arancel"]):
        category = "financiero"
    elif any(w in name_str for w in ["nota", "calificaci", "parcial", "grado", "malla", "docente", "evaluaci", "programa", "homologacion", "horario"]):
        category = "academico"
    elif any(w in name_str for w in ["portal", "kactus", "seven"]):
        category = "portales"

    if "1_estudiantes" in path_str:
        return {"audience": "estudiante", "doc_type": "autoservicio", "category": category, "source": file_path.name}
    elif "2_profesores" in path_str:
        return {"audience": "profesor", "doc_type": "autoservicio", "category": "academico", "source": file_path.name}
    elif "3_funcionarios_gestion" in path_str or "administrativo" in path_str:
        return {"audience": "administrativo", "doc_type": "gestion_interna", "category": category, "source": file_path.name}
    elif "4_general_normativa" in path_str:
        return {"audience": "general", "doc_type": "normativa", "category": category, "source": file_path.name}
    elif "5_admin_ti" in path_str:
        return {"audience": "admin_ti", "doc_type": "gestion_interna", "category": category, "source": file_path.name}
    return {"audience": "general", "doc_type": "autoservicio", "category": category, "source": file_path.name}


def strip_chunk_boilerplate(content: str) -> str:
    """
    Elimina encabezados, pies de página, códigos de formato ISO y frases ultra-repetitivas
    (boilerplate) ANTES de indexar en ChromaDB para evitar el efecto 'Eco' (saturación vectorial).
    """
    if not content:
        return ""
    # Quitar únicamente encabezados que sean solo el nombre institucional. No
    # borrar líneas completas que también incluyan instrucciones del documento.
    cleaned = re.sub(
        r"(?im)^\s*(?:universidad\s+sim[oó]n\s+bol[ií]var|sistema\s+de\s+gesti[oó]n\s+de\s+la\s+calidad)\s*$",
        "",
        content,
    )
    cleaned = re.sub(
        r"(?im)^\s*(?:c[oó]digo|versi[oó]n|procedimiento|instructivo|p[aá]gina)\s*:\s*[A-Z0-9.\-/\s]+$",
        "",
        cleaned
    )
    cleaned = re.sub(
        r"(?i)\bp[aá]gina\s+\d+\s+de\s+\d+\b",
        "",
        cleaned
    )
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_image(image_bytes: bytes, max_size: int = 2048, quality: int = 95) -> bytes:
    """
    Normaliza la imagen y conserva el texto pequeño con codificación PNG sin pérdida.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Preserve the visible appearance of transparent and palette images.
        if img.mode in {"RGBA", "LA"} or "transparency" in img.info:
            rgba = img.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            img = Image.alpha_composite(background, rgba).convert("RGB")
        # Convert other modes only after handling alpha/transparency.
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        # Redimensionar manteniendo proporciones
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
        # PNG evita artefactos de compresión sobre texto pequeño en capturas y tablas.
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()
    except Exception as exc:
        logger.warning("No se pudo normalizar una imagen para visión (%s).", type(exc).__name__)
        raise ValueError("No se pudo normalizar la imagen sin riesgo de perder su contenido.") from exc


def is_significant_image(image_bytes: bytes, min_kb: int = 0) -> bool:
    """
    Acepta toda imagen con bytes, sin umbral de tamaño, para no perder contenido.
    """
    return bool(image_bytes)


def is_useful_image_description(description: Optional[str]) -> bool:
    """Reject refusals and empty descriptions so the image can be retried, never dropped."""
    text = (description or "").strip()
    if not text or is_non_relevant_image_description(text):
        return False
    if re.search(
        r"(?i)\b(lo siento|lamento|no puedo ayudar|no puedo describir|i am sorry|i'm sorry|i cannot help)\b",
        text,
    ):
        return False
    return True


def is_non_relevant_image_description(description: Optional[str]) -> bool:
    """Recognize a legacy cache marker that must be reprocessed under the current prompt."""
    return (description or "").strip().casefold() == NON_RELEVANT_IMAGE_SENTINEL.casefold()


# =============================================================================
# CACHÉ PERSISTENTE DE VISIÓN (A PRUEBA DE CORTES DE ENERGÍA Y REINICIOS)
# =============================================================================
VISION_CACHE_FILE = PROJECT_ROOT / "data" / ".vision_cache.json"
_vision_cache: Optional[Dict[str, str]] = None


def load_vision_cache() -> Dict[str, str]:
    """Carga en memoria la caché persistente de descripciones de imágenes."""
    global _vision_cache
    if _vision_cache is None:
        if VISION_CACHE_FILE.exists():
            try:
                with open(VISION_CACHE_FILE, "r", encoding="utf-8") as f:
                    _vision_cache = json.load(f)
                logger.info(f"⚡ Caché de visión cargada ({len(_vision_cache)} imágenes analizadas previamente).")
            except Exception as e:
                logger.warning(f"No se pudo leer la caché de visión ({e}), iniciando nueva.")
                _vision_cache = {}
        else:
            _vision_cache = {}
    return _vision_cache


def save_vision_cache_entry(img_hash: str, description: str):
    """Guarda y persiste inmediatamente una interpretación de imagen en disco con escritura atómica."""
    cache = load_vision_cache()
    cache[img_hash] = description
    try:
        VISION_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_cache = VISION_CACHE_FILE.with_suffix(".tmp")
        with open(temp_cache, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        temp_cache.replace(VISION_CACHE_FILE)
    except Exception as e:
        logger.debug(f"No se pudo guardar la caché de visión en disco: {e}")


# =============================================================================
# VISION-LLM: INTERPRETACIÓN VISUAL DE IMÁGENES
# =============================================================================

def describe_image_with_vllm(
    image_bytes: bytes,
    filename: str = "image",
    ollama_url: str = "http://localhost:11434",
    vision_model: str = "llava:13b",
    timeout: float = 120.0,
    max_image_size: int = 2048
) -> str:
    """
    Describe an image with GPT-6 Luna first and Ollama only as the final fallback.
    Cache entries are separated by provider, model, prompt, and image hash.
    """
    settings = get_settings()
    img_hash = hashlib.sha256(image_bytes).hexdigest()
    cache = load_vision_cache()
    prompt_hash = hashlib.sha256(VISION_PROMPT.encode("utf-8")).hexdigest()[:12]
    primary_cache_key = f"openai:gpt-6-luna:{prompt_hash}:{img_hash}"
    fallback_cache_key = f"ollama:{vision_model}:{prompt_hash}:{img_hash}"

    def cached_description(key: str) -> Tuple[bool, Optional[str]]:
        description = cache.get(key)
        if not description:
            return False, None
        if is_non_relevant_image_description(description):
            logger.warning(
                "[Vision-LLM] Se descarta una marca antigua de omisión para '%s'; se volverá a analizar.",
                filename,
            )
            return False, None
        if not is_useful_image_description(description):
            logger.warning(
                "[Vision-LLM] La descripción en caché de '%s' no es utilizable; se volverá a analizar.",
                filename,
            )
            return False, None
        stats["images_described"] += 1
        logger.debug("[Vision-LLM] Imagen '%s' recuperada de caché (%s).", filename, key.split(":", 2)[0])
        return True, description

    cache_hit, cached = cached_description(primary_cache_key)
    if cache_hit:
        return cached

    try:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY no está configurada para la interpretación visual.")
        normalized = normalize_image(image_bytes, max_size=max_image_size)
        img_b64 = base64.b64encode(normalized).decode("ascii")
        payload = {
            "model": "gpt-6-luna",
            "messages": [
                {"role": "system", "content": "Describe imágenes para soporte técnico. No inventes texto ni pasos."},
                {"role": "user", "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{img_b64}",
                        "detail": "high",
                    }},
                ]},
            ],
            "max_completion_tokens": 2048,
            "reasoning_effort": "low",
        }
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        with httpx.Client(timeout=max(float(timeout), float(settings.openai_timeout or 35.0))) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        result = response.json()
        choice = (result.get("choices") or [{}])[0]
        message = (choice.get("message") or {}).get("content", "")
        if isinstance(message, list):
            message = "\n".join(part.get("text", "") for part in message if isinstance(part, dict))
        description = str(message).strip()
        finish_reason = str(choice.get("finish_reason") or "").casefold()
        if finish_reason == "length":
            raise RuntimeError("GPT-6 Luna truncó la descripción visual por límite de salida.")
        if not is_useful_image_description(description):
            raise RuntimeError(
                f"GPT-6 Luna devolvió una descripción vacía o no utilizable "
                f"(finish_reason={finish_reason or 'desconocido'}, caracteres={len(description)})."
            )
        save_vision_cache_entry(primary_cache_key, description)
        stats["images_described"] += 1
        logger.info("[Vision-LLM] Imagen '%s' procesada por OpenAI gpt-6-luna.", filename)
        return description
    except Exception as primary_error:
        logger.warning(
            "[Vision-LLM] OpenAI gpt-6-luna no pudo procesar '%s' (%s: %s); se intenta Ollama como último recurso.",
            filename,
            type(primary_error).__name__,
            str(primary_error)[:240],
        )

    cache_hit, cached = cached_description(fallback_cache_key)
    if cache_hit:
        return cached

    try:
        normalized = normalize_image(image_bytes, max_size=max_image_size)
        img_b64 = base64.b64encode(normalized).decode("ascii")
        payload = {
            "model": vision_model,
            "prompt": VISION_PROMPT,
            "images": [img_b64],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 2048},
        }
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{ollama_url.rstrip('/')}/api/generate", json=payload)
            response.raise_for_status()
        response_payload = response.json()
        description = str(response_payload.get("response", "")).strip()
        if str(response_payload.get("done_reason") or "").casefold() == "length":
            raise RuntimeError("Ollama truncó la descripción visual por límite de salida.")
        if not is_useful_image_description(description):
            raise RuntimeError("Ollama devolvió una descripción vacía o no utilizable.")
        save_vision_cache_entry(fallback_cache_key, description)
        stats["images_described"] += 1
        logger.info("[Vision-LLM] Imagen '%s' procesada por Ollama (%s), último recurso.", filename, vision_model)
        return description
    except Exception as fallback_error:
        logger.warning(
            "[Vision-LLM] Fallaron OpenAI y Ollama para '%s' (%s).",
            filename,
            type(fallback_error).__name__,
        )
        stats["vision_errors"] += 1
        raise ImageProcessingError(
            f"No se pudo describir la imagen '{filename}' con GPT-6 Luna ni con Ollama; "
            "se detuvo la extracción para evitar indexar el documento incompleto."
        ) from fallback_error


def check_vision_model_available(ollama_url: str, vision_model: str) -> Tuple[bool, str]:
    """
    Verifica si el modelo de visión funciona en Ollama haciendo un smoke test real.
    Intenta el modelo primario, y si falla, prueba fallbacks automáticos.
    Retorna (disponible: bool, modelo_funcional: str).
    """
    FALLBACK_MODELS = [vision_model, "llava:13b", "llama3.2-vision:11b", "llava:7b", "llava-llama3:8b"]

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

def _iter_nested_shapes(shapes):
    """Yield slide shapes recursively so pictures inside groups are not missed."""
    for shape in shapes:
        yield shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _iter_nested_shapes(shape.shapes)

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
    if not use_vision:
        logger.warning("Se ignora la opción sin visión para '%s': las imágenes no se omiten.", source_name)
    use_vision = True

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
        for shape in _iter_nested_shapes(slide.shapes):
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
            if hasattr(shape, "image") and shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    img_bytes = shape.image.blob
                    if not is_significant_image(img_bytes, min_kb=min_image_kb):
                        raise ImageProcessingError(
                            f"La imagen de la diapositiva {slide_idx} de '{source_name}' está vacía."
                        )
                    img_name = f"{source_name}_slide{slide_idx}_img"
                    description = describe_image_with_vllm(
                        img_bytes, img_name,
                        ollama_url=ollama_url,
                        vision_model=vision_model,
                        timeout=vision_timeout,
                        max_image_size=max_image_size
                    )
                    slide_images_descriptions.append(f"[Imagen: {description}]")
                except ImageProcessingError:
                    raise
                except Exception as exc:
                    raise ImageProcessingError(
                        f"No se pudo extraer una imagen de la diapositiva {slide_idx} de '{source_name}'."
                    ) from exc

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
    if not use_vision:
        logger.warning("Se ignora la opción sin visión para '%s': las imágenes no se omiten.", source_name)
    use_vision = True

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
                    if not base_image:
                        raise ImageProcessingError(
                            f"No se pudo extraer la imagen xref={xref} de la página {page_idx + 1} de '{source_name}'."
                        )
                    img_bytes = base_image.get("image", b"")
                    if not is_significant_image(img_bytes, min_kb=min_image_kb):
                        raise ImageProcessingError(
                            f"La imagen xref={xref} de la página {page_idx + 1} de '{source_name}' está vacía."
                        )
                    img_name = f"{source_name}_page{page_idx + 1}_xref{xref}"
                    description = describe_image_with_vllm(
                        img_bytes, img_name,
                        ollama_url=ollama_url,
                        vision_model=vision_model,
                        timeout=vision_timeout,
                        max_image_size=max_image_size
                    )
                    page_images_descriptions.append(f"[Imagen: {description}]")
                except ImageProcessingError:
                    raise
                except Exception as exc:
                    raise ImageProcessingError(
                        f"No se pudo extraer una imagen xref={xref} de la página {page_idx + 1} de '{source_name}'."
                    ) from exc

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
                    if not description:
                        raise ImageProcessingError(
                            f"La página escaneada {page_idx + 1} de '{source_name}' quedó sin descripción."
                        )
                    page_images_descriptions.append(f"[Página Escaneada: {description}]")
                except Exception as exc:
                    raise ImageProcessingError(
                        f"No se pudo interpretar la página escaneada {page_idx + 1} de '{source_name}'."
                    ) from exc

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
    f"{file_stem}_{hash}_p{page_num}_c{chunk_idx}"
    """
    import re
    import hashlib
    ids = []
    page_chunk_counts = {}

    for chunk in chunks:
        source_name = chunk.metadata.get("source", "doc")
        file_stem = Path(source_name).stem
        clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", file_stem)
        source_hash = hashlib.md5(source_name.encode('utf-8')).hexdigest()[:6]

        page_num = (
            chunk.metadata.get("page_number")
            or chunk.metadata.get("slide_number")
            or 1
        )

        key = (source_name, page_num)
        chunk_idx = page_chunk_counts.get(key, 0)
        page_chunk_counts[key] = chunk_idx + 1

        chunk_id = f"{clean_stem}_{source_hash}_p{page_num}_c{chunk_idx}"
        ids.append(chunk_id)

    return ids


def _distance_to_similarity(distance: float, metric: str) -> float:
    """Convierte distancias Chroma a similitud para embeddings normalizados."""
    metric = (metric or "l2").casefold()
    if metric in {"l2", "euclidean"}:
        # Chroma reporta L2 al cuadrado. Para vectores unitarios,
        # ||a-b||² = 2 - 2*cos(a,b).
        similarity = 1.0 - float(distance) / 2.0
    elif metric in {"cosine", "ip", "inner_product"}:
        # cosine distance = 1-cos; normalized inner product = cosine.
        similarity = 1.0 - float(distance) if metric == "cosine" else 1.0 - float(distance)
    else:
        raise ValueError(f"Métrica de distancia Chroma no soportada: {metric}")
    return max(-1.0, min(1.0, similarity))


# =============================================================================
# DETECCIÓN DE REDUNDANCIA Y CONTROL DE ADMISIÓN (PRE-FLIGHT CHECK)
# =============================================================================

def calculate_chunk_redundancy(
    chunks: List[Document],
    vector_store: Chroma,
    embeddings: HuggingFaceEmbeddings,
    threshold: float = 0.88,
    ambiguity_threshold: float = 0.65,
    exclude_source: Optional[str] = None,
    batch_size: int = 32
) -> dict:
    """
    Evalúa la redundancia y ambigüedad semántica de una lista de fragmentos contra ChromaDB.
    - Redundancia alta: similitud >= threshold (default 0.88 o 0.85)
    - Ambigüedad semántica: similitud >= ambiguity_threshold y < threshold (default 0.65)
    - Novedoso: similitud < ambiguity_threshold
    """
    total_chunks = len(chunks)
    if total_chunks == 0:
        return {
            "total_chunks": 0,
            "redundant_count": 0,
            "ambiguous_count": 0,
            "novel_count": 0,
            "redundancy_ratio": 0.0,
            "ambiguity_ratio": 0.0,
            "overlapping_sources": {},
            "redundant_indices": set(),
            "ambiguous_indices": set(),
            "novel_indices": set(),
            "chunk_results": []
        }

    try:
        col = vector_store._collection
        col_count = col.count()
        configuration = getattr(col, "configuration", None) or {}
        collection_metadata = getattr(col, "metadata", None) or {}
        metric = (configuration.get("hnsw") or {}).get("space") or collection_metadata.get("hnsw:space", "l2")
    except Exception:
        col = None
        col_count = 0

    if col_count == 0 or col is None:
        return {
            "total_chunks": total_chunks,
            "redundant_count": 0,
            "ambiguous_count": 0,
            "novel_count": total_chunks,
            "redundancy_ratio": 0.0,
            "ambiguity_ratio": 0.0,
            "overlapping_sources": {},
            "redundant_indices": set(),
            "ambiguous_indices": set(),
            "novel_indices": set(range(total_chunks)),
            "chunk_results": [{"chunk": c, "similarity": 0.0, "matched_source": None, "matched_chunk_snippet": "", "is_redundant": False, "is_ambiguous": False, "status": "novel"} for c in chunks]
        }

    texts = [c.page_content for c in chunks]
    texts_for_embedding = [f"passage: {t}" for t in texts]
    chunk_embeddings = embeddings.embed_documents(texts_for_embedding)

    redundant_indices = set()
    ambiguous_indices = set()
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
                include=["distances", "metadatas", "documents"]
            )
        except Exception:
            try:
                results = col.query(
                    query_embeddings=batch_embs,
                    n_results=n_results,
                    include=["distances", "metadatas"]
                )
            except Exception as exc:
                logger.warning(f"Error consultando ChromaDB para redundancia y ambigüedad: {exc}")
                continue

        for i, chunk in enumerate(batch_chunks):
            global_idx = start_idx + i
            distances = results["distances"][i] if i < len(results["distances"]) else []
            metadatas = results["metadatas"][i] if i < len(results["metadatas"]) else []
            docs = results.get("documents", [[]])[i] if ("documents" in results and i < len(results["documents"])) else []

            best_dist = 999.0
            best_meta = {}
            best_matched_doc = ""
            for k, (dist, meta) in enumerate(zip(distances, metadatas)):
                src = meta.get("source") if meta else ""
                if exclude_source and src == exclude_source:
                    continue
                best_dist = dist
                best_meta = meta or {}
                if k < len(docs) and docs[k]:
                    best_matched_doc = str(docs[k]).strip()
                break

            similarity = _distance_to_similarity(best_dist, metric) if best_dist < 900.0 else 0.0
            matched_src = best_meta.get("source", "desconocido") if best_meta else None

            is_redundant = (similarity >= threshold) and (matched_src is not None)
            is_ambiguous = (similarity >= ambiguity_threshold and not is_redundant) and (matched_src is not None)

            if is_redundant:
                redundant_indices.add(global_idx)
            elif is_ambiguous:
                ambiguous_indices.add(global_idx)
            else:
                novel_indices.add(global_idx)

            if (is_redundant or is_ambiguous) and matched_src:
                if matched_src not in overlapping_sources:
                    overlapping_sources[matched_src] = {
                        "count": 0,
                        "redundant_count": 0,
                        "ambiguous_count": 0,
                        "max_similarity": 0.0,
                        "sample_snippet": chunk.page_content[:150].strip(),
                        "matched_sample_snippet": best_matched_doc[:150].strip()
                    }
                overlapping_sources[matched_src]["count"] += 1
                if is_redundant:
                    overlapping_sources[matched_src]["redundant_count"] += 1
                if is_ambiguous:
                    overlapping_sources[matched_src]["ambiguous_count"] += 1
                overlapping_sources[matched_src]["max_similarity"] = max(
                    overlapping_sources[matched_src]["max_similarity"],
                    similarity
                )

            status_str = "redundant" if is_redundant else ("ambiguous" if is_ambiguous else "novel")
            chunk_results.append({
                "chunk": chunk,
                "distance": best_dist if best_dist < 900.0 else None,
                "distance_metric": metric,
                "similarity": similarity,
                "matched_source": matched_src,
                "matched_chunk_snippet": best_matched_doc.strip(),
                "is_redundant": is_redundant,
                "is_ambiguous": is_ambiguous,
                "status": status_str
            })

    redundancy_ratio = round((len(redundant_indices) / total_chunks) * 100.0, 1) if total_chunks > 0 else 0.0
    ambiguity_ratio = round((len(ambiguous_indices) / total_chunks) * 100.0, 1) if total_chunks > 0 else 0.0

    return {
        "total_chunks": total_chunks,
        "redundant_count": len(redundant_indices),
        "ambiguous_count": len(ambiguous_indices),
        "novel_count": len(novel_indices),
        "redundancy_ratio": redundancy_ratio,
        "ambiguity_ratio": ambiguity_ratio,
        "overlapping_sources": overlapping_sources,
        "redundant_indices": redundant_indices,
        "ambiguous_indices": ambiguous_indices,
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
        configuration = getattr(col, "configuration", None) or {}
        collection_metadata = getattr(col, "metadata", None) or {}
        metric = (configuration.get("hnsw") or {}).get("space") or collection_metadata.get("hnsw:space", "l2")
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
            sample_texts_for_embedding = [f"passage: {t}" for t in sample_texts]
            sample_embeddings = embeddings.embed_documents(sample_texts_for_embedding)
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
                    sim = _distance_to_similarity(dist, metric)
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
# COMPATIBILIDAD DE INGESTA: TRANSFORMAR A MARKDOWN ANTES DE INDEXAR
# =============================================================================

def ingest_multimodal(
    docs_path: Optional[str] = None,
    chroma_path: Optional[str] = None,
    sanitized_docs_path: Optional[str] = None,
    model_name: Optional[str] = None,
    file_path: Optional[str] = None,
    incremental: bool = True,
    delete_doc: Optional[str] = None,
    wipe_db: bool = False,
    check_redundancy: bool = False,
    deduplicate: bool = False,
    similarity_threshold: float = 0.88,
    audit_db: bool = False,
    vision_model_override: Optional[str] = None,
    min_image_kb_override: Optional[int] = None,
    pre_index_validator=None,
) -> bool:
    """Compatibility entry point: raw PDF/PPTX input is sanitized to Markdown before indexing."""
    del model_name, similarity_threshold
    if check_redundancy or audit_db:
        logger.error("La ingesta Markdown no ejecuta auditorías de redundancia; no se modificó ChromaDB.")
        return False
    if deduplicate:
        logger.info("Deduplicación semántica omitida para conservar evidencia documental completa.")

    from scripts.ingest_sanitized_documents import ingest_sanitized_documents

    full_rebuild = wipe_db or (not incremental and not file_path and not delete_doc)
    force_document = bool(file_path and not incremental)
    return ingest_sanitized_documents(
        docs_path=docs_path,
        chroma_path=chroma_path,
        sanitized_docs_path=sanitized_docs_path,
        file_path=file_path,
        incremental=incremental,
        delete_doc=delete_doc,
        wipe_db=full_rebuild,
        force=force_document,
        use_vision=True,
        vision_model_override=vision_model_override,
        min_image_kb_override=min_image_kb_override,
        pre_index_validator=pre_index_validator,
    )


if __name__ == "__main__":
    from scripts.ingest_sanitized_documents import main

    raise SystemExit(main())

