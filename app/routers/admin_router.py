"""
Router Administrativo y de Gestión de Base de Conocimiento para UniMon (USB).
Provee endpoints para el panel de administración (/admin), subida de documentos,
re-indexación en ChromaDB y consulta de estado del sistema.
"""

import asyncio
import hashlib
import os
import shutil
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Query, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, SecretStr
from starlette.concurrency import run_in_threadpool

import uuid
import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import get_settings
from app.security import require_admin_auth, require_admin_origin
from app.upload_security import save_upload, validated_filename
from app.services.rag_service import rag_service
from app.services.telemetry_service import get_chatbot_instance_kpis, get_kpis_summary
from app.services.knowledge_base_service import (
    audit_source_against_markdown,
    build_knowledge_catalog,
    get_document_detail,
    resolve_source_file,
)
from app.services.bot_instance_service import (
    BotInstanceError,
    bot_instance_manager,
)
from app.services.sanitized_documents import split_markdown_for_rag
from app.services.llm_endpoint_security import validate_custom_llm_base_url
from scripts.ingest_multimodal_docs import (
    ingest_multimodal,
    calculate_chunk_redundancy,
    delete_document_chunks,
    process_pdf,
    process_pptx
)
from scripts.apply_document_taxonomy import run_taxonomy_update as apply_taxonomy_to_chroma

logger = logging.getLogger("unimon.admin_router")

router = APIRouter(
    tags=["Panel de Administración UniMon"],
    dependencies=[Depends(require_admin_auth), Depends(require_admin_origin)]
)

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DOCS_DIR = Path(settings.docs_dir)
STAGED_DIR = Path("data/scratch/staged_uploads")
STAGED_DIR.mkdir(parents=True, exist_ok=True)
FIDELITY_AUDIT_SLOTS = asyncio.Semaphore(2)


class ResolveUploadRequest(BaseModel):
    staged_id: str = Field(..., pattern=r"^(?:[0-9a-f]{10}|[0-9a-f]{32})$", description="ID de sesión temporal de subida")
    action: str = Field(..., pattern=r"^(replace|deduplicate|force|cancel)$", description="Acción de resolución: 'replace', 'deduplicate', 'force' o 'cancel'")
    target_to_replace: Optional[str] = Field(default=None, description="Documento previo a purgar (opcional)")


class ResolveInstanceUploadRequest(BaseModel):
    staged_id: str = Field(..., pattern=r"^[0-9a-f]{32}$", description="ID temporal de la instancia")
    action: str = Field(..., pattern=r"^(replace|deduplicate|force|cancel)$")
    target_to_replace: Optional[str] = Field(default=None, max_length=180)


class FidelityAuditRequest(BaseModel):
    source_path: str = Field(..., min_length=1, max_length=1024)
    force: bool = False


class CreateBotInstanceRequest(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=80)
    dependency_name: str = Field(..., min_length=2, max_length=120)
    scope_description: str = Field(..., min_length=10, max_length=600)
    support_email: str = Field(default="", max_length=120)
    support_phone: str = Field(default="", max_length=32)
    bot_id: str = Field(default="", max_length=40)
    llm_provider: str = Field(..., min_length=1, max_length=32)
    llm_model: str = Field(..., min_length=1, max_length=160)
    llm_custom_provider: str = Field(default="", max_length=80)
    llm_protocol: str = Field(default="", max_length=32)
    llm_base_url: str = Field(default="", max_length=512)
    llm_timeout: float = Field(default=35.0, ge=2.0, le=180.0)
    llm_api_key: Optional[SecretStr] = None


class UpdateBotInstanceRequest(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=80)
    dependency_name: str = Field(..., min_length=2, max_length=120)
    scope_description: str = Field(..., min_length=10, max_length=600)
    support_email: str = Field(default="", max_length=120)
    support_phone: str = Field(default="", max_length=32)
    llm_provider: str = Field(..., min_length=1, max_length=32)
    llm_model: str = Field(..., min_length=1, max_length=160)
    llm_custom_provider: str = Field(default="", max_length=80)
    llm_protocol: str = Field(default="", max_length=32)
    llm_base_url: str = Field(default="", max_length=512)
    llm_timeout: float = Field(default=35.0, ge=2.0, le=180.0)
    llm_api_key: Optional[SecretStr] = None


class SetBotInstanceEnabledRequest(BaseModel):
    enabled: bool


def extract_chunks_from_staged_file(file_path: Path) -> List[Document]:
    """Extrae texto de un archivo subido temporalmente y genera fragmentos para auditoría."""
    ext = file_path.suffix.lower()
    docs: List[Document] = []
    source_name = file_path.name
    if "_" in source_name:
        orig_name = source_name.split("_", 1)[1]
    else:
        orig_name = source_name

    if ext == ".pdf":
        try:
            import fitz
            pdf = fitz.open(str(file_path))
            for idx, page in enumerate(pdf):
                txt = page.get_text("text").strip()
                if txt:
                    docs.append(Document(
                        page_content=txt,
                        metadata={"source": orig_name, "page_number": idx + 1, "total_pages": len(pdf)}
                    ))
            pdf.close()
        except Exception as exc:
            logger.warning(f"Error extrayendo texto con fitz para '{source_name}': {exc}")

        # Fallback de lectura directa para mocks o archivos de texto plano renombrados
        if not docs:
            try:
                raw_txt = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                if raw_txt:
                    docs.append(Document(page_content=raw_txt, metadata={"source": orig_name, "page_number": 1}))
            except Exception:
                pass

    elif ext == ".pptx":
        try:
            from pptx import Presentation
            prs = Presentation(str(file_path))
            for s_idx, slide in enumerate(prs.slides):
                parts = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        parts.append(shape.text_frame.text)
                txt = "\n".join(parts).strip()
                if txt:
                    docs.append(Document(page_content=txt, metadata={"source": orig_name, "slide_number": s_idx + 1}))
        except Exception as exc:
            logger.warning(f"Error procesando pptx para '{source_name}': {exc}")

    elif ext == ".docx":
        try:
            import docx
            doc = docx.Document(str(file_path))
            parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    cells = [cell.text.strip().replace("\n", " / ") for cell in row.cells]
                    if any(cells):
                        parts.append(" | ".join(cells))
            txt = "\n".join(parts).strip()
            if txt:
                docs.append(Document(page_content=txt, metadata={"source": orig_name}))
        except Exception as exc:
            logger.warning(f"Error procesando docx para '{source_name}': {exc}")

    elif ext in (".txt", ".md", ".csv"):
        try:
            txt = file_path.read_text(encoding="utf-8", errors="ignore").strip()
            if txt:
                docs.append(Document(page_content=txt, metadata={"source": orig_name}))
        except Exception as exc:
            logger.warning(f"Error leyendo archivo de texto '{source_name}': {exc}")

    if not docs:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return text_splitter.split_documents(docs)


settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DOCS_DIR = Path(settings.docs_dir)

# Mapeo de audiencia a subdirectorios estándar
AUDIENCE_FOLDER_MAP = {
    "estudiante": "1_estudiantes",
    "estudiantes": "1_estudiantes",
    "profesor": "2_profesores",
    "profesores": "2_profesores",
    "docente": "2_profesores",
    "docentes": "2_profesores",
    "administrativo": "3_funcionarios_gestion",
    "administrativos": "3_funcionarios_gestion",
    "funcionario": "3_funcionarios_gestion",
    "funcionarios": "3_funcionarios_gestion",
    "general": "4_general_normativa",
    "normativa": "4_general_normativa",
    "otros": "4_general_normativa"
}


# =============================================================================
# 1. RUTAS DE VISTA HTML (/admin)
# =============================================================================

@router.get(
    "/admin",
    summary="Panel de Administración y Observabilidad",
    description="Sirve la interfaz web administrativa de gestión técnica y telemetría."
)
@router.get(
    "/admin.html",
    include_in_schema=False
)
async def get_admin_dashboard():
    """Retorna la página HTML del panel de administración."""
    admin_html = STATIC_DIR / "admin.html"
    if admin_html.exists():
        return FileResponse(str(admin_html))
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="El archivo admin.html no se encuentra en app/static/admin.html"
    )


# =============================================================================
# 2. GESTIÓN Y LISTADO DE DOCUMENTOS (/api/admin/docs)
# =============================================================================

@router.get(
    "/api/admin/docs",
    summary="Listar Documentos de la Base de Conocimiento",
    description="Relaciona fuentes PDF/PPTX/DOCX con su Markdown validado, estado de indexación y auditorías de fidelidad."
)
async def list_documents() -> Dict[str, Any]:
    """Lista fuentes, Markdown generado, estado Chroma y auditorías de fidelidad."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = Path(settings.sanitized_docs_dir)
    try:
        return await run_in_threadpool(
            lambda: build_knowledge_catalog(DOCS_DIR, output_dir, rag_service.vector_store),
        )
    except Exception as exc:
        logger.exception("No se pudo construir el catálogo de la base de conocimiento")
        raise HTTPException(status_code=500, detail="No se pudo cargar el catálogo de conocimiento") from exc


@router.get(
    "/api/admin/docs/detail",
    summary="Ver detalle de una fuente y su Markdown",
)
async def document_detail(source_path: str = Query(..., min_length=1, max_length=1024)) -> Dict[str, Any]:
    try:
        return await run_in_threadpool(
            get_document_detail, DOCS_DIR, Path(settings.sanitized_docs_dir), source_path
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/api/admin/docs/source",
    summary="Abrir el archivo fuente original",
)
async def document_source(source_path: str = Query(..., min_length=1, max_length=1024)):
    try:
        path = await run_in_threadpool(resolve_source_file, DOCS_DIR, source_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    media_type = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(path.suffix.lower(), "application/octet-stream")
    content_disposition = f"inline; filename*=UTF-8''{quote(path.name)}"
    return FileResponse(
        path,
        media_type=media_type,
        headers={
            "Content-Disposition": content_disposition,
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post(
    "/api/admin/docs/audit",
    summary="Comparar el Markdown validado con su PDF o PPTX fuente",
)
async def audit_document_fidelity(request: FidelityAuditRequest) -> Dict[str, Any]:
    try:
        async with FIDELITY_AUDIT_SLOTS:
            return await audit_source_against_markdown(
                DOCS_DIR,
                Path(settings.sanitized_docs_dir),
                request.source_path,
                force=request.force,
            )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Falló la auditoría de fidelidad de %s", request.source_path)
        raise HTTPException(status_code=502, detail="La comparación con el modelo no se pudo completar") from exc


# =============================================================================
# 3. CARGA DE NUEVOS DOCUMENTOS (/api/admin/upload-doc)
# =============================================================================

@router.post(
    "/api/admin/upload-doc",
    summary="Subir Documento a la Base de Conocimiento",
    description="Sube un documento a data/docs; la indexación automática convierte PDF/PPTX/DOCX a Markdown antes de usar ChromaDB."
)
async def upload_document(
    file: UploadFile = File(...),
    audience: str = Form("general"),
    auto_index: bool = Form(False)
) -> Dict[str, Any]:
    """Recibe un archivo y lo almacena en la estructura de data/docs/."""
    filename = validated_filename(file.filename)
    if Path(filename).suffix.lower() not in {".pdf", ".pptx", ".docx"}:
        raise HTTPException(status_code=415, detail="La ingesta Markdown admite archivos PDF, PPTX y DOCX.")

    # Determinar subdirectorio según audiencia
    subfolder_name = AUDIENCE_FOLDER_MAP.get(audience.lower().strip(), "4_general_normativa")
    target_dir = DOCS_DIR / subfolder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    dest_path = target_dir / filename

    try:
        file_size = await save_upload(file, dest_path, settings.max_upload_size_mb * 1024 * 1024)
        logger.info(f"✅ Documento '{filename}' guardado en: {dest_path} ({file_size} bytes)")

        # Si se solicitó auto-indexar este archivo inmediatamente
        indexing_result = None
        if auto_index:
            try:
                indexed = ingest_multimodal(file_path=str(dest_path), incremental=True)
                if not indexed:
                    raise RuntimeError(
                        "El índice actual todavía no admite la incorporación incremental; "
                        "revisa los logs y completa primero la reconstrucción Markdown."
                    )
                apply_taxonomy_to_chroma()
                indexing_result = "Transformado a Markdown e indexado en ChromaDB."
            except Exception as e:
                logger.warning(f"Aviso durante auto-indexación: {e}")
                indexing_result = f"Guardado, pero la indexación falló: {e}"

        return {
            "status": "success",
            "message": f"Documento '{filename}' subido exitosamente a la carpeta '{subfolder_name}'.",
            "filename": filename,
            "audience": audience,
            "folder": subfolder_name,
            "file_size_kb": round(file_size / 1024, 1),
            "indexing_result": indexing_result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error guardando documento '{filename}': {e}")
        raise HTTPException(status_code=500, detail="Error al guardar archivo en el servidor")


# =============================================================================
# 3.1 PRE-AUDITORÍA Y RESOLUCIÓN DE REDUNDANCIA / AMBIGÜEDAD
# =============================================================================

@router.post(
    "/api/admin/audit-doc",
    summary="Auditar Documento contra Redundancia y Ambigüedad en ChromaDB",
    description="Extrae fragmentos del archivo y analiza su solapamiento semántico con ChromaDB sin persistirlo."
)
async def audit_document(
    file: UploadFile = File(...),
    audience: str = Form("general"),
    threshold: float = Form(0.85),
    ambiguity_threshold: float = Form(0.65)
) -> Dict[str, Any]:
    """Analiza en memoria/staging un documento para calcular solapamiento semántico y ambigüedad contra ChromaDB."""
    filename = validated_filename(file.filename)
    if Path(filename).suffix.lower() not in {".pdf", ".pptx", ".docx"}:
        raise HTTPException(status_code=415, detail="La ingesta Markdown admite archivos PDF, PPTX y DOCX.")

    staged_id = uuid.uuid4().hex
    staged_filename = f"{staged_id}_{filename}"
    staged_file_path = STAGED_DIR / staged_filename

    try:
        await save_upload(file, staged_file_path, settings.max_upload_size_mb * 1024 * 1024)

        # Extraer fragmentos para pre-auditoría
        chunks = extract_chunks_from_staged_file(staged_file_path)
        total_chunks = len(chunks)

        rep = {
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

        if total_chunks > 0:
            try:
                vs = rag_service.vector_store
                emb = rag_service.embeddings
                if vs is not None and vs._collection.count() > 0:
                    rep = calculate_chunk_redundancy(
                        chunks=chunks,
                        vector_store=vs,
                        embeddings=emb,
                        threshold=threshold,
                        ambiguity_threshold=ambiguity_threshold,
                        exclude_source=None,
                        batch_size=32
                    )
            except Exception as exc:
                logger.warning(f"Aviso al calcular redundancia contra ChromaDB: {exc}")

        redundancy_ratio = round(rep.get("redundancy_ratio", 0.0), 1)
        ambiguity_ratio = round(rep.get("ambiguity_ratio", 0.0), 1)
        redundant_count = rep.get("redundant_count", 0)
        ambiguous_count = rep.get("ambiguous_count", 0)
        novel_count = rep.get("novel_count", total_chunks - (redundant_count + ambiguous_count))

        overlapping_sources_raw = rep.get("overlapping_sources", {})
        overlapping_sources = []
        for src, data in sorted(
            overlapping_sources_raw.items(),
            key=lambda item: item[1].get("max_similarity", 0),
            reverse=True
        ):
            overlapping_sources.append({
                "source": src,
                "matched_chunks": data.get("count", 0),
                "redundant_count": data.get("redundant_count", 0),
                "ambiguous_count": data.get("ambiguous_count", 0),
                "max_similarity": round(data.get("max_similarity", 0.0) * 100, 1),
                "sample_snippet": data.get("sample_snippet", ""),
                "matched_sample_snippet": data.get("matched_sample_snippet", "")
            })

        detailed_chunks = []
        for idx, item in enumerate(rep.get("chunk_results", [])):
            chunk_obj = item.get("chunk")
            snippet = chunk_obj.page_content.strip() if chunk_obj else ""
            detailed_chunks.append({
                "index": idx + 1,
                "content_snippet": snippet,
                "matched_chunk_snippet": item.get("matched_chunk_snippet", ""),
                "similarity": round(item.get("similarity", 0.0) * 100, 1),
                "matched_source": item.get("matched_source") or "Ninguno",
                "is_redundant": bool(item.get("is_redundant", False)),
                "is_ambiguous": bool(item.get("is_ambiguous", False)),
                "status": item.get("status", "novel")
            })

        primary_source = overlapping_sources[0]["source"] if overlapping_sources else None
        redundancy_detected = (redundancy_ratio >= 20.0) or (redundant_count > 0)
        ambiguity_detected = (ambiguous_count > 0) or (ambiguity_ratio >= 10.0)

        overall_status = "clean"
        if redundancy_detected:
            overall_status = "redundant"
        elif ambiguity_detected:
            overall_status = "ambiguous"

        # Guardar metadatos de staging
        meta = {
            "staged_id": staged_id,
            "filename": filename,
            "audience": audience,
            "staged_path": str(staged_file_path),
            "primary_overlapping_source": primary_source,
            "overlapping_sources": [o["source"] for o in overlapping_sources],
            "metrics": {
                "total_chunks": total_chunks,
                "novel_chunks": novel_count,
                "ambiguous_chunks": ambiguous_count,
                "redundant_chunks": redundant_count,
                "ambiguity_ratio": ambiguity_ratio,
                "redundancy_ratio": redundancy_ratio
            },
            "overall_status": overall_status,
            "created_at": datetime.now().isoformat()
        }
        meta_file = STAGED_DIR / f"{staged_id}_meta.json"
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "status": "success",
            "staged_id": staged_id,
            "filename": filename,
            "audience": audience,
            "threshold": threshold,
            "ambiguity_threshold": ambiguity_threshold,
            "ambiguity_detected": ambiguity_detected,
            "redundancy_detected": redundancy_detected,
            "overall_status": overall_status,
            "metrics": {
                "total_chunks": total_chunks,
                "novel_chunks": novel_count,
                "ambiguous_chunks": ambiguous_count,
                "redundant_chunks": redundant_count,
                "ambiguity_ratio": ambiguity_ratio,
                "redundancy_ratio": redundancy_ratio
            },
            "primary_overlapping_source": primary_source,
            "overlapping_sources": overlapping_sources,
            "detailed_chunks": detailed_chunks
        }

    except HTTPException:
        staged_file_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        staged_file_path.unlink(missing_ok=True)
        logger.error(f"Error auditando documento '{filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error durante la auditoría del documento")


@router.post(
    "/api/admin/resolve-upload",
    summary="Resolver Ingesta de Documento Auditado",
    description="Aplica una de las 4 acciones de resolución: replace, deduplicate, force o cancel."
)
async def resolve_staged_upload(
    request: ResolveUploadRequest
) -> Dict[str, Any]:
    """Aplica la resolución elegida por el administrador para un documento en staging."""
    clean_staged_id = request.staged_id
    meta_file = STAGED_DIR / f"{clean_staged_id}_meta.json"

    if not meta_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Sesión de carga temporal '{clean_staged_id}' no encontrada o ya procesada."
        )

    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        filename = validated_filename(meta.get("filename"))
        staged_path = STAGED_DIR / f"{clean_staged_id}_{filename}"
        audience = meta.get("audience", "general")

        # 1. CASO: Cancelar / Descartar
        if request.action == "cancel":
            if staged_path.exists():
                staged_path.unlink()
            meta_file.unlink(missing_ok=True)
            return {
                "status": "cancelled",
                "action": "cancel",
                "filename": filename,
                "message": f"Documento '{filename}' descartado exitosamente. No se realizaron cambios."
            }

        if not staged_path.exists():
            raise HTTPException(status_code=404, detail=f"Archivo temporal en '{staged_path}' no encontrado.")

        # Determinar directorio destino según audiencia
        subfolder_name = AUDIENCE_FOLDER_MAP.get(audience.lower().strip(), "4_general_normativa")
        target_dir = DOCS_DIR / subfolder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        dest_path = target_dir / filename

        # Mover o copiar archivo a su ubicación permanente
        if staged_path.is_symlink() or not staged_path.is_file():
            raise HTTPException(status_code=400, detail="Archivo temporal inválido")
        with staged_path.open("rb") as source:
            from tempfile import NamedTemporaryFile
            with NamedTemporaryFile(dir=target_dir, prefix=".upload-", delete=False) as output:
                temp_dest = Path(output.name)
                shutil.copyfileobj(source, output)
        try:
            os.replace(temp_dest, dest_path)
        finally:
            temp_dest.unlink(missing_ok=True)

        # 2. CASO: Actualizar / Reemplazar Documento Existente
        if request.action == "replace":
            target_to_purge = request.target_to_replace or meta.get("primary_overlapping_source") or filename
            indexed = ingest_multimodal(file_path=str(dest_path), incremental=False, deduplicate=False)
            if not indexed:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se indexó el documento. El índice activo puede requerir primero una reconstrucción Markdown completa.",
                )
            if target_to_purge and target_to_purge != filename:
                vs = rag_service.vector_store
                if vs is not None:
                    delete_document_chunks(vs, target_to_purge)
                for root, _, files in os.walk(DOCS_DIR):
                    if target_to_purge in files:
                        (Path(root) / target_to_purge).unlink(missing_ok=True)
                        logger.info("Documento fuente anterior eliminado tras indexar la versión nueva: %s", target_to_purge)
            apply_taxonomy_to_chroma()
            rag_service.reload_vector_store()

            msg = f"Versión anterior de '{target_to_purge or filename}' purgada y nueva versión de '{filename}' indexada."

        # 3. CASO: Guardar como Nuevo (con Deduplicación de Fragmentos)
        elif request.action == "deduplicate":
            logger.info(f"🛡️ Deduplicación activa para '{filename}'...")
            indexed = ingest_multimodal(file_path=str(dest_path), incremental=False, deduplicate=True, similarity_threshold=0.85)
            if not indexed:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se indexó el documento; completa primero la reconstrucción Markdown.")
            apply_taxonomy_to_chroma()
            rag_service.reload_vector_store()

            msg = f"Documento '{filename}' transformado a Markdown e indexado completo; no se descartaron fragmentos por similitud."

        # 4. CASO: Forzar Indexación Completa (Sin Filtrado)
        elif request.action == "force":
            logger.info(f"⚡ Ingesta forzada completa para '{filename}'...")
            indexed = ingest_multimodal(file_path=str(dest_path), incremental=False, deduplicate=False)
            if not indexed:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se indexó el documento; completa primero la reconstrucción Markdown.")
            apply_taxonomy_to_chroma()
            rag_service.reload_vector_store()

            msg = f"Documento '{filename}' indexado completamente sin aplicar filtros de redundancia."

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Acción '{request.action}' desconocida. Válidas: 'replace', 'deduplicate', 'force', 'cancel'."
            )

        # Limpieza de archivos temporales de staging
        try:
            staged_path.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)
        except Exception:
            pass

        return {
            "status": "success",
            "action": request.action,
            "filename": filename,
            "folder": subfolder_name,
            "message": msg
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolviendo subida '{clean_staged_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error resolviendo la subida del documento")


# =============================================================================
# 4. RE-INDEXACIÓN DE BASE VECTORIAL (/api/admin/reindex)
# =============================================================================

@router.post(
    "/api/admin/reindex",
    summary="Re-indexar Base Vectorial ChromaDB",
    description="Transforma documentos nuevos o modificados a Markdown y los indexa. La reconstrucción completa se ejecuta fuera del servidor."
)
async def reindex_knowledge_base(
    incremental: bool = Query(default=True, description="Procesar solo documentos nuevos o modificados"),
    wipe_db: bool = Query(default=False, description="La reconstrucción completa requiere ejecutar el script con UniMon detenido")
) -> Dict[str, Any]:
    """Procesa incrementalmente solo documentos cuyo Markdown aún no está indexado."""
    if wipe_db or not incremental:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La reconstrucción limpia debe ejecutarse con UniMon detenido para liberar ChromaDB. "
                "Ejecuta: .venv\\Scripts\\python.exe scripts\\ingest_sanitized_documents.py --rebuild"
            ),
        )
    try:
        start_time = datetime.now()
        logger.info("🔄 Iniciando indexación incremental de Markdown...")

        success = ingest_multimodal(incremental=True)

        taxonomy_updated = 0
        if success:
            try:
                taxonomy_updated = apply_taxonomy_to_chroma()
            except Exception as tax_err:
                logger.warning(f"Aviso al actualizar taxonomía: {tax_err}")

        elapsed_sec = round((datetime.now() - start_time).total_seconds(), 2)

        return {
            "status": "success" if success else "warning",
            "message": "Documentos nuevos o modificados transformados a Markdown e indexados." if success else "No se completó la ingesta Markdown; revisa los logs y confirma que el índice ya fue reconstruido.",
            "duration_seconds": elapsed_sec,
            "incremental": True,
            "wipe_db": False,
            "taxonomy_chunks_classified": taxonomy_updated
        }

    except Exception as e:
        logger.error(f"Error durante re-indexación de ChromaDB: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la re-indexación: {str(e)}"
        )


# =============================================================================
# 5. ELIMINACIÓN DE DOCUMENTO (/api/admin/docs/{filename})
# =============================================================================

@router.delete(
    "/api/admin/docs/{filename:path}",
    summary="Eliminar Documento y sus Chunks Vectoriales",
    description="Elimina el archivo físico de data/docs/ y borra todos sus fragmentos indexados en ChromaDB."
)
async def delete_document(filename: str) -> Dict[str, Any]:
    """Elimina el archivo físico y purga sus fragmentos en ChromaDB."""
    clean_filename = Path(filename).name
    target_file = None

    # Buscar archivo en data/docs y subcarpetas
    for root, _, files in os.walk(DOCS_DIR):
        if clean_filename in files:
            target_file = Path(root) / clean_filename
            break

    if not target_file or not target_file.exists():
        raise HTTPException(status_code=404, detail=f"Documento '{clean_filename}' no encontrado en data/docs/.")

    try:
        # 1. Eliminar archivo físico
        target_file.unlink()
        logger.info(f"🗑️ Archivo físico '{target_file}' eliminado.")

        # 2. Purgar chunks en ChromaDB
        chunks_deleted = 0
        try:
            ingest_multimodal(delete_doc=clean_filename)
        except Exception as e:
            logger.warning(f"Aviso al purgar chunks de ChromaDB para '{clean_filename}': {e}")

        return {
            "status": "success",
            "message": f"Documento '{clean_filename}' eliminado del disco y de la base vectorial ChromaDB.",
            "deleted_file": clean_filename
        }

    except Exception as e:
        logger.error(f"Error eliminando documento '{clean_filename}': {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo eliminar el documento: {str(e)}")


# =============================================================================
# 5.1 INSTANCIAS DE CHATBOT POR DEPENDENCIA
# =============================================================================

@router.get(
    "/api/admin/llm-models",
    summary="Listar proveedores y modelos LLM configurados",
    description="Devuelve modelos cloud configurados y modelos locales instalados en Ollama, sin exponer credenciales.",
)
async def list_llm_models() -> Dict[str, Any]:
    import httpx

    current = get_settings()
    default_provider = (current.llm_provider or "openai").strip().casefold()
    provider_settings = {
        "openai": ("OpenAI", current.openai_api_key, current.openai_model),
        "anthropic": ("Anthropic", current.anthropic_api_key, current.anthropic_model),
        "gemini": ("Google Gemini", current.gemini_api_key, current.gemini_model),
    }
    async def discover_cloud_models(provider: str) -> tuple[str, List[str], set[str]]:
        _, api_key, configured_model = provider_settings[provider]
        if not api_key:
            return provider, [], set()
        if provider == "anthropic":
            url = f"{current.anthropic_base_url.rstrip('/')}/models"
            headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
            params = {"limit": 1000}
        elif provider == "gemini":
            url = f"{current.gemini_base_url.rstrip('/')}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            params = None
        else:
            url = f"{current.openai_base_url.rstrip('/')}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            params = None
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                response = await client.get(url, headers=headers, params=params)
            if response.status_code != 200:
                return provider, ([configured_model] if configured_model else []), set()
            payload = response.json()
            rows = payload.get("data") or payload.get("models") or []
            model_ids = set()
            for row in rows:
                if not isinstance(row, dict):
                    continue
                model_id = str(row.get("id") or row.get("name") or "").strip()
                if model_id.startswith("models/"):
                    model_id = model_id.removeprefix("models/")
                if not model_id:
                    continue
                # El selector ofrece familias conversacionales compatibles con este cliente.
                if provider == "anthropic" and not model_id.casefold().startswith("claude"):
                    continue
                if provider == "gemini" and "gemini" not in model_id.casefold():
                    continue
                if provider == "openai" and not re.match(r"^(?:gpt|o[1-9]|chatgpt)", model_id, re.IGNORECASE):
                    continue
                model_ids.add(model_id)
            verified_ids = sorted(model_ids, key=str.casefold)
            if configured_model and configured_model not in model_ids:
                model_ids.add(configured_model)
            return provider, sorted(model_ids, key=str.casefold), set(verified_ids)
        except Exception:
            return provider, ([configured_model] if configured_model else []), set()

    cloud_results = await asyncio.gather(*(
        discover_cloud_models(provider) for provider in provider_settings
    ))
    cloud_catalogs = {
        provider: {"models": models, "verified_ids": verified_ids}
        for provider, models, verified_ids in cloud_results
    }
    providers: List[Dict[str, Any]] = []
    for provider, (label, api_key, configured_model) in provider_settings.items():
        cloud_catalog = cloud_catalogs.get(provider, {})
        available_models = cloud_catalog.get("models", [])
        confirmed_ids = set(cloud_catalog.get("verified_ids", set()))
        # El último modelo configurado siempre se puede revisar o editar aunque el endpoint
        # de catálogo del proveedor no responda durante esta carga del panel.
        if configured_model and configured_model not in available_models and api_key:
            available_models = [*available_models, configured_model]
        providers.append({
            "id": provider,
            "label": label,
            "configured": bool(api_key),
            "models": [
                {
                    "id": model,
                    "label": f"{model} ({'disponible en el proveedor' if model in confirmed_ids else 'configurado; disponibilidad no confirmada'})",
                    "available": model in confirmed_ids,
                }
                for model in available_models
            ] if api_key else [],
        })

    local_models: List[str] = []
    running_models: set[str] = set()
    ollama_online = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{current.ollama_base_url.rstrip('/')}/api/tags")
        if response.status_code == 200:
            ollama_online = True
            local_models = [
                str(item.get("name"))
                for item in response.json().get("models", [])
                if isinstance(item, dict) and item.get("name")
            ]
            try:
                async with httpx.AsyncClient(timeout=1.5) as client:
                    running_response = await client.get(f"{current.ollama_base_url.rstrip('/')}/api/ps")
                if running_response.status_code == 200:
                    running_models = {
                        str(item.get("name"))
                        for item in running_response.json().get("models", [])
                        if isinstance(item, dict) and item.get("name")
                    }
            except Exception:
                running_models = set()
    except Exception:
        # La indisponibilidad de Ollama no debe impedir la administración cloud.
        pass
    providers.append({
        "id": "ollama",
        "label": "Ollama local",
        "configured": True,
        "online": ollama_online,
        "models": [
            {
                "id": model,
                "label": f"{model} ({'activo en memoria' if model in running_models else 'local instalado'})",
                "available": True,
                "running": model in running_models,
            }
            for model in local_models
        ],
    })
    providers.append({
        "id": "custom",
        "label": "Otro proveedor / API compatible",
        "configured": True,
        "models": [],
    })
    return {
        "status": "success",
        "default": {
            "provider": default_provider,
            "model": {
                "openai": current.openai_model,
                "anthropic": current.anthropic_model,
                "gemini": current.gemini_model,
                "ollama": current.llm_model,
            }.get(default_provider, current.openai_model),
        },
        "providers": providers,
    }


async def validate_instance_llm_model(provider: str, model: str, *, allow_unchanged_local: bool = False) -> None:
    """Do not let an instance select an Ollama model that the local server cannot load."""
    provider = str(provider or "").strip().casefold()
    if provider != "ollama":
        return
    import httpx

    current = get_settings()
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{current.ollama_base_url.rstrip('/')}/api/tags")
        if response.status_code == 200:
            installed = {
                str(item.get("name", "")).casefold()
                for item in response.json().get("models", [])
                if isinstance(item, dict)
            }
            if model.casefold() in installed:
                return
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ese modelo local no está instalado en Ollama. Instálalo en el servidor y vuelve a seleccionarlo.",
            )
    except HTTPException:
        raise
    except Exception:
        if allow_unchanged_local:
            return
    if allow_unchanged_local:
        return
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Ollama no está disponible para comprobar el modelo local. Inicia Ollama y vuelve a intentarlo.",
    )


@router.get(
    "/api/admin/chatbot-instances",
    summary="Listar chatbots configurados",
    description="Lista las instancias adicionales y sus bases documentales independientes.",
)
async def list_chatbot_instances(
    start_date: Optional[str] = Query(default=None, description="Fecha inicio (YYYY-MM-DD o hoy)"),
    end_date: Optional[str] = Query(default=None, description="Fecha fin (YYYY-MM-DD o hoy)"),
) -> Dict[str, Any]:
    instances = []
    for profile in bot_instance_manager.list(include_disabled=True):
        paths = bot_instance_manager.paths(profile.bot_id)
        instances.append({
            **profile.admin_config(paths),
            "metrics": get_chatbot_instance_kpis(profile.bot_id, start_date, end_date),
        })
    return {"status": "success", "instances": instances}


@router.post(
    "/api/admin/chatbot-instances",
    summary="Crear chatbot para una dependencia",
    description="Registra una instancia independiente sin editar variables de entorno ni código.",
    status_code=status.HTTP_201_CREATED,
)
async def create_chatbot_instance(request: CreateBotInstanceRequest) -> Dict[str, Any]:
    if request.llm_provider == "custom":
        try:
            await run_in_threadpool(
                validate_custom_llm_base_url, request.llm_base_url, resolve_dns=True
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    await validate_instance_llm_model(request.llm_provider, request.llm_model)
    try:
        payload = request.model_dump(exclude={"llm_api_key"})
        payload["llm_api_key"] = request.llm_api_key.get_secret_value() if request.llm_api_key else ""
        profile = bot_instance_manager.create(**payload)
    except BotInstanceError as exc:
        code = status.HTTP_409_CONFLICT if "Ya existe" in str(exc) else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return {
        "status": "success",
        "message": f"Se creó la instancia {profile.display_name} para {profile.dependency_name}.",
        "instance": profile.admin_config(bot_instance_manager.paths(profile.bot_id)),
    }


@router.patch(
    "/api/admin/chatbot-instances/{bot_id}",
    summary="Editar una instancia de chatbot",
)
async def update_chatbot_instance(bot_id: str, request: UpdateBotInstanceRequest) -> Dict[str, Any]:
    existing = bot_instance_manager.get_any(bot_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe una instancia con ese identificador.")
    if request.llm_provider == "custom":
        try:
            await run_in_threadpool(
                validate_custom_llm_base_url, request.llm_base_url, resolve_dns=True
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    same_local_selection = (
        str(request.llm_provider).casefold(), request.llm_model
    ) == (existing.llm_provider, existing.llm_model)
    await validate_instance_llm_model(
        request.llm_provider,
        request.llm_model,
        allow_unchanged_local=same_local_selection,
    )
    try:
        payload = request.model_dump(exclude={"llm_api_key"})
        payload["llm_api_key"] = request.llm_api_key.get_secret_value() if request.llm_api_key else ""
        profile = bot_instance_manager.update(bot_id, **payload)
    except BotInstanceError as exc:
        code = status.HTTP_404_NOT_FOUND if "No existe" in str(exc) else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    paths = bot_instance_manager.paths(bot_id)
    return {
        "status": "success",
        "message": f"Se actualizaron los datos de {profile.display_name}.",
        "instance": {**profile.admin_config(paths), "metrics": get_chatbot_instance_kpis(bot_id)},
    }


@router.delete(
    "/api/admin/chatbot-instances/{bot_id}",
    summary="Desactivar una instancia conservando sus datos",
    description="Retira la instancia del enrutador y del acceso público. Conserva documentos, Markdown, índice y métricas para permitir reactivarla.",
)
async def deactivate_chatbot_instance(bot_id: str) -> Dict[str, Any]:
    try:
        profile = bot_instance_manager.set_enabled(bot_id, False)
    except BotInstanceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {
        "status": "success",
        "message": f"{profile.display_name} se desactivó. Sus documentos e índice se conservaron y puede reactivarse.",
        "data_retained": True,
    }


@router.post(
    "/api/admin/chatbot-instances/{bot_id}/reactivate",
    summary="Reactivar una instancia desactivada",
)
async def reactivate_chatbot_instance(bot_id: str) -> Dict[str, Any]:
    try:
        profile = bot_instance_manager.set_enabled(bot_id, True)
    except BotInstanceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    paths = bot_instance_manager.paths(bot_id)
    return {
        "status": "success",
        "message": f"{profile.display_name} quedó activo nuevamente.",
        "instance": {**profile.admin_config(paths), "metrics": get_chatbot_instance_kpis(bot_id)},
    }


@router.get(
    "/api/admin/chatbot-instances/{bot_id}/metrics",
    summary="Consultar métricas de una instancia",
)
async def get_chatbot_instance_metrics(
    bot_id: str,
    start_date: Optional[str] = Query(default=None, description="Fecha inicio (YYYY-MM-DD o hoy)"),
    end_date: Optional[str] = Query(default=None, description="Fecha fin (YYYY-MM-DD o hoy)"),
) -> Dict[str, Any]:
    profile = bot_instance_manager.get_any(bot_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe una instancia con ese identificador.")
    return {"status": "success", "bot_id": bot_id, "metrics": get_chatbot_instance_kpis(bot_id, start_date, end_date)}


def _instance_upload_stage(paths: Any, staged_id: str) -> tuple[Path, Path, Path]:
    """Resolve and constrain temporary upload paths to one chatbot instance."""
    if not re.fullmatch(r"[0-9a-f]{32}", staged_id or ""):
        raise HTTPException(status_code=422, detail="La sesión temporal no es válida.")
    root = paths.root.resolve()
    staging_root = (root / ".staged_uploads").resolve()
    if root not in staging_root.parents:
        raise HTTPException(status_code=400, detail="La carpeta temporal de la instancia no es válida.")
    staging_root.mkdir(parents=True, exist_ok=True)
    stage_dir = (staging_root / staged_id).resolve()
    if staging_root not in stage_dir.parents:
        raise HTTPException(status_code=400, detail="La ruta temporal de la instancia no es válida.")
    return stage_dir, stage_dir / "source", stage_dir / "sanitized_docs"


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _serialize_redundancy_report(rep: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    overlapping_sources = []
    for source, data in sorted(
        (rep.get("overlapping_sources") or {}).items(),
        key=lambda item: item[1].get("max_similarity", 0),
        reverse=True,
    ):
        overlapping_sources.append({
            "source": str(source),
            "matched_chunks": int(data.get("count", 0)),
            "redundant_count": int(data.get("redundant_count", 0)),
            "ambiguous_count": int(data.get("ambiguous_count", 0)),
            "max_similarity": round(float(data.get("max_similarity", 0.0)) * 100, 1),
            "sample_snippet": str(data.get("sample_snippet") or ""),
            "matched_sample_snippet": str(data.get("matched_sample_snippet") or ""),
        })
    detailed_chunks = []
    for index, item in enumerate(rep.get("chunk_results") or [], start=1):
        chunk = item.get("chunk")
        detailed_chunks.append({
            "index": index,
            "content_snippet": chunk.page_content.strip() if chunk else "",
            "matched_chunk_snippet": str(item.get("matched_chunk_snippet") or ""),
            "similarity": round(float(item.get("similarity", 0.0)) * 100, 1),
            "matched_source": item.get("matched_source") or "Ninguno",
            "is_redundant": bool(item.get("is_redundant", False)),
            "is_ambiguous": bool(item.get("is_ambiguous", False)),
            "status": item.get("status", "novel"),
        })
    return overlapping_sources, detailed_chunks


async def _finish_instance_document_upload(
    bot_id: str,
    profile: Any,
    paths: Any,
    filename: str,
) -> dict[str, Any]:
    specialization_path = None
    warning = None
    try:
        specialization_path = await run_in_threadpool(bot_instance_manager.refresh_specialization_profile, bot_id)
    except Exception as exc:
        logger.warning("El documento se indexó, pero no se pudo actualizar el perfil de '%s': %s", bot_id, type(exc).__name__)
        warning = "El documento y el índice se actualizaron, pero el perfil de especialidad no pudo actualizarse."
    return {
        "status": "success",
        "message": warning or f"'{filename}' quedó convertido a Markdown e indexado para {profile.dependency_name}; el perfil de especialidad también se actualizó.",
        "specialization_profile": str(specialization_path) if specialization_path else None,
        "instance": profile.admin_config(paths),
    }


@router.post(
    "/api/admin/chatbot-instances/{bot_id}/documents/audit",
    summary="Analizar ambigüedad y redundancia antes de cargar a una instancia",
    description="Genera Markdown validado, lo compara con el original y mide similitud únicamente contra el índice privado de la instancia.",
)
async def audit_chatbot_instance_document(
    bot_id: str,
    file: UploadFile = File(...),
    threshold: float = Form(0.85, ge=0.0, le=1.0),
    ambiguity_threshold: float = Form(0.65, ge=0.0, le=1.0),
) -> Dict[str, Any]:
    profile = bot_instance_manager.get(bot_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="No existe una instancia activa con ese identificador.")
    filename = validated_filename(file.filename)
    if Path(filename).suffix.casefold() not in {".pdf", ".pptx", ".docx"}:
        raise HTTPException(status_code=415, detail="Solo se admiten documentos PDF, PPTX y DOCX.")

    async with bot_instance_manager.get_ingestion_lock(bot_id):
        paths = bot_instance_manager.paths(bot_id)
        if (paths.docs / filename).exists():
            raise HTTPException(status_code=409, detail="Ya existe un documento con ese nombre en esta instancia. Cambia el nombre antes de analizarlo.")
        staged_id = uuid.uuid4().hex
        stage_dir, source_dir, output_dir = _instance_upload_stage(paths, staged_id)
        source_dir.mkdir(parents=True, exist_ok=False)
        staged_source = source_dir / filename
        try:
            await save_upload(file, staged_source, settings.max_upload_size_mb * 1024 * 1024)
            runtime = bot_instance_manager.get_runtime(bot_id)
            prepared = await run_in_threadpool(runtime.prepare_document_for_audit, staged_source, output_dir)
            record = prepared["record"]
            relative_markdown = Path(str(record.get("markdown_relative_path") or ""))
            markdown_path = (output_dir / relative_markdown).resolve()
            if output_dir.resolve() not in markdown_path.parents or not markdown_path.is_file():
                raise RuntimeError("No se encontró el Markdown validado dentro del área temporal de la instancia.")
            if _sha256_path(staged_source) != record.get("source_sha256") or _sha256_path(markdown_path) != record.get("markdown_sha256"):
                raise RuntimeError("El original o el Markdown cambió después de la validación de fidelidad.")

            audit = prepared["fidelity_audit"]
            if prepared.get("status") == "review_required" or audit.get("status") != "coincide":
                meta = {
                    "bot_id": bot_id,
                    "staged_id": staged_id,
                    "filename": filename,
                    "source_sha256": record["source_sha256"],
                    "markdown_sha256": record["markdown_sha256"],
                    "record": record,
                    "fidelity_audit": audit,
                    "status": "review_required",
                    "created_at": datetime.now().isoformat(),
                }
                meta_path = stage_dir / "audit.json"
                meta_tmp = stage_dir / "audit.json.tmp"
                meta_tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(meta_tmp, meta_path)
                return {
                    "status": "review_required",
                    "bot_id": bot_id,
                    "staged_id": staged_id,
                    "filename": filename,
                    "message": "El borrador no alcanzó una coincidencia verificable después de la corrección automática. Se conservó para revisión y no se indexó.",
                    "fidelity_audit": audit,
                    "fidelity_repair_attempts": prepared.get("fidelity_repair_attempts", 0),
                    "markdown_preview": markdown_path.read_text(encoding="utf-8")[:12000],
                    "markdown_preview_truncated": markdown_path.stat().st_size > 12000,
                }

            chunks = split_markdown_for_rag(
                markdown_path.read_text(encoding="utf-8"),
                {
                    "source": filename,
                    "source_filename": filename,
                    "source_path": filename,
                    "indexed_format": "markdown",
                },
            )
            vector_store = runtime.rag.vector_store
            embeddings = runtime.rag.embeddings
            if vector_store is None or embeddings is None:
                raise RuntimeError("El índice privado o el modelo de embeddings no están disponibles para el análisis.")
            rep = calculate_chunk_redundancy(
                chunks=chunks,
                vector_store=vector_store,
                embeddings=embeddings,
                threshold=threshold,
                ambiguity_threshold=ambiguity_threshold,
                exclude_source=None,
                batch_size=32,
            )
            if len(rep.get("chunk_results") or []) != len(chunks):
                raise RuntimeError("No se pudo comparar todo el Markdown con el índice privado.")

            overlapping_sources, detailed_chunks = _serialize_redundancy_report(rep)
            redundancy_ratio = round(float(rep.get("redundancy_ratio", 0.0)), 1)
            ambiguity_ratio = round(float(rep.get("ambiguity_ratio", 0.0)), 1)
            redundant_count = int(rep.get("redundant_count", 0))
            ambiguous_count = int(rep.get("ambiguous_count", 0))
            total_chunks = len(chunks)
            overall_status = "redundant" if redundant_count or redundancy_ratio >= 20.0 else (
                "ambiguous" if ambiguous_count or ambiguity_ratio >= 10.0 else "clean"
            )
            metrics = {
                "total_chunks": total_chunks,
                "novel_chunks": int(rep.get("novel_count", 0)),
                "ambiguous_chunks": ambiguous_count,
                "redundant_chunks": redundant_count,
                "ambiguity_ratio": ambiguity_ratio,
                "redundancy_ratio": redundancy_ratio,
            }
            meta = {
                "bot_id": bot_id,
                "staged_id": staged_id,
                "filename": filename,
                "source_sha256": record["source_sha256"],
                "markdown_sha256": record["markdown_sha256"],
                "record": record,
                "fidelity_audit": audit,
                "primary_overlapping_source": overlapping_sources[0]["source"] if overlapping_sources else None,
                "overlapping_sources": [item["source"] for item in overlapping_sources],
                "metrics": metrics,
                "overall_status": overall_status,
                "created_at": datetime.now().isoformat(),
            }
            meta_path = stage_dir / "audit.json"
            meta_tmp = stage_dir / "audit.json.tmp"
            meta_tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(meta_tmp, meta_path)
            return {
                "status": "success",
                "bot_id": bot_id,
                "staged_id": staged_id,
                "filename": filename,
                "threshold": threshold,
                "ambiguity_threshold": ambiguity_threshold,
                "ambiguity_detected": bool(ambiguous_count or ambiguity_ratio >= 10.0),
                "redundancy_detected": bool(redundant_count or redundancy_ratio >= 20.0),
                "overall_status": overall_status,
                "metrics": metrics,
                "fidelity_audit": {
                    "status": audit.get("status"),
                    "summary": audit.get("summary"),
                    "provider": audit.get("provider"),
                    "model": audit.get("model"),
                    "contingency": audit.get("contingency", False),
                },
                "primary_overlapping_source": meta["primary_overlapping_source"],
                "overlapping_sources": overlapping_sources,
                "detailed_chunks": detailed_chunks,
            }
        except HTTPException:
            shutil.rmtree(stage_dir, ignore_errors=True)
            raise
        except Exception as exc:
            shutil.rmtree(stage_dir, ignore_errors=True)
            logger.exception("Falló la preauditoría del documento de '%s' (%s)", bot_id, filename)
            raise HTTPException(
                status_code=422,
                detail="No se pudo validar y analizar el documento. No se agregó al índice de esta dependencia.",
            ) from exc


@router.post(
    "/api/admin/chatbot-instances/{bot_id}/documents/resolve",
    summary="Resolver la auditoría de un documento de instancia",
    description="Indexa el Markdown validado solo en el Chroma privado de la instancia o descarta la carga temporal.",
)
async def resolve_chatbot_instance_document(
    bot_id: str,
    request: ResolveInstanceUploadRequest,
) -> Dict[str, Any]:
    profile = bot_instance_manager.get(bot_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="No existe una instancia activa con ese identificador.")
    async with bot_instance_manager.get_ingestion_lock(bot_id):
        paths = bot_instance_manager.paths(bot_id)
        stage_dir, source_dir, output_dir = _instance_upload_stage(paths, request.staged_id)
        meta_path = stage_dir / "audit.json"
        if not meta_path.is_file() or meta_path.is_symlink():
            raise HTTPException(status_code=404, detail="La auditoría temporal no existe o ya fue procesada.")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=409, detail="No se pudo leer la auditoría temporal; vuelve a analizar el archivo.") from exc
        if meta.get("bot_id") != bot_id or meta.get("staged_id") != request.staged_id:
            raise HTTPException(status_code=403, detail="La auditoría no corresponde a esta instancia.")
        filename = validated_filename(meta.get("filename"))
        staged_source = source_dir / filename
        if request.action == "cancel":
            shutil.rmtree(stage_dir, ignore_errors=True)
            return {"status": "cancelled", "action": "cancel", "filename": filename, "message": "Se descartó el archivo temporal; la instancia no tuvo cambios."}
        if not staged_source.is_file() or staged_source.is_symlink():
            raise HTTPException(status_code=404, detail="No se encontró el original temporal; vuelve a cargarlo.")
        if _sha256_path(staged_source) != meta.get("source_sha256"):
            raise HTTPException(status_code=409, detail="El original cambió desde la auditoría; vuelve a analizarlo.")

        target_to_replace = None
        if request.action == "replace":
            try:
                target_to_replace = validated_filename(request.target_to_replace)
            except HTTPException as exc:
                raise HTTPException(status_code=422, detail="Selecciona el documento de esta instancia que quieres reemplazar.") from exc
            if target_to_replace not in set(meta.get("overlapping_sources") or []) or target_to_replace == filename:
                raise HTTPException(status_code=422, detail="El documento seleccionado no pertenece a las coincidencias de esta auditoría.")
            if not (paths.docs / target_to_replace).is_file():
                raise HTTPException(status_code=404, detail="El documento seleccionado ya no está en esta instancia.")

        record = meta.get("record")
        if not isinstance(record, dict) or record.get("status") != "success":
            raise HTTPException(status_code=409, detail="La auditoría no contiene un Markdown validado; analiza el archivo de nuevo.")
        if (meta.get("fidelity_audit") or {}).get("status") != "coincide":
            raise HTTPException(status_code=422, detail="El Markdown no coincide suficientemente con el original y no se puede indexar.")
        relative_markdown = Path(str(record.get("markdown_relative_path") or ""))
        staged_markdown = (output_dir / relative_markdown).resolve()
        if output_dir.resolve() not in staged_markdown.parents or not staged_markdown.is_file() or staged_markdown.is_symlink():
            raise HTTPException(status_code=409, detail="No se encontró el Markdown temporal validado; vuelve a analizar el archivo.")
        if _sha256_path(staged_markdown) != meta.get("markdown_sha256"):
            raise HTTPException(status_code=409, detail="El Markdown cambió después de su validación; vuelve a analizar el archivo.")

        paths.docs.mkdir(parents=True, exist_ok=True)
        paths.markdown.mkdir(parents=True, exist_ok=True)
        instance_root = paths.root.resolve()
        for storage_path in (paths.docs, paths.markdown):
            if instance_root not in storage_path.resolve().parents:
                raise HTTPException(status_code=400, detail="Una carpeta de datos apunta fuera de esta instancia.")
        manifest_path = paths.markdown / "manifest.json"
        if manifest_path.is_symlink():
            raise HTTPException(status_code=400, detail="El manifiesto de esta instancia no tiene una ruta válida.")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {"schema_version": 2, "records": {}}
            if not isinstance(manifest, dict) or not isinstance(manifest.get("records", {}), dict):
                raise ValueError("estructura inválida")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail="El manifiesto de esta instancia no se puede leer; no se indexó el documento.") from exc
        destination = paths.docs / filename
        if destination.is_symlink():
            raise HTTPException(status_code=400, detail="El destino del documento no es válido.")
        if destination.exists() and _sha256_path(destination) != meta["source_sha256"]:
            raise HTTPException(status_code=409, detail="Ya existe otro documento con ese nombre en esta instancia.")
        final_markdown = (paths.markdown / relative_markdown).resolve()
        if paths.markdown.resolve() not in final_markdown.parents:
            raise HTTPException(status_code=400, detail="La ruta del Markdown no es válida para esta instancia.")
        final_markdown.parent.mkdir(parents=True, exist_ok=True)
        if final_markdown.is_symlink():
            raise HTTPException(status_code=400, detail="El destino del Markdown no es válido.")
        if final_markdown.exists() and _sha256_path(final_markdown) != meta["markdown_sha256"]:
            raise HTTPException(status_code=409, detail="Ya existe un Markdown distinto para este documento.")
        created_source = False
        created_markdown = False
        manifest_tmp = manifest_path.with_name(f".{request.staged_id}-manifest.tmp")
        try:
            if not destination.exists():
                temporary_source = paths.docs / f".upload-{request.staged_id}-{filename}"
                try:
                    shutil.copy2(staged_source, temporary_source)
                    os.replace(temporary_source, destination)
                    created_source = True
                finally:
                    temporary_source.unlink(missing_ok=True)
            if not final_markdown.exists():
                temporary_markdown = final_markdown.with_name(f".{request.staged_id}-{final_markdown.name}.tmp")
                try:
                    shutil.copyfile(staged_markdown, temporary_markdown)
                    os.replace(temporary_markdown, final_markdown)
                    created_markdown = True
                finally:
                    temporary_markdown.unlink(missing_ok=True)

            source_stat = destination.stat()
            record.update({
                "source_path": filename,
                "source": filename,
                "source_filename": filename,
                "source_size_bytes": source_stat.st_size,
                "source_mtime_ns": source_stat.st_mtime_ns,
                "fidelity_audit": meta["fidelity_audit"],
            })
            manifest.setdefault("records", {})[filename] = record
            manifest["transform_provider"] = record.get("transform_provider", "openai")
            manifest["transform_model"] = record.get("transform_model", "gpt-6-luna")
            manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(manifest_tmp, manifest_path)
        except Exception:
            if created_source:
                destination.unlink(missing_ok=True)
            if created_markdown:
                final_markdown.unlink(missing_ok=True)
            raise
        finally:
            manifest_tmp.unlink(missing_ok=True)

        try:
            runtime = bot_instance_manager.get_runtime(bot_id)
            indexed = await run_in_threadpool(runtime.ingest_document, paths, str(destination))
            if not indexed:
                raise RuntimeError("La transformación o indexación Markdown no terminó correctamente.")
            if target_to_replace:
                removed = await run_in_threadpool(runtime.delete_document, paths, target_to_replace)
                if not removed:
                    raise RuntimeError("El documento nuevo se indexó, pero no fue posible retirar la versión anterior.")
        except Exception as exc:
            logger.error("No se pudo completar la carga auditada '%s' de '%s': %s", filename, bot_id, exc, exc_info=True)
            raise HTTPException(
                status_code=422,
                detail="El archivo y su Markdown validado se conservaron en la instancia, pero la indexación no terminó. Puedes reintentar la acción desde la misma auditoría.",
            ) from exc

        shutil.rmtree(stage_dir, ignore_errors=True)
        result = await _finish_instance_document_upload(bot_id, profile, paths, filename)
        result["action"] = request.action
        if request.action == "deduplicate":
            result["message"] = f"'{filename}' quedó indexado en {profile.dependency_name}. Se conservaron todos los fragmentos; el análisis solo informa similitud y no elimina evidencia automáticamente."
        return result


@router.post(
    "/api/admin/chatbot-instances/{bot_id}/documents",
    summary="Subir directamente e indexar un documento de un chatbot",
    description="Conserva PDF/PPTX/DOCX, genera Markdown, verifica su fidelidad al original y lo indexa exclusivamente en el Chroma de la dependencia.",
)
async def upload_chatbot_instance_document(
    bot_id: str,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    profile = bot_instance_manager.get(bot_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="No existe una instancia activa con ese identificador.")
    filename = validated_filename(file.filename)
    if Path(filename).suffix.casefold() not in {".pdf", ".pptx", ".docx"}:
        raise HTTPException(status_code=415, detail="Solo se admiten documentos PDF, PPTX y DOCX.")

    async with bot_instance_manager.get_ingestion_lock(bot_id):
        paths = bot_instance_manager.paths(bot_id)
        paths.docs.mkdir(parents=True, exist_ok=True)
        destination = paths.docs / filename
        if destination.exists():
            raise HTTPException(
                status_code=409,
                detail="Ya existe un documento con ese nombre en esta instancia. Cambia el nombre del archivo antes de cargarlo.",
            )
        await save_upload(file, destination, settings.max_upload_size_mb * 1024 * 1024)
        try:
            runtime = bot_instance_manager.get_runtime(bot_id)
            indexed = await run_in_threadpool(runtime.ingest_document, paths, str(destination))
            if not indexed:
                raise RuntimeError("La transformación o indexación Markdown no terminó correctamente.")
        except Exception as exc:
            logger.error("No se indexó '%s' para el chatbot '%s': %s", filename, bot_id, exc, exc_info=True)
            raise HTTPException(
                status_code=422,
                detail="El archivo se conservó en la instancia, pero no se pudo validar o indexar. Revisa el estado de la ingesta en la terminal.",
            ) from exc
        return await _finish_instance_document_upload(bot_id, profile, paths, filename)


# =============================================================================
# 6. ESTADO GENERAL DEL SISTEMA (/api/admin/system-status)
# =============================================================================

@router.get(
    "/api/admin/system-status",
    summary="Estado de la Infraestructura del Sistema",
    description="Retorna el estado de Ollama, GPU activa, base de datos de telemetría y ChromaDB."
)
async def get_system_status() -> Dict[str, Any]:
    """Retorna información de diagnóstico y salud de la infraestructura."""
    import httpx
    
    # Chequeo LLM activo (Anthropic / Gemini / OpenAI / Ollama)
    from app.services.llm_client import get_llm_client
    llm_client = get_llm_client()
    llm_health = await llm_client.check_health()
    llm_ok = llm_health.get("active", False)

    ollama_ok = False
    models_available = []
    cloud_providers = ("anthropic", "gemini", "openai")
    if llm_client.provider == "ollama":
        ollama_ok = llm_ok
        models_available = llm_health.get("models_in_server", [])
    else:
        # Chequeo secundario a Ollama local si el principal es en la nube
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                r = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
                if r.status_code == 200:
                    ollama_ok = True
                    models_available = [m.get("name") for m in r.json().get("models", [])]
        except Exception:
            ollama_ok = False

    # Chequeo GPU / Aceleración
    gpu_info = f"CPU / Cloud API ({llm_client.provider.upper()})" if llm_client.provider in cloud_providers else "CPU (Modo Fallback)"
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(torch.cuda.get_device_properties(0).total_mem / (1024**3), 1)
            gpu_info = f"{gpu_name} ({vram_gb} GB VRAM)"
    except Exception:
        pass

    # Conteo de Documentos en disco
    total_docs = 0
    if DOCS_DIR.exists():
        for _, _, files in os.walk(DOCS_DIR):
            total_docs += len([f for f in files if f.endswith(('.pdf', '.docx', '.pptx', '.txt'))])

    active_endpoint = llm_health.get("endpoint", "")
    if not active_endpoint:
        if llm_client.provider == "gemini":
            active_endpoint = settings.gemini_base_url
        elif llm_client.provider == "openai":
            active_endpoint = settings.openai_base_url
        elif llm_client.provider == "anthropic":
            active_endpoint = settings.anthropic_base_url
        else:
            active_endpoint = settings.ollama_base_url

    return {
        "status": "online",
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "gpu_active": gpu_info,
        "llm": {
            "provider": llm_client.provider,
            "active_model": llm_client.active_model,
            "active": llm_ok,
            "endpoint": active_endpoint
        },
        "ollama": {
            "endpoint": active_endpoint,
            "active": llm_ok if llm_client.provider in cloud_providers else ollama_ok,
            "model_configured": llm_client.active_model if llm_client.provider in cloud_providers else settings.llm_model,
            "models_in_server": [llm_client.active_model] if llm_client.provider in cloud_providers else models_available
        },
        "glpi": {
            "endpoint": settings.glpi_base_url,
            "configured": bool(settings.glpi_app_token and settings.glpi_user_token)
        },
        "knowledge_base": {
            "docs_directory": str(DOCS_DIR.resolve()),
            "total_source_files": total_docs,
            "chroma_directory": str(Path(settings.chroma_db_dir).resolve())
        }
    }
