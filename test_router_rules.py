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
    print("VALIDACIÓN: PROHIBICIÓN DE REFERENCIAR MANUALES Y ACCIÓN DIRECTA PASO A PASO")
    print("=" * 70)

    # -------------------------------------------------------------
    # PRUEBA 1: Verificación del System Prompt con Prohibición de Enviar a Leer
    # -------------------------------------------------------------
    print("\n[PRUEBA 1] System Prompt RAG con Directivas de Acción Directa")
    assert "PROHIBICIÓN TOTAL DE REFERENCIAR MANUALES AL USUARIO" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "NUNCA le digas al usuario \"revisa el instructivo\", \"consulta el PDF\"" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "GUÍA ACCIONABLE PASO A PASO" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "¿Te sirvieron estos pasos o prefieres que radique un caso de soporte técnico en GLPI por ti?" in STRICT_SYSTEM_PROMPT_TEMPLATE
    print("  ✓ System prompt contiene las directivas estrictas de respuesta directa paso a paso")

    # -------------------------------------------------------------
    # PRUEBA 2: Detección de REPORT_PATTERNS (is_report_request)
    # -------------------------------------------------------------
    print("\n[PRUEBA 2] Detección de REPORT_PATTERNS")
    report_frases = [
        "vamos a reportar", "reportar", "reportalo", "radicar", "radica",
        "crear ticket", "abrir caso", "ayudame a reportar", "haz el reporte",
        "si", "sí", "por favor", "porfa", "dale", "ayúdame", "solicito soporte"
    ]
    for frase in report_frases:
        assert RouterLogic.is_report_request(frase), f"ERROR: '{frase}' no fue detectada por is_report_request"
        print(f"  ✓ Intención de reporte/radicación detectada: '{frase}'")

    # -------------------------------------------------------------
    # PRUEBA 3: Salto Directo a Radicación desde DIAGNOSTICO y OFRECIENDO_RADICACION
    # -------------------------------------------------------------
    print("\n[PRUEBA 3] Salto Directo a PIDIENDO_NOMBRE sin Plantilla Intermedia")
    
    # 3.1 Desde DIAGNOSTICO con "vamos a reportar"
    sess_d1 = "sess_diag_reportar"
    router_logic.reset_session(sess_d1)
    router_logic.get_session(sess_d1).estado = EstadoTicket.DIAGNOSTICO

    r_d1 = await router_logic.procesar_mensaje("vamos a reportar", session_id=sess_d1)
    assert r_d1["tipo"] == "RADICANDO_TICKET"
    assert router_logic.get_session(sess_d1).estado == EstadoTicket.PIDIENDO_NOMBRE
    assert "Con gusto te ayudo a radicar el caso en GLPI. Para iniciar, por favor indícame tu **Nombre Completo**:" in r_d1["mensaje"]
    print("  ✓ 'vamos a reportar' en DIAGNOSTICO transicionó de inmediato a PIDIENDO_NOMBRE")

    # 3.2 Desde OFRECIENDO_RADICACION con "ayudame a reportar"
    sess_o1 = "sess_ofrece_reportar"
    router_logic.reset_session(sess_o1)
    router_logic.get_session(sess_o1).estado = EstadoTicket.OFRECIENDO_RADICACION

    r_o1 = await router_logic.procesar_mensaje("ayudame a reportar", session_id=sess_o1)
    assert r_o1["tipo"] == "RADICANDO_TICKET"
    assert router_logic.get_session(sess_o1).estado == EstadoTicket.PIDIENDO_NOMBRE
    assert "Con gusto te ayudo a radicar el caso en GLPI. Para iniciar, por favor indícame tu **Nombre Completo**:" in r_o1["mensaje"]
    print("  ✓ 'ayudame a reportar' en OFRECIENDO_RADICACION transicionó de inmediato a PIDIENDO_NOMBRE")

    # -------------------------------------------------------------
    # PRUEBA 4: Diagnóstico Continuo e Ilimitado (Más de 3 Turnos)
    # -------------------------------------------------------------
    print("\n[PRUEBA 4] Diagnóstico Continuo e Ilimitado (Turnos > 3)")
    sess_unlimited = "sess_unlimited_diag"
    router_logic.reset_session(sess_unlimited)

    mock_rag_response = {
        "response": "Paso 1: Entra a https://unisimon.edu.co. Paso 2: Haz clic en Recuperar contraseña. ¿Te sirvieron estos pasos o prefieres que radique un caso de soporte técnico en GLPI por ti?",
        "sources": ["P-GT-11_Portales.pdf"],
        "has_context": True
    }

    with patch.object(rag_service, "answer_query", new=AsyncMock(return_value=mock_rag_response)):
        # Turno 1
        r1 = await router_logic.procesar_mensaje("no puedo entrar al portal institucional", session_id=sess_unlimited)
        assert r1["tipo"] == "DIAGNOSTICO"
        assert router_logic.get_session(sess_unlimited).estado == EstadoTicket.DIAGNOSTICO

        # Turno 2
        r2 = await router_logic.procesar_mensaje("Ya hice clic y no me llega el correo de recuperacion", session_id=sess_unlimited)
        assert r2["tipo"] == "DIAGNOSTICO"

        # Turno 3
        r3 = await router_logic.procesar_mensaje("Sigue sin llegar el enlace a mi bandeja", session_id=sess_unlimited)
        assert r3["tipo"] == "DIAGNOSTICO"

        # Turno 4 (Debe permanecer en DIAGNOSTICO sin forzar salida a plantilla)
        r4 = await router_logic.procesar_mensaje("Probe en spam y tampoco", session_id=sess_unlimited)
        assert r4["tipo"] == "DIAGNOSTICO"
        assert router_logic.get_session(sess_unlimited).estado == EstadoTicket.DIAGNOSTICO
        print("  ✓ Diagnóstico continuo verificado exitosamente en turnos 1, 2, 3 y 4")

        # Turno 5: Usuario decide reportar ➔ Salto inmediato a PIDIENDO_NOMBRE
        r5 = await router_logic.procesar_mensaje("radica el caso por favor", session_id=sess_unlimited)
        assert r5["tipo"] == "RADICANDO_TICKET"
        assert router_logic.get_session(sess_unlimited).estado == EstadoTicket.PIDIENDO_NOMBRE
        print("  ✓ Salto a radicación tras turnos prolongados completado")

    # -------------------------------------------------------------
    # PRUEBA 5: Flujo Completo de Radicación en GLPI
    # -------------------------------------------------------------
    print("\n[PRUEBA 5] Flujo Completo de Radicación en GLPI")
    # Paso 1: Nombre
    r_nom = await router_logic.procesar_mensaje("Carlos Julio Barreto", session_id=sess_unlimited)
    assert router_logic.get_session(sess_unlimited).estado == EstadoTicket.PIDIENDO_CORREO

    # Paso 2: Correo
    r_cor = await router_logic.procesar_mensaje("carlos.barreto@unisimon.edu.co", session_id=sess_unlimited)
    assert router_logic.get_session(sess_unlimited).estado == EstadoTicket.PIDIENDO_DESCRIPCION

    # Paso 3: Descripción -> Ticket GLPI
    with patch("app.services.router_logic.glpi_client.crear_ticket", new=AsyncMock(return_value={"ticket_id": 11800, "status": "success"})):
        r_tik = await router_logic.procesar_mensaje("No llega el enlace de restablecimiento de contraseña de portal", session_id=sess_unlimited)
        assert r_tik["tipo"] == "TICKET_CREADO"
        assert r_tik["ticket_id"] == 11800
        assert router_logic.get_session(sess_unlimited).estado == EstadoTicket.IDLE
        print("  ✓ Ticket GLPI #11800 creado exitosamente")

    # -------------------------------------------------------------
    # PRUEBA 6: Cancelación Universal ('no')
    # -------------------------------------------------------------
    print("\n[PRUEBA 6] Cancelación Universal ('no')")
    sess_c = "sess_cancel_test"
    router_logic.reset_session(sess_c)
    await router_logic.procesar_mensaje("Necesito un técnico", session_id=sess_c)
    r_no = await router_logic.procesar_mensaje("no", session_id=sess_c)
    assert r_no["tipo"] == "CANCELADO"
    assert router_logic.get_session(sess_c).estado == EstadoTicket.IDLE
    print("  ✓ Rechazo con 'no' reseteó la sesión a IDLE")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE (100% OK)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
