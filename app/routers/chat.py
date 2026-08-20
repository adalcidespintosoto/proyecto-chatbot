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
    Datos opcionales de identificación del solicitante.
    """
    name: Optional[str] = Field(default=None, description="Nombre completo del usuario", example="Alejandro Hernández")
    email: Optional[str] = Field(default=None, description="Correo electrónico institucional o personal", example="usuario@unisimon.edu.co")


class ChatRequest(BaseModel):
    """
    Petición enviada al endpoint /api/chat.
    """
    session_id: Optional[str] = Field(default="default_session", description="Identificador único de la sesión conversacional del usuario", example="sess_12345")
    message: str = Field(..., min_length=1, description="Mensaje enviado por el usuario", example="El computador de la sala 2 no enciende.")
    user_data: Optional[UserData] = Field(default=None, description="Datos opcionales del usuario si ya fueron provistos")
    force_ticket: Optional[bool] = Field(default=False, description="Forzar la creación directa de un ticket en GLPI", example=False)


class TicketDetails(BaseModel):
    """
    Detalles estructurados del ticket registrado en GLPI.
    """
    ticket_id: int = Field(..., description="Identificador único del ticket generado en GLPI", example=1042)
    category: str = Field(..., description="Categoría de soporte asignada al incidente", example="Mantenimiento y Fallas de Cómputo (P-GT-01)")
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

from app.services.router_logic import ConversationState


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesar mensaje del usuario con máquina de estados conversacional",
    description="Gestiona consultas RAG o la captura conversacional paso a paso de datos para tickets en GLPI."
)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal para interacción con el Asistente Virtual UniMon.
    Maneja el flujo conversacional de tickets por sesión.
    """
    session_id = request.session_id or "default_session"
    user_msg = request.message.strip()
    session = RouterLogic.get_session(session_id)

    # 1. Si la sesión ya estaba en un estado intermedio de captura de ticket
    if session.state == ConversationState.AWAITING_DESCRIPTION:
        # El usuario está enviando la descripción de la falla
        session.description = user_msg
        cat_code, cat_name = RouterLogic.categorize_usb_incident(user_msg)
        urgency, impact = RouterLogic.calculate_urgency_and_impact(user_msg)
        session.category_name = cat_name
        session.urgency = urgency
        session.impact = impact

        # Verificar si en este mismo mensaje también incluyó email y/o nombre
        extracted_email = RouterLogic.extract_email(user_msg)
        extracted_name = RouterLogic.extract_name(user_msg, extracted_email)
        if extracted_email:
            session.email = extracted_email
        if extracted_name:
            session.name = extracted_name

        if session.name and session.email:
            # Tenemos todo listo para radicar
            return await _create_glpi_ticket_and_finish(session_id, session)
        else:
            session.state = ConversationState.AWAITING_CONTACT_INFO
            return ChatResponse(
                intent=IntentType.CREATE_TICKET.value,
                reply="Entendido. Para finalizar la radicación en GLPI, por favor indícame tu nombre completo y tu correo electrónico de contacto.",
                ticket_details=None,
                category=session.category_name,
                source="UniMon_Router",
                sources=None
            )

    elif session.state == ConversationState.AWAITING_CONTACT_INFO:
        # El usuario está respondiendo con sus datos de contacto
        extracted_email = RouterLogic.extract_email(user_msg)
        if extracted_email:
            session.email = extracted_email

        extracted_name = RouterLogic.extract_name(user_msg, extracted_email)
        if extracted_name:
            session.name = extracted_name

        # Si aún no tenemos el correo, insistir amablemente
        if not session.email:
            return ChatResponse(
                intent=IntentType.CREATE_TICKET.value,
                reply="Por favor asegúrate de incluir un correo electrónico válido (ej: nombre@unisimon.edu.co o tu correo personal) junto con tu nombre para registrarte como solicitante.",
                ticket_details=None,
                category=session.category_name,
                source="UniMon_Router",
                sources=None
            )

        if not session.name:
            # Si envió el correo pero no detectamos nombre, usar parte del correo o pedir nombre
            session.name = session.email.split("@")[0].capitalize()

        # Proceder con la radicación
        return await _create_glpi_ticket_and_finish(session_id, session)

    # 2. Estado IDLE: Analizar intención del nuevo mensaje
    intent = IntentType.CREATE_TICKET if request.force_ticket else RouterLogic.classify_intent(user_msg)

    # 2.1 Saludo puro y cortesía (Sin invocar RAG ni ChromaDB)
    if intent == IntentType.GREETING:
        greeting_reply = (
            "¡Hola! 👋 Soy **UniMon**, asistente de soporte técnico y gestión de TI de la Universidad Simón Bolívar. "
            "¿En qué te puedo colaborar hoy? Puedes consultarme sobre procedimientos institucionales (backups, cuentas, "
            "antimalware, Seven/Kactus) o indicarme si presentas alguna falla para radicar un ticket."
        )
        return ChatResponse(
            intent=IntentType.GREETING.value,
            reply=greeting_reply,
            ticket_details=None,
            category="Atención y Servicio al Usuario TI",
            source="UniMon_Assistant",
            sources=None
        )

    # 2.2 Creación de Ticket en GLPI
    if intent == IntentType.CREATE_TICKET:
        # Verificar si envió solo la solicitud genérica sin detalles (ej: "quiero abrir un ticket")
        if RouterLogic.is_only_ticket_request_without_details(user_msg):
            session.state = ConversationState.AWAITING_DESCRIPTION
            return ChatResponse(
                intent=IntentType.CREATE_TICKET.value,
                reply="¡Claro que sí! Para radicar tu caso ante soporte técnico, por favor descríbeme cuál es la falla o problema que presentas con tu equipo o servicio.",
                ticket_details=None,
                category="Soporte Técnico y Gestión de TI Unisimon",
                source="UniMon_Router",
                sources=None
            )

        # Si describió una falla, analizar categoría y extraer posibles datos de contacto
        session.description = user_msg
        cat_code, cat_name = RouterLogic.categorize_usb_incident(user_msg)
        urgency, impact = RouterLogic.calculate_urgency_and_impact(user_msg)
        session.category_name = cat_name
        session.urgency = urgency
        session.impact = impact

        # Verificar si vienen datos en request.user_data o embebidos en el mensaje
        if request.user_data and request.user_data.email and is_valid_email(request.user_data.email):
            session.email = request.user_data.email
            session.name = request.user_data.name or session.email.split("@")[0].capitalize()
        else:
            extracted_email = RouterLogic.extract_email(user_msg)
            extracted_name = RouterLogic.extract_name(user_msg, extracted_email)
            if extracted_email:
                session.email = extracted_email
            if extracted_name:
                session.name = extracted_name

        # Si tenemos los datos completos en un solo mensaje -> Radicación inmediata
        if session.name and session.email:
            return await _create_glpi_ticket_and_finish(session_id, session)
        else:
            session.state = ConversationState.AWAITING_CONTACT_INFO
            empathic_contact_request = (
                "Lamento el inconveniente con tu equipo. Para generar tu radicado oficial ante el equipo de soporte técnico, "
                "por favor facilítame tu nombre completo y tu correo electrónico de contacto."
            )
            return ChatResponse(
                intent=IntentType.CREATE_TICKET.value,
                reply=empathic_contact_request,
                ticket_details=None,
                category=session.category_name,
                source="UniMon_Router",
                sources=None
            )

    # 3. Flujo RAG_QUERY: Consulta de procedimientos o guías institucionales
    rag_result = await rag_service.query_rag(question=user_msg, user_name=session.name)
    cat_code, cat_name = RouterLogic.categorize_usb_incident(user_msg)


    return ChatResponse(
        intent=IntentType.RAG_QUERY.value,
        reply=rag_result["response"],
        ticket_details=None,
        category=cat_name,
        source=rag_result.get("source", "ollama_rag"),
        sources=rag_result.get("sources")
    )


async def _create_glpi_ticket_and_finish(session_id: str, session: SessionData) -> ChatResponse:
    """
    Función auxiliar para radicar el ticket en GLPI, asociar el usuario y limpiar la sesión.
    """
    ticket_title = RouterLogic.generate_ticket_title(session.description or "Falla técnica")
    ticket_content = (
        f"<b>REPORTE DE INCIDENTE TÉCNICO - ASISTENTE UNIMON</b><br><br>"
        f"<b>Solicitante:</b> {session.name}<br>"
        f"<b>Correo Electrónico:</b> {session.email}<br>"
        f"<b>Categoría:</b> {session.category_name}<br>"
        f"<b>Urgencia:</b> {session.urgency}/5<br><br>"
        f"<b>Descripción de la falla técnica:</b><br>{session.description}<br><br>"
        f"<i>Caso radicado automáticamente a través de UniMon Chatbot.</i>"
    )

    try:
        ticket_res = await glpi_service.create_ticket(
            name=ticket_title,
            content=ticket_content,
            urgency=session.urgency,
            impact=session.impact,
            requester_email=session.email
        )

        ticket_id = ticket_res["ticket_id"]
        confirmed_email = session.email
        category_name = session.category_name

        # Reset de la sesión
        RouterLogic.reset_session(session_id)

        reply_msg = (
            f"¡Tu caso ha sido radicado exitosamente en GLPI con el número **#{ticket_id}**! "
            f"Un técnico revisará tu requerimiento y te contactará a través de **{confirmed_email}**."
        )

        return ChatResponse(
            intent=IntentType.CREATE_TICKET.value,
            reply=reply_msg,
            ticket_details=TicketDetails(
                ticket_id=ticket_id,
                category=category_name or "Soporte Técnico General",
                urgency=session.urgency,
                impact=session.impact,
                status="success"
            ),
            category=category_name,
            source="GLPI_REST_API",
            sources=None
        )

    except GLPIException as exc:
        logger.error(f"Error al registrar ticket en GLPI: {exc}")
        RouterLogic.reset_session(session_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error en el servidor GLPI al crear el ticket: {str(exc)}"
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

