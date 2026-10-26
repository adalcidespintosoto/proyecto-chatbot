"""
Router para los endpoints de Chat y Soporte Técnico de UniMon (USB).
Define los esquemas de validación Pydantic y procesa las peticiones de los usuarios.
"""

import logging
import secrets
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request, UploadFile, File
from pydantic import BaseModel, Field

from app.security import require_admin_auth, require_admin_origin
from app.upload_security import save_upload, validated_filename
from app.services.router_logic import router_logic, RouterLogic, EstadoTicket, IntentType, is_prompt_injection_query
from app.services.glpi_service import glpi_client, GLPIService, GLPIException, is_valid_email
from app.services.rag_service import rag_service, RAGService

logger = logging.getLogger("unimon.chat_router")
MAX_CHAT_INPUT_CHARS = 12_000


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
    mensaje: Optional[str] = Field(default=None, max_length=MAX_CHAT_INPUT_CHARS, description="Mensaje o consulta enviada por el usuario; admite solicitudes extensas", example="No enciende el computador de la sala 2.")
    message: Optional[str] = Field(default=None, max_length=MAX_CHAT_INPUT_CHARS, description="Alias en inglés para el mensaje; admite solicitudes extensas", example="No enciende el computador de la sala 2.")
    session_id: Optional[str] = Field(default=None, max_length=128, description="Identificador único de la sesión conversacional", example="sess_12345")

    def get_texto(self) -> str:
        """Obtiene el texto del mensaje asegurando no vacíos."""
        return (self.mensaje or self.message or "").strip()


class ChatResponse(BaseModel):
    """
    Respuesta generada por UniMon según la máquina de estados de Nivel 1 y GLPI.
    """
    tipo: str = Field(..., description="Tipo de respuesta (SALUDO, DIAGNOSTICO, SOLUCIONADO, FINALIZADO, RADICANDO_TICKET, TICKET_CREADO, ERROR)", example="DIAGNOSTICO")
    mensaje: str = Field(..., description="Mensaje de respuesta en lenguaje natural para el usuario en español")
    ticket_id: Optional[Any] = Field(default=None, description="ID del ticket en GLPI si fue generado", example=1042)
    session_id: Optional[str] = Field(default=None, description="Identificador de la sesión para continuar la conversación")

    # Campos de compatibilidad para clientes web y quick replies
    intent: Optional[str] = Field(default=None, description="Alias de compatibilidad para tipo")
    reply: Optional[str] = Field(default=None, description="Alias de compatibilidad para mensaje")
    state: Optional[str] = Field(default=None, description="Estado de la sesión conversacional")
    response: Optional[str] = Field(default=None, description="Alias de respuesta")
    quick_replies: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Botones de respuesta rápida")
    ticket_details: Optional[Dict[str, Any]] = Field(default=None, description="Detalles del ticket si fue generado")
    category: Optional[str] = Field(default=None, description="Categoría temática del problema")
    source: Optional[str] = Field(default=None, description="Fuente de la respuesta (GLPI, Ollama, Base de Conocimiento)", example="GLPI_REST_API")
    sources: Optional[List[str]] = Field(default=None, description="Fuentes documentales consultadas en RAG", example=["P-GT-01_Mantenimiento.pdf"])
    routed_to: Optional[str] = Field(default=None, description="Identificador del asistente que atendió la consulta")
    routed_name: Optional[str] = Field(default=None, description="Nombre visible del asistente seleccionado")
    route_reason: Optional[str] = Field(default=None, description="Motivo breve de enrutamiento para trazabilidad")


# ==========================================
# Instancias de Servicios
# ==========================================

from app.services.router_logic import router_logic
from app.services.rag_service import rag_service


# ==========================================
# Rate Limiter & Sanitización
# ==========================================

import time
import re
from fastapi import Request
from app.services.telemetry_service import log_interaction, update_session_status
from app.services.llm_usage import begin_llm_usage_capture, finish_llm_usage_capture, get_route_usage


INJECTION_PATTERNS = [
    r"(?i)\bignora\s+(tus|las|todas\s+las)?\s*instrucciones\b",
    r"(?i)\bolvida\s+(tu|el)?\s*sistema\b",
    r"(?i)\bignore\s+(all\s+)?(previous\s+)?instructions\b",
    r"(?i)\bignore\s+your\s+system\s+prompt\b",
    r"(?i)\bact[uú]a\s+como\s+dan\b",
]


def get_client_ip(request: Optional[Request]) -> str:
    """Obtiene la IP del salto inmediato sin confiar en cabeceras enviadas por clientes."""
    if not request:
        return "127.0.0.1"
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"




def sanitize_input_text(text: str, neutralize_injections: bool = True) -> str:
    """Sanitiza el texto sin truncar cartas o descripciones extensas válidas."""
    clean = text[:MAX_CHAT_INPUT_CHARS].strip()
    # 2. Eliminar etiquetas HTML / script
    clean = re.sub(r'<[^>]*>', '', clean).strip()
    # 3. Neutralizar intentos de inyección de prompt en consultas normales.
    # Si el guardrail ya identificó una inyección, preservamos sus palabras clave
    # tras quitar HTML para que router_logic pueda rechazarla; de otro modo el
    # reemplazo aquí la ocultaba antes de que RAG la detectara.
    if neutralize_injections:
        for pat in INJECTION_PATTERNS:
            clean = re.sub(pat, "[consulta filtrada]", clean)
    return clean.strip()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesar mensaje del usuario con Chatbot de Nivel 1 y Router de Intención",
    description="Orquesta el diagnóstico proactivo de Nivel 1 con RAG (Llama 3.1) o la captura conversacional y radicación de tickets en GLPI."
)
async def process_chat(request: ChatRequest, raw_request: Request = None) -> ChatResponse:
    """
    Endpoint principal para interacción con el Asistente Virtual UniMon.
    Aplica limitación de tasa (25 req/min por IP), sanitización de entrada y registro de telemetría.
    """
    raw_texto = request.get_texto()
    if not raw_texto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El campo 'mensaje' no puede estar vacío."
        )

    session_id = request.session_id or f"sess_{secrets.token_urlsafe(24)}"
    if (not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id)
            or session_id.lower().startswith("wa_")
            or session_id == "default_session"):
        raise HTTPException(status_code=400, detail="Identificador de sesión inválido")


    # ChatRequest limita el tamaño máximo; sanitizar no debe recortar consultas normales.
    # Evaluar la señal de inyección antes de neutralizarla. Si se reemplaza primero,
    # "ignora todas las instrucciones" desaparece y llega al RAG como consulta normal.
    prompt_injection = is_prompt_injection_query(raw_texto)
    texto = sanitize_input_text(raw_texto, neutralize_injections=not prompt_injection)
    if not texto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje ingresado no contiene texto válido tras la sanitización."
        )

    logger.info("Procesando mensaje de chat (longitud: %d caracteres)", len(texto))

    # Medir tiempo de procesamiento (latencia)
    t0 = time.time()
    llm_usage_token = begin_llm_usage_capture()
    try:
        resultado = await router_logic.procesar_mensaje(mensaje=texto, session_id=session_id)
    finally:
        llm_usage = finish_llm_usage_capture(llm_usage_token)
    latency_ms = (time.time() - t0) * 1000
    route_usage = get_route_usage()

    tipo = resultado.get("tipo", "DIAGNOSTICO")
    state = resultado.get("state", tipo)
    mensaje_resp = resultado.get("mensaje", "")
    ticket_id = resultado.get("ticket_id")
    source = resultado.get("source", "UniMon")
    sources = resultado.get("sources") or []
    prompt_tokens = resultado.get("prompt_tokens", 0) or 0
    cached_tokens = resultado.get("cached_tokens", 0) or 0
    eval_tokens = resultado.get("eval_tokens", 0) or 0
    llm_calls = int(llm_usage.get("llm_calls", 0) or 0)
    usage_tracked = bool(llm_usage.get("complete", False))
    if llm_calls:
        # Incluye expansión MultiQuery, respuesta y posibles reintentos. El acumulador
        # es ContextVar, así que consultas simultáneas conservan contadores separados.
        prompt_tokens = llm_usage.get("prompt_tokens", 0) or 0
        cached_tokens = llm_usage.get("cached_tokens", 0) or 0
        eval_tokens = llm_usage.get("eval_tokens", 0) or 0
    else:
        # Una respuesta servida sin llamar al modelo no debe heredar contadores
        # colocados por otra ruta o una respuesta cacheada.
        prompt_tokens = cached_tokens = eval_tokens = 0
    prompt_tokens += int(route_usage.get("prompt_tokens", 0) or 0)
    cached_tokens += int(route_usage.get("cached_tokens", 0) or 0)
    eval_tokens += int(route_usage.get("eval_tokens", 0) or 0)
    llm_calls += int(route_usage.get("llm_calls", 0) or 0)
    usage_tracked = usage_tracked and bool(route_usage.get("complete", True))
    latency_ms += float(route_usage.get("latency_ms", 0) or 0)

    # Obtener rol del usuario registrado en la sesión
    session_obj = router_logic.get_session(session_id)
    user_role = getattr(session_obj, "user_role", "general") or "general"

    # Registrar telemetría de la interacción
    try:
        query_to_log = resultado.get("query") or texto
        if not query_to_log or query_to_log.strip().lower() in ("estudiante", "profesor", "docente", "administrativo", "otros", "otro"):
            if getattr(session_obj, "falla", None):
                query_to_log = session_obj.falla
            elif getattr(session_obj, "last_user_query", None):
                query_to_log = session_obj.last_user_query

        log_interaction(
            session_id=session_id,
            role=user_role,
            query=query_to_log,
            bot_response=mensaje_resp,
            intent=tipo,
            source=source,
            docs=sources,
            latency_ms=round(latency_ms, 2),
            prompt_tokens=prompt_tokens,
            cached_tokens=cached_tokens,
            eval_tokens=eval_tokens,
            feedback=resultado.get("feedback", "NONE"),
            golden_cache_used=resultado.get("golden_cache_used", False),
            golden_cache_similarity=resultado.get("golden_cache_similarity"),
            llm_calls=llm_calls,
            usage_tracked=usage_tracked,
        )

        # Actualizar estado de resolución / escalado
        if tipo in ["FINALIZADO", "SOLUCIONADO"] or state in ["FINALIZADO", "SOLUCIONADO"]:
            update_session_status(session_id, "FINALIZADO", escalated=False)
        elif tipo in ["TICKET_CREADO"] or ticket_id is not None:
            update_session_status(session_id, "TICKET_CREADO", escalated=True)
        elif tipo in ["RADICANDO_TICKET"] or state in ["RADICANDO_TICKET", "PIDIENDO_NOMBRE"]:
            update_session_status(session_id, "RADICANDO_TICKET", escalated=True)
        elif tipo in ["CANCELADO"] or state in ["CANCELADO"]:
            update_session_status(session_id, "CANCELADO", escalated=False)
    except Exception as e:
        logger.warning(f"Error al registrar telemetría: {e}")

    return ChatResponse(
        tipo=tipo,
        mensaje=mensaje_resp,
        ticket_id=ticket_id,
        session_id=session_id,
        intent=tipo,
        reply=mensaje_resp,
        state=state,
        response=mensaje_resp,
        quick_replies=resultado.get("quick_replies", []),
        ticket_details=resultado.get("ticket_details"),
        category=resultado.get("category"),
        source=source,
        sources=sources
    )





# ==========================================
# Asistentes adicionales por dependencia
# ==========================================

@router.get(
    "/chatbots/{bot_id}/config",
    summary="Obtener la configuración pública de un chatbot",
    description="Devuelve el nombre y el saludo de una instancia habilitada, sin exponer su configuración administrativa.",
)
async def get_chatbot_public_config(bot_id: str) -> Dict[str, Any]:
    from app.services.bot_instance_service import bot_instance_manager

    profile = bot_instance_manager.get(bot_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró este asistente.")
    return profile.public_config()


@router.post(
    "/chatbots/{bot_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar el asistente de una dependencia",
    description="Busca únicamente en el índice documental de la instancia indicada y responde con sus canales de atención configurados.",
)
async def process_chatbot_instance(bot_id: str, request: ChatRequest) -> ChatResponse:
    from app.services.bot_instance_service import BotInstanceError, bot_instance_manager

    profile = bot_instance_manager.get(bot_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró este asistente.")

    raw_text = request.get_texto()
    if not raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Escribe una consulta para continuar.")

    session_id = request.session_id or f"sess_{secrets.token_urlsafe(24)}"
    if (
        not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id)
        or session_id.lower().startswith("wa_")
        or session_id == "default_session"
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identificador de sesión inválido.")

    prompt_injection = is_prompt_injection_query(raw_text)
    question = sanitize_input_text(raw_text, neutralize_injections=not prompt_injection)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje no contiene texto válido después de la sanitización.",
        )

    started_at = time.perf_counter()
    llm_usage_token = begin_llm_usage_capture()
    try:
        runtime = bot_instance_manager.get_runtime(bot_id)
        result = await runtime.answer(profile, session_id, question)
    except BotInstanceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error al responder en la instancia '%s'", bot_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Este asistente no está disponible en este momento. Intenta de nuevo más tarde.",
        ) from exc
    finally:
        llm_usage = finish_llm_usage_capture(llm_usage_token)
    from app.services.llm_usage import get_route_usage
    route_usage = get_route_usage()
    latency_ms = (time.perf_counter() - started_at) * 1000 + float(route_usage.get("latency_ms", 0) or 0)
    prompt_tokens = int(llm_usage.get("prompt_tokens", 0) or 0) + int(route_usage.get("prompt_tokens", 0) or 0)
    cached_tokens = int(llm_usage.get("cached_tokens", 0) or 0) + int(route_usage.get("cached_tokens", 0) or 0)
    eval_tokens = int(llm_usage.get("eval_tokens", 0) or 0) + int(route_usage.get("eval_tokens", 0) or 0)
    llm_calls = int(llm_usage.get("llm_calls", 0) or 0) + int(route_usage.get("llm_calls", 0) or 0)
    usage_tracked = bool(llm_usage.get("complete", False)) and bool(route_usage.get("complete", True))

    logger.info(
        "Consulta atendida por instancia '%s' (chunks=%d, latencia_ms=%.0f, llm_calls=%d, tokens_in=%d, cached=%d, tokens_out=%d, usage_tracked=%s)",
        bot_id,
        int(result.get("retrieved_chunks") or 0),
        latency_ms,
        llm_calls,
        prompt_tokens,
        cached_tokens,
        eval_tokens,
        usage_tracked,
    )
    answer = result["response"]
    telemetry_session_id = f"bot_{bot_id}_{session_id}"
    feedback = result.get("feedback", "NONE")
    response_type = result.get("state") or "DIAGNOSTICO"
    try:
        log_interaction(
            session_id=telemetry_session_id,
            role=f"dependencia:{bot_id}",
            query=result.get("feedback_query") or question,
            bot_response=answer,
            intent=response_type,
            source=result.get("source") or f"CHATBOT_INSTANCE:{bot_id}",
            docs=result.get("sources") or [],
            latency_ms=round(latency_ms, 2),
            prompt_tokens=prompt_tokens,
            cached_tokens=cached_tokens,
            eval_tokens=eval_tokens,
            feedback=feedback,
            golden_cache_used=result.get("golden_cache_used", False),
            golden_cache_similarity=result.get("golden_cache_similarity"),
            llm_calls=llm_calls,
            usage_tracked=usage_tracked,
        )
        if response_type == "FINALIZADO":
            update_session_status(telemetry_session_id, "FINALIZADO", escalated=False)
    except Exception as exc:
        logger.warning("No se pudo registrar telemetría del chatbot '%s': %s", bot_id, type(exc).__name__)
    return ChatResponse(
        tipo=response_type,
        mensaje=answer,
        session_id=session_id,
        intent=response_type,
        reply=answer,
        state=response_type,
        response=answer,
        quick_replies=result.get("quick_replies", []),
        source=result.get("source") or f"{bot_id}_RAG",
        sources=result.get("sources") or [],
    )


@router.get(
    "/chatbot-router/config",
    summary="Obtener configuración pública del enrutador de dependencias",
)
async def get_chatbot_router_config() -> Dict[str, Any]:
    from app.services.bot_instance_service import bot_instance_manager

    active_count = len(bot_instance_manager.list())
    return {
        "display_name": "UniMon Asistente de Dependencias",
        "welcome_message": (
            "¡Hola! Soy UniMon. Cuéntame qué necesitas y te conectaré con el asistente "
            "de la dependencia que mejor pueda orientarte."
        ),
        "active_specialists": active_count,
    }


@router.post(
    "/chatbot-router/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Enrutar una consulta al chatbot especializado",
    description="Selecciona entre instancias activas por especialidad y deriva la consulta a su RAG aislado; usa UniMon como fallback.",
)
async def process_chatbot_router(request: ChatRequest, raw_request: Request = None) -> ChatResponse:
    from app.services.bot_router_service import select_chatbot
    from app.services.llm_usage import (
        begin_llm_usage_capture,
        finish_llm_usage_capture,
        set_route_usage,
        reset_route_usage,
    )

    raw_text = request.get_texto()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Escribe una consulta para continuar.")
    session_id = request.session_id or f"sess_{secrets.token_urlsafe(24)}"
    if (
        not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id)
        or session_id.lower().startswith("wa_")
        or session_id == "default_session"
    ):
        raise HTTPException(status_code=400, detail="Identificador de sesión inválido.")

    prompt_injection = is_prompt_injection_query(raw_text)
    question = sanitize_input_text(raw_text, neutralize_injections=not prompt_injection)
    if not question:
        raise HTTPException(status_code=400, detail="El mensaje no contiene texto válido después de la sanitización.")

    route_started = time.perf_counter()
    route_usage_token = begin_llm_usage_capture()
    try:
        if prompt_injection:
            target = {"bot_id": "unimon", "display_name": "UniMon", "reason": "Consulta canalizada al asistente principal."}
        else:
            target = await select_chatbot(question, session_id)
    finally:
        classification_usage = finish_llm_usage_capture(route_usage_token)
    classification_usage["latency_ms"] = (time.perf_counter() - route_started) * 1000
    route_token = set_route_usage(classification_usage)
    try:
        delegated_request = ChatRequest(mensaje=question, session_id=session_id)
        if target["bot_id"] == "unimon":
            response = await process_chat(delegated_request, raw_request)
        else:
            response = await process_chatbot_instance(target["bot_id"], delegated_request)
        response.routed_to = target["bot_id"]
        response.routed_name = target["display_name"]
        response.route_reason = target["reason"]
        return response
    finally:
        reset_route_usage(route_token)


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
    dependencies=[Depends(require_admin_auth), Depends(require_admin_origin)],
    summary="Subir documento PDF o PPTX, sanearlo a Markdown e indexarlo",
    description="Recibe PDF/PPTX, conserva el original en data/docs, genera Markdown validado con GPT-6 Luna y usa únicamente ese Markdown como contenido vectorial."
)
async def upload_document(
    file: UploadFile = File(..., description="Archivo PDF o PPTX institucional a incorporar")
):
    """
    Guarda el original, lo transforma a Markdown validado y recarga el vector store al terminar.
    Soporta archivos PDF (.pdf) y PowerPoint (.pptx).
    """
    filename = validated_filename(file.filename, {".pdf", ".pptx"})

    settings = get_settings()
    docs_dir = Path(settings.docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    target_path = docs_dir / filename

    # Guardar archivo en disco validando tamaño máximo
    try:
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        file_size = await save_upload(file, target_path, max_bytes)
        logger.info(f"Nuevo documento guardado en: {target_path} ({file_size / 1024:.1f} KB)")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error al escribir archivo en disco: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo guardar el archivo"
        )

    # Indexar únicamente el nuevo archivo con pipeline multimodal incremental
    success = ingest_multimodal(file_path=str(target_path))
    if success:
        rag_service.reload_vector_store()
        return {
            "status": "success",
            "message": f"Documento '{file.filename}' subido, transformado a Markdown e indexado en ChromaDB.",
            "filename": file.filename,
            "size_kb": round(file_size / 1024, 2)
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El archivo se guardó, pero ocurrió un error durante la indexación vectorial."
        )


@router.post(
    "/admin/reindex",
    tags=["Administración RAG"],
    dependencies=[Depends(require_admin_auth), Depends(require_admin_origin)],
    summary="Indexar documentos PDF/PPTX nuevos o modificados",
    description="Busca fuentes nuevas o modificadas, genera Markdown validado y las indexa sin borrar la base activa. La reconstrucción desde cero se ejecuta con el servidor detenido."
)
async def trigger_reindex():
    """
    Busca e indexa incrementalmente solo documentos nuevos o modificados.
    """
    success = ingest_multimodal(incremental=True)
    if success:
        rag_service.reload_vector_store()
        return {
            "status": "success",
            "message": "Documentos nuevos o modificados transformados a Markdown e indexados; ChromaDB fue recargado."
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se completó la ingesta Markdown. Revisa el log; si el RAG conserva fuentes crudas, detén UniMon y ejecuta la reconstrucción indicada en la guía."
        )


