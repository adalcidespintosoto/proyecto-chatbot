"""
Suite de pruebas de integración para el módulo de WhatsApp Cloud API (Meta) en UniMon.
Verifica:
1. Handshake de verificación del Webhook (GET) con token válido e inválido.
2. Endpoint de estado y diagnóstico (/api/whatsapp/status).
3. Recepción de mensajes en tiempo real (POST), deduplicación y respuestas asíncronas.
4. Conversor de formato Markdown a formato nativo de WhatsApp.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings
from app.services.whatsapp_service import markdown_to_whatsapp, whatsapp_service

client = TestClient(app)


def test_markdown_to_whatsapp_conversion():
    """Verifica que el formateo de texto se adapte correctamente a las reglas de WhatsApp."""
    # 1. Negrita
    md_bold = "Este es un texto **importante** para el estudiante."
    wa_bold = markdown_to_whatsapp(md_bold)
    assert wa_bold == "Este es un texto *importante* para el estudiante."

    # 2. Enlaces
    md_link = "Ingresa a [Portal Estudiantes](https://www.unisimon.edu.co/portales) para cambiarla."
    wa_link = markdown_to_whatsapp(md_link)
    assert "Portal Estudiantes (https://www.unisimon.edu.co/portales)" in wa_link

    # 3. Encabezados
    md_head = "### Pasos para restablecer clave"
    wa_head = markdown_to_whatsapp(md_head)
    assert wa_head == "*Pasos para restablecer clave*"

    # 4. Separador
    md_sep = "Texto arriba\n---\nTexto abajo"
    wa_sep = markdown_to_whatsapp(md_sep)
    assert "────────────────────" in wa_sep


def test_whatsapp_webhook_verification_success():
    """Verifica el handshake exitoso de Meta con el token configurado."""
    settings = get_settings()
    verify_token = settings.whatsapp_verify_token
    challenge = "1234567890"

    response = client.get(
        f"/api/whatsapp?hub.mode=subscribe&hub.verify_token={verify_token}&hub.challenge={challenge}"
    )

    assert response.status_code == 200
    assert response.text == challenge


def test_whatsapp_webhook_verification_invalid_token():
    """Verifica que tokens incorrectos sean rechazados con 403 Forbidden."""
    response = client.get(
        "/api/whatsapp?hub.mode=subscribe&hub.verify_token=token_invalido_hacker&hub.challenge=999"
    )

    assert response.status_code == 403
    assert "Verificación fallida" in response.text


def test_whatsapp_status_endpoint():
    """Verifica el endpoint de diagnóstico del estado de WhatsApp."""
    response = client.get("/api/whatsapp/status")
    assert response.status_code == 200
    data = response.json()
    assert "whatsapp_channel_enabled" in data
    assert "is_ready_for_production" in data
    assert "api_version" in data
    assert data["api_version"] == "v20.0"


def test_whatsapp_receive_webhook_status_event():
    """Verifica que las notificaciones de estado (delivered, read) se acepten con 200 sin procesar mensajes."""
    status_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "statuses": [
                                {
                                    "id": "wamid.HBgL...",
                                    "status": "delivered",
                                    "timestamp": "1727618000",
                                    "recipient_id": "573001234567"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    response = client.post("/api/whatsapp", json=status_payload)
    assert response.status_code == 200
    assert response.json() == {"status": "EVENT_RECEIVED"}


@pytest.mark.asyncio
async def test_whatsapp_deduplication():
    """Verifica que mensajes con el mismo ID no se procesen dos veces."""
    msg_id = "test_wamid_unique_001"
    assert not whatsapp_service.is_message_duplicate(msg_id)
    assert whatsapp_service.is_message_duplicate(msg_id)  # Segunda vez debe ser duplicado


@pytest.mark.asyncio
async def test_whatsapp_process_message_flow():
    """Verifica el procesamiento completo simulando un mensaje entrante de un estudiante."""
    incoming_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "573001112233",
                                "phone_number_id": "106540352242922"
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Carlos Gomez"},
                                    "wa_id": "573009998877"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "573009998877",
                                    "id": "wamid.HBgLTEST_FLOW_999",
                                    "timestamp": "1727618500",
                                    "text": {
                                        "body": "Hola, se me olvidó la contraseña de mi correo"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    # Mockeamos el envío hacia Meta para validar que el servicio despache la respuesta
    with patch.object(whatsapp_service, "send_text_message", new_callable=AsyncMock) as mock_send_text, \
         patch.object(whatsapp_service, "send_interactive_buttons_message", new_callable=AsyncMock) as mock_send_btns, \
         patch.object(whatsapp_service, "mark_message_as_read", new_callable=AsyncMock):

        mock_send_text.return_value = True
        mock_send_btns.return_value = True

        await whatsapp_service.process_incoming_webhook_payload(incoming_payload)

        # Debe haber llamado a enviar texto o botones interactivos al número del remitente
        called = mock_send_text.called or mock_send_btns.called
        assert called, "El servicio debió despachar la respuesta al usuario en WhatsApp"
        
        if mock_send_text.called:
            called_phone = mock_send_text.call_args.kwargs.get("to_phone") or mock_send_text.call_args[0][0]
            assert called_phone == "573009998877"
        if mock_send_btns.called:
            called_phone = mock_send_btns.call_args.kwargs.get("to_phone") or mock_send_btns.call_args[0][0]
            assert called_phone == "573009998877"
