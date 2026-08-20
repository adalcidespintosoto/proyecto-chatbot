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
    Datos de identificación del miembro de la comunidad USB.
    """
    name: Optional[str] = Field(default=None, description="Nombre completo del usuario", example="Alejandro Hernández")
    email: Optional[str] = Field(default=None, description="Correo electrónico institucional o personal", example="18-10000@usb.ve")
    usb_id: Optional[str] = Field(default=None, description="Carnet o identificación USB", example="18-10000")
    campus: Optional[str] = Field(default="Sartenejas", description="Sede universitaria (Sartenejas o Litoral)", example="Sartenejas")
    role: Optional[str] = Field(default="Estudiante", description="Rol en la USB (Estudiante, Profesor, Administrativo, Obrero)", example="Estudiante")


class ChatRequest(BaseModel):
    """
    Petición enviada al endpoint /api/chat.
    """
    message: str = Field(..., min_length=1, description="Mensaje o descripción del problema técnico enviado por el usuario", example="No puedo conectarme a eduroam desde mi laptop en el edificio MEM.")
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
            f"<b>REPORTE DE INCIDENTE TÉCNICO - ASISTENTE UNIMON USB</b><br><br>"
            f"<b>Usuario:</b> {user_display_name} ({user_role})<br>"
            f"<b>Carnet/ID:</b> {user_id}<br>"
            f"<b>Correo de Contacto:</b> {email_display}<br>"
            f"<b>Sede:</b> {user_campus}<br>"
            f"<b>Categoría Asignada:</b> {category_name}<br>"
            f"<b>Nivel de Urgencia Calculado:</b> {urgency}/5<br><br>"
            f"<b>Descripción del problema:</b><br>{user_msg}<br><br>"
            f"<i>Reporte generado automáticamente vía UniMon Backend.</i>"
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
                f"El equipo de soporte de la Dirección de Servicios Telemáticos / DTI ha sido notificado y atenderá su requerimiento a la brevedad."
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
    rag_result = await rag_service.query_llm(user_message=user_msg, user_name=user_info.name)

    return ChatResponse(
        intent=IntentType.RAG_QUERY.value,
        reply=rag_result["response"],
        ticket_details=None,
        category=category_name,
        source=rag_result.get("source", "ollama_rag")
    )
