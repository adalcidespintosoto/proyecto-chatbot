"""
Router para los endpoints de Chat y Soporte Técnico de UniMon (USB).
Define los esquemas de validación Pydantic y procesa las peticiones de los usuarios.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.router_logic import RouterLogic, IntentType
from app.services.glpi_service import GLPIService, GLPIException, is_valid_email
from app.services.rag_service import RAGService

logger = logging.getLogger("unimon.chat_router")

router = APIRouter(
    prefix="/api",
    tags=["Chat & Soporte UniMon"]
)


# ==========================================
# Esquemas Pydantic para el Endpoint de Chat
# ==========================================

class UserData(BaseModel):
    """
    Datos de identificación del miembro de la comunidad universitaria Unisimon.
    """
    name: Optional[str] = Field(default=None, description="Nombre completo del usuario", example="Alejandro Hernández")
    email: Optional[str] = Field(default=None, description="Correo electrónico institucional o personal", example="usuario@unisimon.edu.co")
    usb_id: Optional[str] = Field(default=None, description="Identificación o código institucional", example="1042500000")
    campus: Optional[str] = Field(default="Barranquilla", description="Sede universitaria (Barranquilla o Cúcuta)", example="Barranquilla")
    role: Optional[str] = Field(default="Estudiante", description="Rol (Estudiante, Docente, Funcionario / Administrativo)", example="Estudiante")


class ChatRequest(BaseModel):
    """
    Petición enviada al endpoint /api/chat.
    """
    message: str = Field(..., min_length=1, description="Mensaje o descripción del problema técnico enviado por el usuario", example="El computador del laboratorio 204 en la sede Barranquilla no enciende y presenta pantalla negra.")
    user_data: Optional[UserData] = Field(default=None, description="Información del usuario solicitante")
    force_ticket: Optional[bool] = Field(default=False, description="Forzar la creación directa de un ticket en GLPI sin pasar por consulta informativa", example=False)


class TicketDetails(BaseModel):
    """
    Detalles estructurados del ticket registrado en GLPI.
    """
    ticket_id: int = Field(..., description="Identificador único del ticket generado en GLPI", example=1042)
    category: str = Field(..., description="Categoría de soporte asignada al incidente", example="Red WiFi USB / Eduroam / Conectividad")
    urgency: int = Field(..., ge=1, le=5, description="Nivel de urgencia institucional (1 a 5)", example=4)
    impact: int = Field(..., ge=1, le=5, description="Nivel de impacto del problema (1 a 5)", example=3)
    status: str = Field(default="success", description="Estado del registro en GLPI", example="success")
    tracking_url: Optional[str] = Field(default=None, description="Enlace opcional para seguimiento institucional")


class ChatResponse(BaseModel):
    """
    Respuesta enriquecida devuelta por UniMon.
    """
    intent: str = Field(..., description="Intención detectada: CREATE_TICKET o RAG_QUERY", example="CREATE_TICKET")
    reply: str = Field(..., description="Mensaje de respuesta en lenguaje natural para el usuario en español")
    ticket_details: Optional[TicketDetails] = Field(default=None, description="Detalles del ticket si fue generado")
    category: Optional[str] = Field(default=None, description="Categoría temática del problema")
    source: Optional[str] = Field(default=None, description="Fuente de la respuesta (GLPI, Ollama, Base de Conocimiento)", example="GLPI_REST_API")
    sources: Optional[List[str]] = Field(default=None, description="Fuentes documentales consultadas en RAG", example=["Guia_WiFi_Eduroam.pdf"])


# ==========================================
# Instancias de Servicios
# ==========================================

glpi_service = GLPIService()
rag_service = RAGService()


# ==========================================
# Endpoint Principal: POST /api/chat
# ==========================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesar mensaje del usuario y orquestar soporte USB",
    description="Analiza la intención del mensaje, consulta la base de conocimientos RAG institucional vía Ollama o genera automáticamente un ticket de soporte en GLPI con cálculo de urgencia."
)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal para interacción con el Asistente Virtual UniMon.
    """
    user_msg = request.message.strip()
    user_info = request.user_data or UserData()

    # 1. Análisis de intención, categoría y urgencia
    analysis = RouterLogic.analyze_message(user_msg)
    detected_intent = IntentType.CREATE_TICKET if request.force_ticket else analysis["intent"]
    category_name = analysis["category_name"]
    urgency = analysis["urgency"]
    impact = analysis["impact"]

    logger.info(f"Procesando mensaje. Intención: {detected_intent}, Categoría: {category_name}, Urgencia: {urgency}")

    # 2. Flujo de creación de Ticket en GLPI (CREATE_TICKET)
    if detected_intent == IntentType.CREATE_TICKET:
        user_display_name = user_info.name or "Usuario Anónimo USB"
        raw_email = user_info.email.strip() if user_info.email else ""
        user_email = raw_email if (raw_email and is_valid_email(raw_email)) else None
        email_display = raw_email if raw_email else "Sin correo especificado"
        user_id = user_info.usb_id or "Sin carnet"
        user_campus = user_info.campus or "Sartenejas"
        user_role = user_info.role or "Comunidad USB"

        # Construir asunto y contenido formal para el ticket en GLPI
        ticket_subject = f"[{category_name}] Reporte: {user_msg[:60]}..." if len(user_msg) > 60 else f"[{category_name}] Reporte: {user_msg}"
        ticket_content = (
            f"<b>REPORTE DE INCIDENTE TÉCNICO - ASISTENTE UNIMON (UNISIMON COLOMBIA)</b><br><br>"
            f"<b>Usuario:</b> {user_display_name} ({user_role})<br>"
            f"<b>ID / Código:</b> {user_id}<br>"
            f"<b>Correo de Contacto:</b> {email_display}<br>"
            f"<b>Sede:</b> {user_campus}<br>"
            f"<b>Categoría Asignada:</b> {category_name}<br>"
            f"<b>Nivel de Urgencia Calculado:</b> {urgency}/5<br><br>"
            f"<b>Descripción del problema:</b><br>{user_msg}<br><br>"
            f"<i>Reporte generado automáticamente vía UniMon Backend (Unisimon TI).</i>"
        )

        try:
            ticket_res = await glpi_service.create_ticket(
                name=ticket_subject,
                content=ticket_content,
                urgency=urgency,
                impact=impact,
                requester_email=user_email
            )

            ticket_id = ticket_res["ticket_id"]
            reply_msg = (
                f"Estimado/a {user_display_name}, he generado exitosamente su solicitud de soporte técnico.\n\n"
                f"📌 **Número de Ticket GLPI:** #{ticket_id}\n"
                f"🏷️ **Categoría:** {category_name}\n"
                f"⚡ **Nivel de Urgencia:** {urgency}/5\n"
                f"📍 **Sede:** {user_campus}\n\n"
                f"El equipo de Soporte y Gestión de TI de la Universidad Simón Bolívar ({user_campus}) ha recibido su caso y procederá con la atención requerida."
            )

            return ChatResponse(
                intent=IntentType.CREATE_TICKET.value,
                reply=reply_msg,
                ticket_details=TicketDetails(
                    ticket_id=ticket_id,
                    category=category_name,
                    urgency=urgency,
                    impact=impact,
                    status="success"
                ),
                category=category_name,
                source="GLPI_REST_API"
            )

        except GLPIException as exc:
            logger.error(f"Error al registrar ticket en GLPI: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error en el servidor GLPI al crear el ticket: {str(exc)}"
            )

    # 3. Flujo de Consulta Informativa RAG (RAG_QUERY)
    rag_result = await rag_service.query_rag(question=user_msg, user_name=user_info.name)

    return ChatResponse(
        intent=IntentType.RAG_QUERY.value,
        reply=rag_result["response"],
        ticket_details=None,
        category=category_name,
        source=rag_result.get("source", "ollama_rag"),
        sources=rag_result.get("sources")
    )


# ==========================================
# Endpoints de Administración de Documentos RAG
# ==========================================

from fastapi import UploadFile, File
from pathlib import Path
from app.config import get_settings
from scripts.ingest_docs import ingest_documents


@router.post(
    "/admin/upload",
    tags=["Administración RAG"],
    summary="Subir documento PDF e indexar automáticamente",
    description="Recibe un archivo PDF, lo almacena en ./data/docs/ y ejecuta la reindexación automática inmediata en ChromaDB."
)
async def upload_document(
    file: UploadFile = File(..., description="Archivo PDF institucional a incorporar")
):
    """
    Guarda el archivo PDF subido y dispara la reindexación y recarga automática del vector store.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se admiten documentos en formato PDF (.pdf)."
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

    # Reindexar automáticamente
    success = ingest_documents()
    if success:
        rag_service.reload_vector_store()
        return {
            "status": "success",
            "message": f"Documento '{file.filename}' subido e indexado exitosamente en ChromaDB.",
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
    summary="Forzar reindexación completa de documentos",
    description="Ejecuta la limpieza y reindexación de todos los PDFs en ./data/docs/ y recarga ChromaDB en memoria."
)
async def trigger_reindex():
    """
    Dispara manualmente el pipeline de ingestión y actualiza la base vectorial activa.
    """
    success = ingest_documents()
    if success:
        rag_service.reload_vector_store()
        return {
            "status": "success",
            "message": "Base vectorial ChromaDB reindexada y recargada exitosamente."
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar la reindexación de documentos."
        )

