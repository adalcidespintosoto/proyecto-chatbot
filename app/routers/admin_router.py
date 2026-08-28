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

from app.config import get_settings
from app.services.telemetry_service import get_kpis_summary
from scripts.ingest_multimodal_docs import ingest_multimodal
from scripts.apply_document_taxonomy import run_taxonomy_update as apply_taxonomy_to_chroma

logger = logging.getLogger("unimon.admin_router")

router = APIRouter(
    tags=["Panel de Administración UniMon"]
)

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
