"""
Router Administrativo y de Gestión de Base de Conocimiento para UniMon (USB).
Provee endpoints para el panel de administración (/admin), subida de documentos,
re-indexación en ChromaDB y consulta de estado del sistema.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

import uuid
import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import get_settings
from app.services.rag_service import rag_service
from app.services.telemetry_service import get_kpis_summary
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
    tags=["Panel de Administración UniMon"]
)

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DOCS_DIR = Path(settings.docs_dir)
STAGED_DIR = Path("data/scratch/staged_uploads")
STAGED_DIR.mkdir(parents=True, exist_ok=True)


class ResolveUploadRequest(BaseModel):
    staged_id: str = Field(..., description="ID de sesión temporal de subida")
    action: str = Field(..., description="Acción de resolución: 'replace', 'deduplicate', 'force' o 'cancel'")
    target_to_replace: Optional[str] = Field(default=None, description="Documento previo a purgar (opcional)")


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
            txt = "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()
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
    description="Retorna el listado de documentos PDF/DOCX disponibles en data/docs con metadatos de tamaño y fecha."
)
async def list_documents() -> Dict[str, Any]:
    """Retorna todos los documentos almacenados en data/docs/."""
    docs_list = []
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    allowed_exts = {".pdf", ".docx", ".pptx", ".txt", ".xlsx", ".csv", ".md"}

    for root, _, files in os.walk(DOCS_DIR):
        for file in sorted(files):
            file_path = Path(root) / file
            if file_path.suffix.lower() in allowed_exts:
                stat = file_path.stat()
                rel_path = file_path.relative_to(DOCS_DIR).as_posix()
                
                # Determinar categoría o carpeta contenedora
                folder = file_path.parent.name if file_path.parent != DOCS_DIR else "Raíz"
                audience_label = "General"
                if "estudiante" in folder.lower():
                    audience_label = "Estudiante"
                elif "profesor" in folder.lower() or "docente" in folder.lower():
                    audience_label = "Profesor / Docente"
                elif "funcionario" in folder.lower() or "gestion" in folder.lower() or "admin" in folder.lower():
                    audience_label = "Administrativo"
                elif "general" in folder.lower() or "normativa" in folder.lower():
                    audience_label = "General / Normativa"

                docs_list.append({
                    "filename": file,
                    "relative_path": rel_path,
                    "folder": folder,
                    "audience": audience_label,
                    "size_bytes": stat.st_size,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "size_formatted": f"{round(stat.st_size / 1024, 1)} KB" if stat.st_size < 1024*1024 else f"{round(stat.st_size / (1024*1024), 2)} MB",
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "extension": file_path.suffix.lower().replace(".", "")
                })

    return {
        "status": "success",
        "total_documents": len(docs_list),
        "documents": docs_list
    }


# =============================================================================
# 3. CARGA DE NUEVOS DOCUMENTOS (/api/admin/upload-doc)
# =============================================================================

@router.post(
    "/api/admin/upload-doc",
    summary="Subir Documento a la Base de Conocimiento",
    description="Sube un archivo PDF/DOCX y lo asigna a la carpeta correspondiente según la audiencia."
)
async def upload_document(
    file: UploadFile = File(...),
    audience: str = Form("general"),
    auto_index: bool = Form(False)
) -> Dict[str, Any]:
    """Recibe un archivo y lo almacena en la estructura de data/docs/."""
    filename = Path(file.filename).name
    if not filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")

    ext = Path(filename).suffix.lower()
    allowed_exts = {".pdf", ".docx", ".pptx", ".txt", ".xlsx", ".md"}
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión '{ext}' no soportada. Use: {', '.join(allowed_exts)}"
        )

    # Determinar subdirectorio según audiencia
    subfolder_name = AUDIENCE_FOLDER_MAP.get(audience.lower().strip(), "4_general_normativa")
    target_dir = DOCS_DIR / subfolder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    dest_path = target_dir / filename

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = dest_path.stat().st_size
        logger.info(f"✅ Documento '{filename}' guardado en: {dest_path} ({file_size} bytes)")

        # Si se solicitó auto-indexar este archivo inmediatamente
        indexing_result = None
        if auto_index:
            try:
                ingest_multimodal(file_path=str(dest_path), incremental=True)
                apply_taxonomy_to_chroma()
                indexing_result = "Indexado inmediatamente en ChromaDB."
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

    except Exception as e:
        logger.error(f"Error guardando documento '{filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Error al guardar archivo en el servidor: {str(e)}")


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
    filename = Path(file.filename).name
    if not filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")

    ext = Path(filename).suffix.lower()
    allowed_exts = {".pdf", ".docx", ".pptx", ".txt", ".xlsx", ".md"}
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión '{ext}' no soportada. Use: {', '.join(allowed_exts)}"
        )

    staged_id = uuid.uuid4().hex[:10]
    staged_filename = f"{staged_id}_{filename}"
    staged_file_path = STAGED_DIR / staged_filename

    try:
        with open(staged_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

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

    except Exception as e:
        logger.error(f"Error auditando documento '{filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error durante la auditoría del documento: {str(e)}")


@router.post(
    "/api/admin/resolve-upload",
    summary="Resolver Ingesta de Documento Auditado",
    description="Aplica una de las 4 acciones de resolución: replace, deduplicate, force o cancel."
)
async def resolve_staged_upload(
    request: ResolveUploadRequest
) -> Dict[str, Any]:
    """Aplica la resolución elegida por el administrador para un documento en staging."""
    clean_staged_id = Path(request.staged_id).name
    meta_file = STAGED_DIR / f"{clean_staged_id}_meta.json"

    if not meta_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Sesión de carga temporal '{clean_staged_id}' no encontrada o ya procesada."
        )

    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        staged_path = Path(meta.get("staged_path", ""))
        filename = meta.get("filename", "")
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
        shutil.copy2(staged_path, dest_path)

        # 2. CASO: Actualizar / Reemplazar Documento Existente
        if request.action == "replace":
            target_to_purge = request.target_to_replace or meta.get("primary_overlapping_source") or filename
            if target_to_purge:
                logger.info(f"🔄 Reemplazando: Purgando fragmentos previos de '{target_to_purge}'...")
                try:
                    vs = rag_service.vector_store
                    if vs is not None:
                        delete_document_chunks(vs, target_to_purge)
                except Exception as exc:
                    logger.warning(f"Aviso purgando chunks de '{target_to_purge}': {exc}")

                # Si el archivo previo tiene otro nombre y está en data/docs, eliminarlo
                if target_to_purge != filename:
                    for root, _, files in os.walk(DOCS_DIR):
                        if target_to_purge in files:
                            try:
                                (Path(root) / target_to_purge).unlink()
                                logger.info(f"🗑️ Archivo físico anterior '{target_to_purge}' eliminado.")
                            except Exception as exc:
                                logger.warning(f"Aviso eliminando archivo físico {target_to_purge}: {exc}")

            # Purgar también cualquier fragmento previo del nombre nuevo
            try:
                vs = rag_service.vector_store
                if vs is not None:
                    delete_document_chunks(vs, filename)
            except Exception:
                pass

            # Ingestar la nueva versión completa
            ingest_multimodal(file_path=str(dest_path), incremental=False, deduplicate=False)
            apply_taxonomy_to_chroma()
            rag_service.reload_vector_store()

            msg = f"Versión anterior de '{target_to_purge or filename}' purgada y nueva versión de '{filename}' indexada."

        # 3. CASO: Guardar como Nuevo (con Deduplicación de Fragmentos)
        elif request.action == "deduplicate":
            logger.info(f"🛡️ Deduplicación activa para '{filename}'...")
            ingest_multimodal(file_path=str(dest_path), incremental=False, deduplicate=True, similarity_threshold=0.85)
            apply_taxonomy_to_chroma()
            rag_service.reload_vector_store()

            msg = f"Documento '{filename}' indexado exitosamente conservando únicamente fragmentos novedosos."

        # 4. CASO: Forzar Indexación Completa (Sin Filtrado)
        elif request.action == "force":
            logger.info(f"⚡ Ingesta forzada completa para '{filename}'...")
            ingest_multimodal(file_path=str(dest_path), incremental=False, deduplicate=False)
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
        raise HTTPException(status_code=500, detail=f"Error resolviendo la subida del documento: {str(e)}")


# =============================================================================
# 4. RE-INDEXACIÓN DE BASE VECTORIAL (/api/admin/reindex)
# =============================================================================

@router.post(
    "/api/admin/reindex",
    summary="Re-indexar Base Vectorial ChromaDB",
    description="Ejecuta la ingesta multimodal sobre todos los documentos de data/docs y actualiza la taxonomía."
)
async def reindex_knowledge_base(
    incremental: bool = Query(default=True, description="Procesar solo documentos nuevos o modificados"),
    wipe_db: bool = Query(default=False, description="Borrar completamente la base vectorial previa")
) -> Dict[str, Any]:
    """Dispara el pipeline de ingesta multimodal hacia ChromaDB."""
    try:
        start_time = datetime.now()
        logger.info(f"🔄 Iniciando Re-indexación de ChromaDB (incremental={incremental}, wipe_db={wipe_db})...")

        # Ejecutar ingesta
        success = ingest_multimodal(
            incremental=incremental,
            wipe_db=wipe_db
        )

        # Aplicar taxonomía de metadatos (roles, categorías)
        taxonomy_updated = 0
        try:
            taxonomy_updated = apply_taxonomy_to_chroma()
        except Exception as tax_err:
            logger.warning(f"Aviso al actualizar taxonomía: {tax_err}")

        elapsed_sec = round((datetime.now() - start_time).total_seconds(), 2)

        return {
            "status": "success" if success else "warning",
            "message": "Base vectorial ChromaDB re-indexada exitosamente." if success else "La ingesta finalizó con advertencias.",
            "duration_seconds": elapsed_sec,
            "incremental": incremental,
            "wipe_db": wipe_db,
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
    
    # Chequeo Ollama
    ollama_ok = False
    models_available = []
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            if r.status_code == 200:
                ollama_ok = True
                models_available = [m.get("name") for m in r.json().get("models", [])]
    except Exception:
        ollama_ok = False

    # Chequeo GPU
    gpu_info = "CPU (Modo Fallback)"
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

    return {
        "status": "online",
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "gpu_active": gpu_info,
        "ollama": {
            "endpoint": settings.ollama_base_url,
            "active": ollama_ok,
            "model_configured": settings.llm_model,
            "models_in_server": models_available
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
