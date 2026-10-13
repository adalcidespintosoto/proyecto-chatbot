"""
Router de Webhook y Diagnóstico para WhatsApp Cloud API (Meta) en UniMon.
Procesa el handshake de validación de Meta (GET) y los eventos entrantes de mensajería (POST).
"""

import hashlib
import hmac
import json
import logging
import re
from typing import Optional
from fastapi import APIRouter, Query, Response, status, BackgroundTasks, Request, Header, HTTPException, Depends

from app.config import get_settings
from app.security import require_admin_auth
from app.services.whatsapp_service import whatsapp_service

logger = logging.getLogger("unimon.whatsapp_router")

router = APIRouter(
    prefix="/api/whatsapp",
    tags=["WhatsApp Cloud API (Meta)"]
)


@router.get(
    "",
    summary="Verificación del Webhook de WhatsApp (Meta Handshake)",
    description="Endpoint que invoca Meta con hub.mode, hub.verify_token y hub.challenge para validar la URL pública.",
    response_class=Response
)
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """
    Maneja la verificación del webhook de Meta.
    Meta envía una petición GET para validar que el servidor responde con el desafío correcto.
    """
    valid, challenge = whatsapp_service.verify_webhook_token(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge
    )

    if valid and challenge is not None:
        # Meta exige que el challenge se retorne como texto plano con HTTP 200
        return Response(content=str(challenge), media_type="text/plain", status_code=status.HTTP_200_OK)

    return Response(
        content="Verificación fallida: Token inválido o parámetros incorrectos.",
        media_type="text/plain",
        status_code=status.HTTP_403_FORBIDDEN
    )


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Recepción de Mensajes y Eventos de WhatsApp",
    description="Endpoint donde Meta envía en tiempo real los mensajes que escriben los estudiantes, profesores y funcionarios."
)
async def receive_webhook(
    background_tasks: BackgroundTasks,
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Recibe los mensajes de WhatsApp en tiempo real.
    Responde HTTP 200 inmediatamente a Meta en <100ms y delega el procesamiento RAG
    en una tarea de fondo (BackgroundTasks) para evitar reintentos por latencia de red.
    """
    settings = get_settings()

    if not whatsapp_service.is_configured():
        logger.error("Webhook de WhatsApp deshabilitado: configuración incompleta")
        raise HTTPException(status_code=503, detail="Webhook no configurado")

    if not x_hub_signature_256 or not re.fullmatch(r"sha256=[0-9a-f]{64}", x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Firma inválida")

    # Verificar la firma del cuerpo original antes de interpretar el JSON.
    body = bytearray()
    async for part in request.stream():
        body.extend(part)
        if len(body) > 1024 * 1024:
            raise HTTPException(status_code=413, detail="Evento demasiado grande")
    expected_signature = "sha256=" + hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        logger.warning("Firma de Meta inválida")
        raise HTTPException(status_code=403, detail="Firma inválida")

    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="JSON inválido") from None
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Evento inválido")

    # Despachar procesamiento en segundo plano para respuesta ultra rápida a Meta
    background_tasks.add_task(whatsapp_service.process_incoming_webhook_payload, payload)

    # Meta exige HTTP 200 con { "status": "EVENT_RECEIVED" } para no reintentar
    return {"status": "EVENT_RECEIVED"}


@router.get(
    "/status",
    dependencies=[Depends(require_admin_auth)],
    summary="Estado de la Integración con WhatsApp",
    description="Permite verificar si las credenciales y el webhook están listos para operar."
)
async def whatsapp_status():
    """
    Retorna el estado de configuración del canal WhatsApp en el backend.
    """
    settings = get_settings()
    configured = whatsapp_service.is_configured()

    # Enmascarar IDs para visualización segura
    phone_id_preview = (
        f"***{settings.whatsapp_phone_number_id[-4:]}"
        if len(settings.whatsapp_phone_number_id) >= 4
        else "No configurado"
    )

    token_preview = "Configurado" if settings.whatsapp_access_token else "No configurado"

    return {
        "whatsapp_channel_enabled": settings.whatsapp_enabled,
        "is_ready_for_production": configured,
        "phone_number_id": phone_id_preview,
        "waba_id_configured": bool(settings.whatsapp_waba_id),
        "access_token_status": token_preview,
        "verify_token_configured": bool(settings.whatsapp_verify_token and settings.whatsapp_verify_token != "UniMon_USB_Verify_Token_2026"),
        "app_secret_configured": bool(settings.whatsapp_app_secret),
        "api_version": settings.whatsapp_api_version,
        "instructions": (
            "✅ Listo para operar."
            if configured
            else "Pendiente: configura las credenciales de WhatsApp, el token de verificación y WHATSAPP_APP_SECRET en .env."
        )
    }
