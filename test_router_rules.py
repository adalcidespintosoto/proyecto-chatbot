import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.documents import Document

from app.services.normalizer_service import normalize_and_expand_query
from app.services.router_logic import router_logic, RouterLogic, EstadoTicket
from app.services.rag_service import rag_service, STRICT_SYSTEM_PROMPT_TEMPLATE, MENSAJE_NO_DOCUMENTADO, MIN_RELEVANCE_SCORE_THRESHOLD

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def run_tests():
    print("=" * 70)
    print("VALIDACIÓN: ESTADO PIDIENDO_ROL Y CALIFICACIÓN OBLIGATORIA DE PERFIL")
    print("=" * 70)

    # -------------------------------------------------------------
    # PRUEBA 1: Flujo A (Pregunta primero -> Pide Rol -> Califica -> Respuesta)
    # -------------------------------------------------------------
    print("\n[PRUEBA 1] Flujo A: Pregunta primero sin rol -> PIDIENDO_ROL -> Funcionario")
    sess_a = "sess_flujo_a"
    router_logic.reset_session(sess_a)

    # Turno 1: Pregunta directa de funcionario sin declarar rol
    r_a1 = await router_logic.procesar_mensaje("¿Cómo veo los reportes de desertores?", session_id=sess_a)
    assert r_a1["tipo"] == "PIDIENDO_ROL"
    assert router_logic.get_session(sess_a).estado == EstadoTicket.PIDIENDO_ROL
    assert router_logic.get_session(sess_a).pending_query == "¿Cómo veo los reportes de desertores?"
    assert "¿Eres **Estudiante** o **Funcionario / Docente**?" in r_a1["mensaje"]
    print("  ✓ Bot intercepta la consulta y pregunta si es Estudiante o Funcionario")

    # Turno 2: Usuario responde con su rol
    mock_desertores_resp = {
        "response": "Paso 1: Ingresa a SIAAF Módulo Directores. Paso 2: Selecciona Reportes -> Desertores. Paso 3: Filtra por periodo académico.",
        "sources": ["Reporte_Desertores.pdf"],
        "has_context": True
    }
    with patch.object(rag_service, "answer_query", new=AsyncMock(return_value=mock_desertores_resp)):
        r_a2 = await router_logic.procesar_mensaje("Soy funcionario", session_id=sess_a)
        assert r_a2["tipo"] == "DIAGNOSTICO"
        assert router_logic.get_session(sess_a).estado == EstadoTicket.DIAGNOSTICO
        assert router_logic.get_session(sess_a).user_role == "funcionario"
        assert router_logic.get_session(sess_a).pending_query is None
        assert "SIAAF" in r_a2["mensaje"]
        print("  ✓ Bot ejecuta la consulta retenida con rol 'funcionario' y entrega la solución de inmediato")

    # -------------------------------------------------------------
    # PRUEBA 2: Flujo B (Saludo primero -> Pide Rol -> Califica -> Queda listo)
    # -------------------------------------------------------------
    print("\n[PRUEBA 2] Flujo B: Saludo primero -> PIDIENDO_ROL -> Estudiante -> Listo")
    sess_b = "sess_flujo_b"
    router_logic.reset_session(sess_b)

    # Turno 1: Saludo simple
    r_b1 = await router_logic.procesar_mensaje("Hola", session_id=sess_b)
    assert r_b1["tipo"] == "PIDIENDO_ROL"
    assert router_logic.get_session(sess_b).estado == EstadoTicket.PIDIENDO_ROL
    assert router_logic.get_session(sess_b).pending_query is None
    print("  ✓ Saludo inicial solicita identificación de rol")

    # Turno 2: Responde "Estudiante"
    r_b2 = await router_logic.procesar_mensaje("Estudiante", session_id=sess_b)
    assert r_b2["tipo"] == "DIAGNOSTICO"
    assert router_logic.get_session(sess_b).estado == EstadoTicket.DIAGNOSTICO
    assert router_logic.get_session(sess_b).user_role == "estudiante"
    assert "¡Entendido! ¿En qué procedimiento institucional o falla técnica te puedo colaborar hoy?" in r_b2["mensaje"]
    print("  ✓ Bot confirma rol 'estudiante' y queda listo en DIAGNOSTICO para recibir consultas")

    # -------------------------------------------------------------
    # PRUEBA 3: Rol declarado directamente en el primer mensaje
    # -------------------------------------------------------------
    print("\n[PRUEBA 3] Flujo Directo: Rol y pregunta en el primer mensaje")
    sess_c = "sess_flujo_directo"
    router_logic.reset_session(sess_c)

    mock_portal_resp = {
        "response": "Paso 1: Entra a https://unisimon.edu.co. Paso 2: Haz clic en Recuperar contraseña.",
        "sources": ["instructivo portales estudiantes.pdf"],
        "has_context": True
    }
    with patch.object(rag_service, "answer_query", new=AsyncMock(return_value=mock_portal_resp)):
        r_c = await router_logic.procesar_mensaje("soy estudiante y no puedo entrar al portal", session_id=sess_c)
        assert r_c["tipo"] == "DIAGNOSTICO"
        assert router_logic.get_session(sess_c).user_role == "estudiante"
        assert router_logic.get_session(sess_c).estado == EstadoTicket.DIAGNOSTICO
        print("  ✓ Bot detecta rol 'estudiante' inmediatamente y procesa el RAG sin estado intermedio")

    # -------------------------------------------------------------
    # PRUEBA 4: Detección de REPORT_PATTERNS
    # -------------------------------------------------------------
    print("\n[PRUEBA 4] Detección de REPORT_PATTERNS")
    report_frases = [
        "vamos a reportar", "reportar", "reportalo", "radicar", "radica",
        "crear ticket", "abrir caso", "ayudame a reportar", "haz el reporte",
        "si", "sí", "por favor", "porfa", "dale", "ayúdame", "solicito soporte"
    ]
    for frase in report_frases:
        assert RouterLogic.is_report_request(frase), f"ERROR: '{frase}' no fue detectada por is_report_request"
        print(f"  ✓ Intención de reporte detectada: '{frase}'")

    # -------------------------------------------------------------
    # PRUEBA 5: Salto Directo a Radicación y Flujo Completo
    # -------------------------------------------------------------
    print("\n[PRUEBA 5] Salto Directo a PIDIENDO_NOMBRE y Radicación Completa")
    sess_d = "sess_radicacion_completa"
    router_logic.reset_session(sess_d)
    router_logic.get_session(sess_d).user_role = "funcionario"
    router_logic.get_session(sess_d).estado = EstadoTicket.DIAGNOSTICO

    r_d1 = await router_logic.procesar_mensaje("vamos a reportar", session_id=sess_d)
    assert r_d1["tipo"] == "RADICANDO_TICKET"
    assert router_logic.get_session(sess_d).estado == EstadoTicket.PIDIENDO_NOMBRE
    assert "glpi" not in r_d1["mensaje"].lower()

    r_d2 = await router_logic.procesar_mensaje("Carlos Julio Barreto", session_id=sess_d)
    assert router_logic.get_session(sess_d).estado == EstadoTicket.PIDIENDO_CORREO

    r_d3 = await router_logic.procesar_mensaje("carlos.barreto@unisimon.edu.co", session_id=sess_d)
    assert router_logic.get_session(sess_d).estado == EstadoTicket.PIDIENDO_DESCRIPCION

    with patch("app.services.router_logic.glpi_client.crear_ticket", new=AsyncMock(return_value={"ticket_id": 11800, "status": "success"})):
        r_d4 = await router_logic.procesar_mensaje("No llega el enlace de restablecimiento de contraseña", session_id=sess_d)
        assert r_d4["tipo"] == "TICKET_CREADO"
        assert r_d4["ticket_id"] == 11800
        assert router_logic.get_session(sess_d).estado == EstadoTicket.IDLE
        assert "glpi" not in r_d4["mensaje"].lower()
        print("  ✓ Flujo completo de radicación validado exitosamente")

    # -------------------------------------------------------------
    # PRUEBA 6: Cancelación Universal ('no')
    # -------------------------------------------------------------
    print("\n[PRUEBA 6] Cancelación Universal ('no')")
    sess_cancel = "sess_cancel_test"
    router_logic.reset_session(sess_cancel)
    router_logic.get_session(sess_cancel).estado = EstadoTicket.OFRECIENDO_RADICACION
    r_cancel = await router_logic.procesar_mensaje("no", session_id=sess_cancel)
    assert r_cancel["tipo"] == "CANCELADO"
    assert router_logic.get_session(sess_cancel).estado == EstadoTicket.IDLE
    assert "glpi" not in r_cancel["mensaje"].lower()
    print("  ✓ Cancelación con 'no' reseteó la sesión a IDLE")

    # -------------------------------------------------------------
    # PRUEBA 7: Política TTL de Expiración de Sesiones Inactivas
    # -------------------------------------------------------------
    print("\n[PRUEBA 7] Control Temporal (TTL) y Limpieza de Sesiones Inactivas")
    from datetime import datetime, timezone, timedelta
    sess_ttl = "sess_ttl_expired"
    router_logic.reset_session(sess_ttl)
    s = router_logic.get_session(sess_ttl)
    s.estado = EstadoTicket.PIDIENDO_NOMBRE
    s.pending_query = "Consulta antigua"
    # Simular inactividad de 30 minutos
    s.last_interaction = datetime.now(timezone.utc) - timedelta(minutes=30)

    # 7.1 Limpieza explícita
    cleaned = RouterLogic.clean_inactive_sessions(ttl_minutes=20)
    assert cleaned >= 1
    assert router_logic.get_session(sess_ttl).estado == EstadoTicket.IDLE
    assert router_logic.get_session(sess_ttl).pending_query is None
    print("  ✓ RouterLogic.clean_inactive_sessions() restableció la sesión inactiva a IDLE")

    # 7.2 Expiración al recibir mensaje tras inactividad
    sess_ttl2 = "sess_ttl_expired2"
    router_logic.reset_session(sess_ttl2)
    s2 = router_logic.get_session(sess_ttl2)
    s2.estado = EstadoTicket.PIDIENDO_ROL
    s2.pending_query = "¿Cómo cambio mi clave?"
    s2.last_interaction = datetime.now(timezone.utc) - timedelta(minutes=25)

    # Al llegar nuevo mensaje, debe detectar la expiración y reiniciar
    r_ttl = await router_logic.procesar_mensaje("Hola", session_id=sess_ttl2)
    assert r_ttl["tipo"] == "PIDIENDO_ROL"
    print("  ✓ Mensaje tras inactividad >20 min reinició sesión y procedió con flujo limpio")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE (100% OK)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
