"""
Suite de Pruebas Unitarias para Reglas de Enrutamiento, Clasificación de Feedback,
Ciclo de Reintentos en Diagnóstico, Bienvenida Limpia de Rol y Eliminación de Términos Internos (GLPI).
"""

import sys
import json
import asyncio
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.router_logic import router_logic, RouterLogic, EstadoTicket
from app.services.router_service import handle_feedback_transition, RESOLVED_INTENTS, RETRY_INTENTS, TICKET_EXPLICIT_INTENTS
from app.services.rag_service import rag_service

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def test_handle_feedback_transition_resolved_direct():
    """Verifica que las intenciones de éxito transicionen directamente a FINALIZADO."""
    for intent in ["resolved", "RESOLVED", "si", "sí", "si me sirvio", "sí me sirvió", "gracias", "muchas gracias", "listo", "ya quedo"]:
        session = {"state": "DIAGNOSTICO", "diagnosis_attempts": 1}
        res = handle_feedback_transition(intent, "DIAGNOSTICO", session)
        assert res is not None, f"Fallo al reconocer '{intent}' como resuelto"
        assert res["state"] == "FINALIZADO"
        assert session["state"] == "FINALIZADO"
        assert session["diagnosis_attempts"] == 0
        assert "excelente" in res["response"].lower() or "alegra" in res["response"].lower()
        assert "glpi" not in res["response"].lower()
        assert res["quick_replies"] == []


def test_handle_feedback_transition_explicit_ticket_direct():
    """Verifica que solicitudes explícitas de reporte o asesor transicionen inmediatamente a RADICANDO_TICKET."""
    for intent in ["create_ticket", "CREATE_TICKET", "generar reporte", "crear reporte", "soporte", "asesor", "radicar", "ticket"]:
        session = {"state": "DIAGNOSTICO", "diagnosis_attempts": 1}
        res = handle_feedback_transition(intent, "DIAGNOSTICO", session)
        assert res is not None, f"Fallo al reconocer '{intent}' como reporte explícito"
        assert res["state"] == "RADICANDO_TICKET"
        assert session["state"] == "RADICANDO_TICKET"
        assert "nombre completo" in res["response"].lower()
        assert "glpi" not in res["response"].lower()
        assert res["quick_replies"] == []


def test_handle_feedback_transition_retry_first_attempt():
    """Verifica que en el intento 1 ('no', 'no me funcionó', 'RETRY_DIAGNOSIS') se mantenga en DIAGNOSTICO y pida detalles del error."""
    for intent in ["retry_diagnosis", "RETRY_DIAGNOSIS", "no", "no me funciono", "no me sirvió", "no pude", "sigue saliendo error"]:
        session = {"state": "DIAGNOSTICO", "diagnosis_attempts": 1}
        res = handle_feedback_transition(intent, "DIAGNOSTICO", session)
        assert res is not None, f"Fallo al procesar reintento para '{intent}'"
        assert res["state"] == "DIAGNOSTICO"
        assert session["state"] == "DIAGNOSTICO"
        assert session["diagnosis_attempts"] == 2
        assert "¿podrías indicarme qué mensaje de error" in res["response"].lower() or "en qué paso exacto" in res["response"].lower()
        assert "glpi" not in res["response"].lower()
        assert len(res["quick_replies"]) == 1
        assert res["quick_replies"][0]["payload"] == "CREATE_TICKET"


def test_handle_feedback_transition_retry_second_attempt_escalates():
    """Verifica que si ya se reintentó (diagnosis_attempts >= 2) y el usuario dice 'no', escale a RADICANDO_TICKET."""
    for intent in ["no", "no me funciono", "RETRY_DIAGNOSIS", "no pude"]:
        session = {"state": "DIAGNOSTICO", "diagnosis_attempts": 2}
        res = handle_feedback_transition(intent, "DIAGNOSTICO", session)
        assert res is not None, f"Fallo al escalar en intento 2 para '{intent}'"
        assert res["state"] == "RADICANDO_TICKET"
        assert session["state"] == "RADICANDO_TICKET"
        assert "nombre completo" in res["response"].lower()
        assert "glpi" not in res["response"].lower()


def test_handle_feedback_transition_followup_question():
    """Verifica que una pregunta de seguimiento no sea interceptada como feedback y retorne None."""
    session = {"state": "DIAGNOSTICO", "diagnosis_attempts": 1}
    res = handle_feedback_transition("¿Cómo descargo el certificado de notas?", "DIAGNOSTICO", session)
    assert res is None


@pytest.mark.asyncio
async def test_resolved_feedback_after_diagnostico():
    """Verifica que feedback positivo tras DIAGNOSTICO retorne FINALIZADO sin pedir nombre."""
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
        assert "glpi" not in res["mensaje"].lower()


@pytest.mark.asyncio
async def test_retry_cycle_and_escalation_flow():
    """Verifica el ciclo completo: Diagnóstico -> No (Pide Error) -> No (Escala a Ticket con Nombre)."""
    sess_id = "sess_retry_cycle_test"
    router_logic.reset_session(sess_id)
    session = router_logic.get_session(sess_id)
    session.user_role = "docente"
    session.estado = EstadoTicket.DIAGNOSTICO
    session.falla = "falla en portal docente"
    session.diagnosis_attempts = 1

    # Turno 1 de feedback: Primer "no" -> Debe pedir aclaración del error y mantenerse en DIAGNOSTICO
    r1 = await router_logic.procesar_mensaje("no me funciono", session_id=sess_id)
    assert r1["tipo"] == "DIAGNOSTICO"
    assert session.estado == EstadoTicket.DIAGNOSTICO
    assert session.diagnosis_attempts == 2
    assert "error" in r1["mensaje"].lower()
    assert "glpi" not in r1["mensaje"].lower()
    assert len(r1.get("quick_replies", [])) == 1

    # Turno 2 de feedback: Segundo "no" -> Debe escalar a RADICANDO_TICKET pidiendo Nombre Completo
    r2 = await router_logic.procesar_mensaje("sigue saliendo error", session_id=sess_id)
    assert r2["tipo"] == "RADICANDO_TICKET"
    assert session.estado == EstadoTicket.PIDIENDO_NOMBRE
    assert "nombre completo" in r2["mensaje"].lower()
    assert "glpi" not in r2["mensaje"].lower()


@pytest.mark.asyncio
async def test_explicit_ticket_escalation():
    """Verifica que pulsar 'CREATE_TICKET' o escribir 'generar reporte' pase directo a RADICANDO_TICKET."""
    sess_id = "sess_direct_ticket"
    router_logic.reset_session(sess_id)
    session = router_logic.get_session(sess_id)
    session.user_role = "funcionario"
    session.estado = EstadoTicket.DIAGNOSTICO
    session.diagnosis_attempts = 1

    res = await router_logic.procesar_mensaje("CREATE_TICKET", session_id=sess_id)
    assert res["tipo"] == "RADICANDO_TICKET"
    assert session.estado == EstadoTicket.PIDIENDO_NOMBRE
    assert "nombre completo" in res["mensaje"].lower()
    assert "glpi" not in res["mensaje"].lower()


@pytest.mark.asyncio
async def test_role_welcome_without_premature_rag_or_buttons():
    """BUG 1: Verifica que confirmar el rol sin pregunta previa NO llame a RAG ni adjunte quick replies."""
    sess_id = "sess_clean_role_welcome"
    router_logic.reset_session(sess_id)

    # 1. Saludo inicial
    r1 = await router_logic.procesar_mensaje("Hola, buenos días", session_id=sess_id)
    assert r1["tipo"] == "PIDIENDO_ROL"
    assert router_logic.get_session(sess_id).pending_query is None

    # 2. Selección de rol sin pregunta
    with patch.object(rag_service, "answer_query", new=AsyncMock()) as mock_rag:
        r2 = await router_logic.procesar_mensaje("Soy estudiante", session_id=sess_id)
        assert r2["tipo"] == "DIAGNOSTICO"
        assert router_logic.get_session(sess_id).estado == EstadoTicket.DIAGNOSTICO
        assert "procedimiento institucional o falla técnica" in r2["mensaje"]
        assert r2.get("quick_replies") == []
        mock_rag.assert_not_called()  # RAG NO debe ser invocado prematuramente


@pytest.mark.asyncio
async def test_direct_role_declaration_without_premature_rag():
    """BUG 1: Verifica que declarar el rol en el primer mensaje NO llame a RAG ni adjunte quick replies."""
    sess_id = "sess_direct_role"
    router_logic.reset_session(sess_id)

    with patch.object(rag_service, "answer_query", new=AsyncMock()) as mock_rag:
        r = await router_logic.procesar_mensaje("funcionario", session_id=sess_id)
        assert r["tipo"] == "DIAGNOSTICO"
        assert router_logic.get_session(sess_id).user_role in ["administrativo", "funcionario"]
        assert r.get("quick_replies") == []
        mock_rag.assert_not_called()


@pytest.mark.asyncio
async def test_placeholder_sanitization_in_rag_service():
    """BUG 2: Verifica que el RAG sanitize automáticamente placeholders de GLPI o URLs inventadas."""
    fake_ollama_resp = {
        "message": {
            "content": "Para solucionar el problema ingresa a [URL del GLPI] y asigna tu caso en GLPI o usa [Link]."
        }
    }
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=fake_ollama_resp)
        mock_post.return_value = mock_response

        res = await rag_service.answer_query(query="falla de monitor", user_role="funcionario")
        resp_text = res["response"]

        assert "[URL del GLPI]" not in resp_text
        assert "GLPI" not in resp_text
        assert "Mesa de Ayuda TI" in resp_text
        assert "[Link]" not in resp_text


# -----------------------------------------------------------------------------
# PRUEBAS: ENRUTAMIENTO SEMÁNTICO CON LLM (AUTOSERVICIO VS. SOPORTE FÍSICO)
# -----------------------------------------------------------------------------

def test_classify_request_intent_unit():
    """Verifica que classify_request_intent procese el JSON de Ollama correctamente."""
    from app.services.router_service import classify_request_intent

    with patch("httpx.post") as mock_post:
        # Caso 1: Retorna AUTOSERVICIO
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": json.dumps({"categoria": "AUTOSERVICIO"})}
        mock_post.return_value = mock_resp

        res = classify_request_intent("¿Cómo reporto las fallas a clase y subo notas?", "docente")
        assert res == "AUTOSERVICIO"

        # Caso 2: Retorna SOPORTE_FISICO
        mock_resp.json.return_value = {"response": json.dumps({"categoria": "SOPORTE_FISICO"})}
        res2 = classify_request_intent("El cable de red está roto y el computador no prende", "funcionario")
        assert res2 == "SOPORTE_FISICO"

        # Caso 3: Error de red -> Fallback seguro a AUTOSERVICIO
        mock_post.side_effect = Exception("Ollama connection error")
        res3 = classify_request_intent("consulta cualquiera", "estudiante")
        assert res3 == "AUTOSERVICIO"


@pytest.mark.asyncio
async def test_academic_fallas_a_clase_stays_in_autoservicio_and_diagnostico():
    """
    Verifica que consultas académicas con la palabra 'fallas' (ej: fallas a clase, inasistencias, notas)
    NO salten a radicación de hardware, sino que continúen al RAG (AUTOSERVICIO / DIAGNOSTICO).
    """
    sess_id = "sess_academic_fallas"
    router_logic.reset_session(sess_id)
    session = router_logic.get_session(sess_id)
    session.user_role = "docente"

    msg = "¿Cómo y hasta cuándo puedo subir las notas de mis estudiantes y reportar las fallas a clase?"

    fake_rag_resp = {
        "response": "Para subir notas y reportar inasistencias (fallas a clase), ingresa al sistema SIAAF en el módulo docente...",
        "sources": ["manual_siaaf.pdf"],
        "has_context": True,
        "quick_replies": []
    }

    with patch.object(router_logic, "classify_intent", new=AsyncMock(return_value="AUTOSERVICIO")), \
         patch.object(rag_service, "answer_query", new=AsyncMock(return_value=fake_rag_resp)) as mock_rag:

        res = await router_logic.procesar_mensaje(msg, session_id=sess_id)

        assert res["tipo"] == "DIAGNOSTICO"
        assert res["state"] == "DIAGNOSTICO"
        assert router_logic.get_session(sess_id).estado == EstadoTicket.DIAGNOSTICO
        assert "Nombre Completo" not in res["mensaje"]
        assert "SIAAF" in res["mensaje"]
        mock_rag.assert_called_once()


@pytest.mark.asyncio
async def test_physical_hardware_direct_routing_from_idle():
    """Verifica que consultas de SOPORTE_FISICO salten DIRECTAMENTE a RADICANDO_TICKET pidiendo Nombre."""
    sess_id = "sess_hw_idle"
    router_logic.reset_session(sess_id)
    session = router_logic.get_session(sess_id)
    session.user_role = "funcionario"

    msg = "Solicito la revisión y reparación de la conexión a internet por cable del equipo de escritorio de mi oficina"

    with patch.object(router_logic, "classify_intent", new=AsyncMock(return_value="SOPORTE_FISICO")), \
         patch.object(rag_service, "answer_query", new=AsyncMock()) as mock_rag:

        res = await router_logic.procesar_mensaje(msg, session_id=sess_id)

        assert res["tipo"] == "RADICANDO_TICKET"
        assert res["state"] == "RADICANDO_TICKET"
        assert res["source"] == "UniMon_SemanticRouter_Hardware"
        assert router_logic.get_session(sess_id).estado == EstadoTicket.PIDIENDO_NOMBRE
        assert "revisión técnica o falla física" in res["mensaje"]
        assert "Nombre Completo" in res["mensaje"]
        assert res.get("quick_replies") == []
        mock_rag.assert_not_called()  # RAG NO debe ser llamado para soporte físico directo


@pytest.mark.asyncio
async def test_physical_hardware_no_enciende_direct_routing():
    """Verifica que 'mi computador no enciende' clasificado como SOPORTE_FISICO salte directo a captura de Nombre."""
    sess_id = "sess_hw_no_prende"
    router_logic.reset_session(sess_id)
    session = router_logic.get_session(sess_id)
    session.user_role = "docente"

    with patch.object(router_logic, "classify_intent", new=AsyncMock(return_value="SOPORTE_FISICO")), \
         patch.object(rag_service, "answer_query", new=AsyncMock()) as mock_rag:

        res = await router_logic.procesar_mensaje("mi computador no enciende", session_id=sess_id)

        assert res["tipo"] == "RADICANDO_TICKET"
        assert res["source"] == "UniMon_SemanticRouter_Hardware"
        assert router_logic.get_session(sess_id).estado == EstadoTicket.PIDIENDO_NOMBRE
        assert "Nombre Completo" in res["mensaje"]
        assert res.get("quick_replies") == []
        mock_rag.assert_not_called()


@pytest.mark.asyncio
async def test_physical_hardware_routing_after_role_qualification():
    """Verifica el flujo: Falla física sin rol previo -> Califica rol -> Salto semántico directo a RADICANDO_TICKET."""
    sess_id = "sess_hw_role_flow"
    router_logic.reset_session(sess_id)

    # 1. Consulta inicial de hardware sin rol
    r1 = await router_logic.procesar_mensaje("El cable de red del computador de mi oficina está roto", session_id=sess_id)
    assert r1["tipo"] == "PIDIENDO_ROL"

    # 2. Usuario indica rol -> Debe clasificar semánticamente y saltar a RADICANDO_TICKET sin pasar por RAG
    with patch.object(router_logic, "classify_intent", new=AsyncMock(return_value="SOPORTE_FISICO")), \
         patch.object(rag_service, "answer_query", new=AsyncMock()) as mock_rag:

        r2 = await router_logic.procesar_mensaje("Soy docente", session_id=sess_id)

        assert r2["tipo"] == "RADICANDO_TICKET"
        assert r2["source"] == "UniMon_SemanticRouter_Hardware"
        assert router_logic.get_session(sess_id).estado == EstadoTicket.PIDIENDO_NOMBRE
        assert "revisión técnica o falla física" in r2["mensaje"]
        assert "Nombre Completo" in r2["mensaje"]
        assert r2.get("quick_replies") == []
        mock_rag.assert_not_called()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
