"""
Suite de Pruebas Unitarias para Reglas de Enrutamiento, Clasificación de Feedback y Transición de Estados de UniMon.
"""

import sys
import asyncio
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import AsyncMock, patch

from app.services.router_logic import router_logic, RouterLogic, EstadoTicket
from app.services.router_service import handle_feedback_transition, RESOLVED_INTENTS, TICKET_INTENTS
from app.services.rag_service import rag_service

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def test_handle_feedback_transition_resolved_direct():
    """Verifica que las intenciones de éxito transicionen directamente a FINALIZADO."""
    for intent in ["resolved", "RESOLVED", "si", "sí", "si me sirvio", "sí me sirvió", "gracias", "muchas gracias", "listo"]:
        session = {"state": "DIAGNOSTICO"}
        res = handle_feedback_transition(intent, "DIAGNOSTICO", session)
        assert res is not None, f"Fallo al reconocer '{intent}' como resuelto"
        assert res["state"] == "FINALIZADO"
        assert session["state"] == "FINALIZADO"
        assert "excelente" in res["response"].lower() or "alegra" in res["response"].lower()
        assert res["quick_replies"] == []


def test_handle_feedback_transition_ticket_direct():
    """Verifica que las intenciones de falla/escalado transicionen a RADICANDO_TICKET."""
    for intent in ["create_ticket", "CREATE_TICKET", "no", "no me sirvio", "no me sirvió", "no me funciono", "no pude", "radicar"]:
        session = {"state": "DIAGNOSTICO"}
        res = handle_feedback_transition(intent, "DIAGNOSTICO", session)
        assert res is not None, f"Fallo al reconocer '{intent}' como escalado a ticket"
        assert res["state"] == "RADICANDO_TICKET"
        assert session["state"] == "RADICANDO_TICKET"
        assert "nombre completo" in res["response"].lower()
        assert res["quick_replies"] == []


def test_handle_feedback_transition_followup_question():
    """Verifica que una pregunta de seguimiento no sea interceptada como feedback y retorne None."""
    session = {"state": "DIAGNOSTICO"}
    res = handle_feedback_transition("¿Cómo descargo el certificado?", "DIAGNOSTICO", session)
    assert res is None


@pytest.mark.asyncio
async def test_resolved_feedback_after_diagnostico():
    """Verifica que 'si me sirvio', 'sí', 'gracias' o 'RESOLVED' tras DIAGNOSTICO retorne FINALIZADO."""
    test_cases = ["si me sirvio", "sí", "gracias", "RESOLVED", "si me funcionó", "muchas gracias"]
    
    for user_input in test_cases:
        sess_id = f"sess_resolved_{user_input.replace(' ', '_')}"
        router_logic.reset_session(sess_id)
        session = router_logic.get_session(sess_id)
        session.user_role = "estudiante"
        session.estado = EstadoTicket.DIAGNOSTICO
        session.falla = "problema de acceso"

        res = await router_logic.procesar_mensaje(user_input, session_id=sess_id)
        assert res["tipo"] in ["FINALIZADO", "SOLUCIONADO"], f"Esperaba FINALIZADO para '{user_input}', obtuvo {res['tipo']}"
        assert router_logic.get_session(sess_id).estado in [EstadoTicket.IDLE, EstadoTicket.FINALIZADO]
        assert "nombre" not in res["mensaje"].lower()
        assert "ticket" not in res["mensaje"].lower() or "otra plataforma" in res["mensaje"].lower()


@pytest.mark.asyncio
async def test_ticket_feedback_after_diagnostico():
    """Verifica que 'no', 'no me funciono' o 'CREATE_TICKET' tras DIAGNOSTICO retorne RADICANDO_TICKET y pida Nombre."""
    test_cases = ["no", "no me funciono", "CREATE_TICKET", "no me sirvió", "no pude", "radicar"]

    for user_input in test_cases:
        sess_id = f"sess_ticket_{user_input.replace(' ', '_')}"
        router_logic.reset_session(sess_id)
        session = router_logic.get_session(sess_id)
        session.user_role = "funcionario"
        session.estado = EstadoTicket.DIAGNOSTICO
        session.falla = "error en sistema"

        res = await router_logic.procesar_mensaje(user_input, session_id=sess_id)
        assert res["tipo"] == "RADICANDO_TICKET", f"Esperaba RADICANDO_TICKET para '{user_input}', obtuvo {res['tipo']}"
        assert router_logic.get_session(sess_id).estado == EstadoTicket.PIDIENDO_NOMBRE
        assert "nombre" in res["mensaje"].lower()


@pytest.mark.asyncio
async def test_full_flow_with_role_diagnostico_and_ticket():
    """Prueba flujo completo: Pregunta -> Rol -> Diagnóstico con Quick Replies -> No -> Slot Filling -> Ticket GLPI."""
    sess_id = "sess_full_flow_test"
    router_logic.reset_session(sess_id)

    # 1. Pregunta sin rol
    r1 = await router_logic.procesar_mensaje("No puedo ingresar al portal", session_id=sess_id)
    assert r1["tipo"] == "PIDIENDO_ROL"

    # 2. Indicar rol
    mock_rag = {
        "response": "Paso 1: Entra al portal. Paso 2: Restablece tu clave.",
        "sources": ["manual_portal.pdf"],
        "has_context": True,
        "quick_replies": [
            {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
            {"label": "🎫 No, radicar ticket", "payload": "CREATE_TICKET"}
        ]
    }
    with patch.object(rag_service, "answer_query", new=AsyncMock(return_value=mock_rag)):
        r2 = await router_logic.procesar_mensaje("Soy estudiante", session_id=sess_id)
        assert r2["tipo"] == "DIAGNOSTICO"
        assert len(r2.get("quick_replies", [])) == 2

    # 3. Usuario pulsa 'No, radicar ticket' (CREATE_TICKET)
    r3 = await router_logic.procesar_mensaje("CREATE_TICKET", session_id=sess_id)
    assert r3["tipo"] == "RADICANDO_TICKET"
    assert router_logic.get_session(sess_id).estado == EstadoTicket.PIDIENDO_NOMBRE

    # 4. Slot Filling: Nombre
    r4 = await router_logic.procesar_mensaje("Ana Maria Gomez", session_id=sess_id)
    assert router_logic.get_session(sess_id).estado == EstadoTicket.PIDIENDO_CORREO

    # 5. Slot Filling: Correo
    r5 = await router_logic.procesar_mensaje("ana.gomez@unisimon.edu.co", session_id=sess_id)
    assert router_logic.get_session(sess_id).estado == EstadoTicket.PIDIENDO_DESCRIPCION

    # 6. Slot Filling: Descripción y radicación
    with patch("app.services.router_logic.glpi_client.crear_ticket", new=AsyncMock(return_value={"ticket_id": 9901, "status": "success"})):
        r6 = await router_logic.procesar_mensaje("El enlace de restablecimiento dice token inválido", session_id=sess_id)
        assert r6["tipo"] == "TICKET_CREADO"
        assert r6["ticket_id"] == 9901
        assert router_logic.get_session(sess_id).estado == EstadoTicket.IDLE


if __name__ == "__main__":
    pytest.main(["-v", __file__])
