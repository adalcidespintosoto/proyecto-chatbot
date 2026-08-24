"""
Router para los endpoints de Chat y Soporte Técnico de UniMon (USB).
Define los esquemas de validación Pydantic y procesa las peticiones de los usuarios.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.router_logic import router_logic, RouterLogic, EstadoTicket, IntentType
from app.services.glpi_service import glpi_client, GLPIService, GLPIException, is_valid_email
from app.services.rag_service import rag_service, RAGService

logger = logging.getLogger("unimon.chat_router")


router = APIRouter(
    prefix="/api",
    tags=["Chat & Soporte UniMon"]
)


# ==========================================
# Esquemas Pydantic para el Endpoint de Chat
# ==========================================

class ChatRequest(BaseModel):
    """
    Petición enviada al endpoint /api/chat.
    Admite tanto 'mensaje' como 'message' para máxima compatibilidad.
    """
    mensaje: Optional[str] = Field(default=None, description="Mensaje o consulta técnica enviada por el usuario", example="No enciende el computador de la sala 2.")
    message: Optional[str] = Field(default=None, description="Alias en inglés para el mensaje", example="No enciende el computador de la sala 2.")
    session_id: Optional[str] = Field(default="default_session", description="Identificador único de la sesión conversacional", example="sess_12345")

    def get_texto(self) -> str:
        """Obtiene el texto del mensaje asegurando no vacíos."""
        return (self.mensaje or self.message or "").strip()


class ChatResponse(BaseModel):
    """
    Respuesta generada por UniMon según la máquina de estados de Nivel 1 y GLPI.
    """
    tipo: str = Field(..., description="Tipo de respuesta (SALUDO, DIAGNOSTICO, SOLUCIONADO, RADICANDO_TICKET, TICKET_CREADO, ERROR)", example="DIAGNOSTICO")
    mensaje: str = Field(..., description="Mensaje de respuesta en lenguaje natural para el usuario en español")
    ticket_id: Optional[Any] = Field(default=None, description="ID del ticket en GLPI si fue generado", example=1042)

    # Campos de compatibilidad para clientes web existentes
    intent: Optional[str] = Field(default=None, description="Alias de compatibilidad para tipo")
    reply: Optional[str] = Field(default=None, description="Alias de compatibilidad para mensaje")
    ticket_details: Optional[Dict[str, Any]] = Field(default=None, description="Detalles del ticket si fue generado")
    category: Optional[str] = Field(default=None, description="Categoría temática del problema")
    source: Optional[str] = Field(default=None, description="Fuente de la respuesta (GLPI, Ollama, Base de Conocimiento)", example="GLPI_REST_API")
    sources: Optional[List[str]] = Field(default=None, description="Fuentes documentales consultadas en RAG", example=["P-GT-01_Mantenimiento.pdf"])


# ==========================================
# Instancias de Servicios
# ==========================================

from app.services.router_logic import router_logic
from app.services.rag_service import rag_service


# ==========================================
# Endpoint Principal: POST /api/chat
# ==========================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesar mensaje del usuario con Chatbot de Nivel 1 y Router de Intención",
    description="Orquesta el diagnóstico proactivo de Nivel 1 con RAG (Llama 3.1) o la captura conversacional y radicación de tickets en GLPI."
)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal para interacción con el Asistente Virtual UniMon.
    Conecta directamente con router_logic.procesar_mensaje(mensaje, session_id).
    """
    texto = request.get_texto()
    if not texto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El campo 'mensaje' no puede estar vacío."
        )

    session_id = request.session_id or "default_session"

    logger.info(f"Procesando mensaje para session_id '{session_id}' (longitud: {len(texto)} chars): '{texto}'")

    # Invocar lógica conversacional del router de intenciones
    resultado = await router_logic.procesar_mensaje(mensaje=texto, session_id=session_id)

    tipo = resultado.get("tipo", "DIAGNOSTICO")
    mensaje_resp = resultado.get("mensaje", "")
    ticket_id = resultado.get("ticket_id")

    return ChatResponse(
        tipo=tipo,
        mensaje=mensaje_resp,
        ticket_id=ticket_id,
        intent=tipo,
        reply=mensaje_resp,
        ticket_details=resultado.get("ticket_details"),
        category=resultado.get("category"),
        source=resultado.get("source"),
        sources=resultado.get("sources")
    )





# ==========================================
# Endpoints de Administración de Documentos RAG
# ==========================================

from fastapi import UploadFile, File
from pathlib import Path
from app.config import get_settings
from scripts.ingest_multimodal_docs import ingest_multimodal


@router.post(
    "/admin/upload",
    tags=["Administración RAG"],
    summary="Subir documento PDF o PPTX e indexar automáticamente",
    description="Recibe un archivo PDF o PPTX, lo almacena en ./data/docs/ y ejecuta la reindexación multimodal automática inmediata en ChromaDB (con interpretación visual de imágenes si el Vision-LLM está disponible)."
)
async def upload_document(
    file: UploadFile = File(..., description="Archivo PDF o PPTX institucional a incorporar")
):
    """
    Guarda el archivo subido y dispara la reindexación multimodal y recarga automática del vector store.
    Soporta archivos PDF (.pdf) y PowerPoint (.pptx).
    """
    allowed_extensions = (".pdf", ".pptx")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se admiten documentos en formato PDF (.pdf) o PowerPoint (.pptx)."
        )

    settings = get_settings()
    docs_dir = Path(settings.docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    target_path = docs_dir / file.filename

    # Guardar archivo en disco
    try:
        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)
        logger.info(f"Nuevo documento guardado en: {target_path} ({len(content) / 1024:.1f} KB)")
    except Exception as exc:
        logger.error(f"Error al escribir archivo en disco: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo guardar el archivo: {str(exc)}"
        )

    # Reindexar automáticamente con pipeline multimodal
    success = ingest_multimodal()
    if success:
        rag_service.reload_vector_store()
        return {
            "status": "success",
            "message": f"Documento '{file.filename}' subido e indexado exitosamente en ChromaDB (pipeline multimodal).",
            "filename": file.filename,
            "size_kb": round(len(content) / 1024, 2)
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El archivo se guardó, pero ocurrió un error durante la reindexación vectorial."
        )


@router.post(
    "/admin/reindex",
    tags=["Administración RAG"],
    summary="Forzar reindexación multimodal completa de documentos",
    description="Ejecuta la limpieza y reindexación multimodal de todos los PDFs y PPTX en ./data/docs/ con interpretación visual de imágenes y recarga ChromaDB en memoria."
)
async def trigger_reindex():
    """
    Dispara manualmente el pipeline de ingesta multimodal y actualiza la base vectorial activa.
    """
    success = ingest_multimodal()
    if success:
        rag_service.reload_vector_store()
        return {
            "status": "success",
            "message": "Base vectorial ChromaDB reindexada con pipeline multimodal y recargada exitosamente."
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar la reindexación multimodal de documentos."
        )


