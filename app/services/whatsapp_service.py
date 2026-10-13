"""
Servicio de Integración Oficial con WhatsApp Cloud API (Meta for Developers) para UniMon.
Gestiona la recepción de webhooks, deduplicación de mensajes, conversión de Markdown a formato WhatsApp,
mensajes interactivos con botones de respuesta rápida y envío mediante Meta Graph API.
"""

import logging
import re
import time
import unicodedata
from typing import Dict, Any, Optional, List, Tuple
import httpx

from app.config import get_settings
from app.services.router_logic import router_logic
from app.services.telemetry_service import log_interaction, update_session_status

logger = logging.getLogger("unimon.whatsapp_service")


def is_new_session_command(text: str) -> bool:
    """Reconoce comandos explícitos para reiniciar el contexto de WhatsApp."""
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9\s/]", " ", normalized.casefold())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized in {
        "new chat", "new_chat", "nuevo chat", "nueva conversacion", "nueva sesion",
        "empezar de nuevo", "empezar otra vez", "reiniciar chat",
        "reiniciar conversacion", "reiniciar sesion", "/nuevo",
    }


def split_whatsapp_follow_up(text: str) -> Tuple[str, str]:
    """Separa pasos de diagnóstico del bloque posterior de escalamiento."""
    match = re.search(r"\n\s*---+\s*\n", text or "")
    if not match:
        return (text or "").strip(), ""
    return text[:match.start()].strip(), text[match.end():].strip()


def markdown_to_whatsapp(text: str) -> str:
    """
    Convierte formato Markdown estándar a formato nativo de WhatsApp:
    - **negrita** -> *negrita*
    - __cursiva__ o *cursiva* -> _cursiva_
    - [Texto](URL) -> Texto: URL
    - `código` -> ```código``` o `código`
    - Preserva viñetas y listas
    """
    if not text:
        return ""

    formatted = re.sub(r"\r\n?", "\n", text or "").strip()

    # 1. Convertir enlaces en Markdown [Texto](URL) a "Texto (URL)"
    formatted = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\1 (\2)', formatted)

    # 2. Convertir títulos Markdown ### o ## a *TÍTULO*
    formatted = re.sub(r'(?m)^#{1,4}\s*(.+)$', r'*\1*', formatted)

    # 3. Convertir **negrita** a *negrita* de WhatsApp
    formatted = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', formatted)

    # 4. Convertir líneas divisorias --- a una línea limpia
    formatted = re.sub(r'(?m)^---+$', '────────────────────', formatted)

    # Normaliza el espaciado para que los mensajes largos se lean bien en móvil.
    formatted = re.sub(r"[ \t]+\n", "\n", formatted)
    formatted = re.sub(r"\n{3,}", "\n\n", formatted)

    return formatted.strip()


class WhatsAppService:
    """
    Cliente y orquestador para la plataforma WhatsApp Cloud API de Meta.
    """

    def __init__(self):
        # Caché en memoria para deduplicación de mensajes recibidos (TTL 10 minutos)
        # Formato: { "message_id": timestamp }
        self._processed_messages: Dict[str, float] = {}
        self._max_cache_size = 2000

    def _cleanup_dedup_cache(self):
        """Elimina mensajes con más de 10 minutos de antigüedad en la caché de deduplicación."""
        now = time.time()
        expired = [msg_id for msg_id, ts in self._processed_messages.items() if now - ts > 600]
        for msg_id in expired:
            del self._processed_messages[msg_id]

    def is_message_duplicate(self, message_id: str) -> bool:
        """Verifica si el mensaje ya fue recibido y procesado previamente por Meta."""
        if not message_id:
            return False
        self._cleanup_dedup_cache()
        if message_id in self._processed_messages:
            return True
        if len(self._processed_messages) >= self._max_cache_size:
            oldest = min(self._processed_messages, key=self._processed_messages.get)
            del self._processed_messages[oldest]
        self._processed_messages[message_id] = time.time()
        return False

    def is_configured(self) -> bool:
        """Verifica si las credenciales de WhatsApp Cloud API están presentes en la configuración."""
        settings = get_settings()
        return bool(
            settings.whatsapp_enabled
            and settings.whatsapp_phone_number_id
            and not settings.whatsapp_phone_number_id.startswith("tu_")
            and settings.whatsapp_access_token
            and not settings.whatsapp_access_token.startswith("tu_")
            and settings.whatsapp_app_secret
            and settings.whatsapp_verify_token
            and settings.whatsapp_verify_token != "UniMon_USB_Verify_Token_2026"
        )

    def verify_webhook_token(self, mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Valida el apretón de manos (handshake) que realiza Meta al configurar el Webhook.
        Retorna (es_valido, challenge_a_responder).
        """
        settings = get_settings()
        expected_token = settings.whatsapp_verify_token

        import hmac
        if (settings.whatsapp_enabled and mode == "subscribe" and challenge is not None
                and token and expected_token
                and expected_token != "UniMon_USB_Verify_Token_2026"
                and hmac.compare_digest(token, expected_token)):
            logger.info("✅ Handshake de Webhook de WhatsApp validado exitosamente con Meta.")
            return True, challenge
        else:
            logger.warning("Intento de verificación de Webhook fallido")
            return False, None

    async def mark_message_as_read(self, message_id: str) -> bool:
        """
        Envía a Meta el estado 'read' para activar el doble check azul al usuario inmediatamente.
        """
        if not self.is_configured():
            return False

        settings = get_settings()
        url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                return resp.status_code == 200
        except Exception as exc:
            logger.debug(f"Aviso al marcar mensaje como leído en WhatsApp: {exc}")
            return False

    async def send_text_message(self, to_phone: str, text: str) -> bool:
        """
        Envía un mensaje de texto plano con formato WhatsApp mediante Meta Graph API.
        Si el texto supera 4000 caracteres, lo divide en fragmentos respetando oraciones.
        """
        if not self.is_configured():
            logger.warning("[WhatsApp] No se puede enviar mensaje: Credenciales no configuradas aún en .env")
            return False

        settings = get_settings()
        url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json"
        }

        formatted_text = markdown_to_whatsapp(text)

        # Dividir si excede el límite de WhatsApp (4096 caracteres)
        MAX_CHUNK = 3800
        chunks = [formatted_text[i:i + MAX_CHUNK] for i in range(0, len(formatted_text), MAX_CHUNK)] if len(formatted_text) > MAX_CHUNK else [formatted_text]

        success = True
        for chunk in chunks:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_phone,
                "type": "text",
                "text": {
                    "preview_url": True,
                    "body": chunk
                }
            }

            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code in [200, 201]:
                        logger.info("[WhatsApp] Mensaje enviado exitosamente")
                    else:
                        logger.error("[WhatsApp] Error HTTP %s al enviar mensaje", resp.status_code)
                        success = False
            except Exception as exc:
                logger.error("[WhatsApp] Falló la conexión al enviar mensaje: %s", type(exc).__name__)
                success = False

        return success

    async def send_interactive_buttons_message(self, to_phone: str, body_text: str, quick_replies: List[Dict[str, str]]) -> bool:
        """
        Envía un mensaje con botones interactivos nativos de WhatsApp (hasta 3 botones).
        Si hay más de 3 botones o los títulos exceden 20 caracteres, envía como texto enriquecido.
        """
        if not self.is_configured():
            logger.warning("[WhatsApp] Credenciales no configuradas.")
            return False

        # Validación de límites de Meta para botones interactivos:
        # - Máximo 3 botones
        # - Título del botón máximo 20 caracteres
        can_use_buttons = (
            1 <= len(quick_replies) <= 3
            and all(len(qr.get("label", "")) <= 20 for qr in quick_replies)
        )

        if not can_use_buttons:
            # Fallback elegante a texto con viñetas numeradas
            options_text = "\n\n*Opciones rápidas:*\n"
            for qr in quick_replies:
                options_text += f"• {qr.get('label', '')}\n"
            return await self.send_text_message(to_phone, body_text + options_text)

        settings = get_settings()
        url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json"
        }

        buttons = []
        for idx, qr in enumerate(quick_replies):
            payload_id = qr.get("payload") or qr.get("label") or f"BTN_{idx}"
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": payload_id[:256],
                    "title": qr.get("label", f"Opción {idx+1}")[:20]
                }
            })

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": markdown_to_whatsapp(body_text)[:1024]
                },
                "action": {
                    "buttons": buttons
                }
            }
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    logger.info("[WhatsApp] Mensaje interactivo enviado")
                    return True
                else:
                    logger.warning("[WhatsApp] Meta rechazó mensaje interactivo (%s); reintentando como texto", resp.status_code)
                    # Reintento con texto plano si Meta rechaza el interactivo
                    return await self.send_text_message(to_phone, body_text)
        except Exception as exc:
            logger.error("[WhatsApp] Error enviando interactivo: %s", type(exc).__name__)
            return await self.send_text_message(to_phone, body_text)

    async def process_incoming_webhook_payload(self, payload: Dict[str, Any]) -> None:
        """
        Procesa el payload JSON enviado por Meta cuando un usuario escribe al número de WhatsApp.
        Extrae el remitente, mensaje, invoca a UniMon (RAG + Router + GLPI) y envía la respuesta.
        """
        try:
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})

                    # Si es solo una actualización de estado (delivered, read, sent), ignorar
                    if "statuses" in value and "messages" not in value:
                        logger.debug("[WhatsApp Webhook] Notificación de estado de entrega recibida.")
                        continue

                    messages = value.get("messages", [])
                    if not messages:
                        continue

                    for msg in messages:
                        msg_id = msg.get("id")
                        from_phone = msg.get("from")  # ej. "573001234567"
                        msg_type = msg.get("type")

                        if not msg_id or not from_phone:
                            continue

                        # 1. Deduplicación estricta de mensajes de Meta
                        if self.is_message_duplicate(msg_id):
                            logger.info("[WhatsApp] Mensaje duplicado ignorado")
                            continue

                        # 2. Marcar como leído en segundo plano
                        await self.mark_message_as_read(msg_id)

                        # 3. Extraer el texto según el tipo de mensaje recibido
                        incoming_text = ""
                        if msg_type == "text":
                            incoming_text = msg.get("text", {}).get("body", "").strip()
                        elif msg_type == "interactive":
                            interactive = msg.get("interactive", {})
                            btn_reply = interactive.get("button_reply", {})
                            list_reply = interactive.get("list_reply", {})
                            incoming_text = btn_reply.get("id") or btn_reply.get("title") or list_reply.get("id") or list_reply.get("title") or ""
                        elif msg_type == "button":
                            incoming_text = msg.get("button", {}).get("text", "").strip()
                        else:
                            # Otros tipos de mensaje (audio, imagen, sticker, ubicación)
                            logger.info("[WhatsApp] Tipo de mensaje recibido: %s", msg_type)
                            incoming_text = "[Archivo/Adjunto enviado por el usuario]"

                        if not incoming_text:
                            continue

                        logger.info("[WhatsApp] Mensaje entrante recibido (%d caracteres)", len(incoming_text))

                        # 4. Identificador de sesión persistente vinculado al número de teléfono
                        session_id = f"wa_{from_phone}"

                        if is_new_session_command(incoming_text):
                            router_logic.reset_session(session_id, preserve_role=False)
                            await self.send_text_message(
                                from_phone,
                                "🔄 *Conversación nueva*\n\nListo, limpié el contexto anterior. "
                                "Cuéntame qué necesitas resolver y empezamos desde cero."
                            )
                            logger.info("[WhatsApp] Conversación reiniciada")
                            continue

                        # 5. Invocar el pipeline inteligente de UniMon
                        t0 = time.time()
                        resultado = await router_logic.procesar_mensaje(
                            mensaje=incoming_text,
                            session_id=session_id
                        )
                        latency_ms = (time.time() - t0) * 1000

                        mensaje_resp = resultado.get("mensaje", "")
                        quick_replies = resultado.get("quick_replies") or []
                        # Reserva un botón corto para reiniciar desde cualquier flujo
                        # que aún tenga espacio dentro del límite de WhatsApp.
                        quick_replies = list(quick_replies)
                        if quick_replies and len(quick_replies) < 3 and not any(
                            (item.get("payload") or "").upper() == "NEW_CHAT" for item in quick_replies
                        ):
                            quick_replies.append({"label": "🔄 Nuevo chat", "payload": "NEW_CHAT"})
                        tipo = resultado.get("tipo", "DIAGNOSTICO")
                        ticket_id = resultado.get("ticket_id")

                        # 6. Registrar telemetría
                        try:
                            session_obj = router_logic.get_session(session_id)
                            user_role = getattr(session_obj, "user_role", "general") or "general"
                            log_interaction(
                                session_id=session_id,
                                role=user_role,
                                query=incoming_text,
                                bot_response=mensaje_resp,
                                intent=tipo,
                                source=resultado.get("source", "UniMon_WhatsApp"),
                                docs=resultado.get("sources") or [],
                                latency_ms=round(latency_ms, 2),
                                prompt_tokens=resultado.get("prompt_tokens", 0) or 0,
                                cached_tokens=resultado.get("cached_tokens", 0) or 0,
                                eval_tokens=resultado.get("eval_tokens", 0) or 0,
                                feedback=resultado.get("feedback", "NONE"),
                                golden_cache_used=resultado.get("golden_cache_used", False),
                                golden_cache_similarity=resultado.get("golden_cache_similarity"),
                            )
                        except Exception as tel_err:
                            logger.debug(f"Aviso en telemetría de WhatsApp: {tel_err}")

                        # 7. Despachar la respuesta de vuelta a WhatsApp
                        if quick_replies and len(quick_replies) <= 3 and all(
                            len(item.get("label", "")) <= 20 for item in quick_replies
                        ):
                            diagnostic_text, follow_up_text = split_whatsapp_follow_up(mensaje_resp)
                            if follow_up_text:
                                await self.send_text_message(from_phone, diagnostic_text)
                                await self.send_interactive_buttons_message(
                                    to_phone=from_phone,
                                    body_text=follow_up_text[:1024],
                                    quick_replies=quick_replies,
                                )
                            elif len(markdown_to_whatsapp(mensaje_resp)) > 1024:
                                await self.send_text_message(from_phone, mensaje_resp)
                                await self.send_interactive_buttons_message(
                                    to_phone=from_phone,
                                    body_text="¿Qué te gustaría hacer ahora?",
                                    quick_replies=quick_replies,
                                )
                            else:
                                await self.send_interactive_buttons_message(
                                    to_phone=from_phone,
                                    body_text=mensaje_resp,
                                    quick_replies=quick_replies
                                )
                        else:
                            await self.send_text_message(
                                to_phone=from_phone,
                                text=mensaje_resp
                            )

        except Exception as exc:
            logger.error(f"[WhatsApp] Error crítico procesando webhook entrante: {exc}", exc_info=True)


# Instancia única del servicio (Singleton)
whatsapp_service = WhatsAppService()
