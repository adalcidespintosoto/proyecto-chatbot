import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.documents import Document

from app.services.router_logic import router_logic, RouterLogic, EstadoTicket
from app.services.rag_service import rag_service, STRICT_SYSTEM_PROMPT_TEMPLATE, MENSAJE_NO_DOCUMENTADO

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def run_tests():
    print("=" * 70)
    print("VALIDACIÓN DE CERO ALUCINACIONES Y RESPUESTA ESTRICTA ANTE FALTA DE DOCUMENTOS")
    print("=" * 70)

    # -------------------------------------------------------------
    # PRUEBA 1: System Prompt Estricto Actualizado
    # -------------------------------------------------------------
    print("\n[PRUEBA 1] Verificación de Reglas de Oro en System Prompt")
    assert "REGLAS DE ORO OBLIGATORIAS:" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "Responde ÚNICA Y EXCLUSIVAMENTE con los pasos explícitos presentes en el contexto institucional." in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "NO inventes rutas ni módulos en Seven o Kactus." in STRICT_SYSTEM_PROMPT_TEMPLATE
    print("  ✓ System prompt contiene las Reglas de Oro obligatorias contra alucinaciones")

    # -------------------------------------------------------------
    # PRUEBA 2: Cero Alucinaciones cuando No Existen Documentos Relevantes
    # -------------------------------------------------------------
    print("\n[PRUEBA 2] Búsqueda RAG sin Documentos Relevantes (score < 0.68)")
    mock_vs_empty = MagicMock()
    # Simular que los fragmentos no superan 0.68
    doc_bajo = Document(page_content="Texto irrelevante", metadata={"source": "Doc.pdf"})
    mock_vs_empty.similarity_search_with_relevance_scores.return_value = [(doc_bajo, 0.45)]

    with patch.object(rag_service, "_vector_store", mock_vs_empty), \
         patch("httpx.AsyncClient.post", new=AsyncMock()) as mock_http_post:

        res_no_doc = await rag_service.answer_query("¿Cómo configuro un dron en la universidad?")
        
        # El LLM (Ollama) NO DEBE SER INVOCADO
        mock_http_post.assert_not_called()
        assert res_no_doc["response"] == MENSAJE_NO_DOCUMENTADO
        assert res_no_doc["sources"] == []
        assert res_no_doc["retrieved_chunks"] == 0
        assert res_no_doc["has_context"] is False
        print("  ✓ Ollama NO fue invocado y se retornó MENSAJE_NO_DOCUMENTADO institucional")

    # -------------------------------------------------------------
    # PRUEBA 3: Enrutamiento en RouterLogic ante Falta de Documentos (OFRECIENDO_RADICACION)
    # -------------------------------------------------------------
    print("\n[PRUEBA 3] Transición de Estado a OFRECIENDO_RADICACION ante Falta de Documentos")
    sess_nodoc = "sess_no_doc_test"
    router_logic.reset_session(sess_nodoc)

    with patch.object(rag_service, "answer_query", new=AsyncMock(return_value={
        "response": MENSAJE_NO_DOCUMENTADO,
        "sources": [],
        "source": "unimon_no_doc_fallback",
        "has_context": False,
        "retrieved_chunks": 0
    })):
        r_nodoc = await router_logic.procesar_mensaje("Necesito cambiar el cargador dañado del portátil", session_id=sess_nodoc)
        s_nodoc = router_logic.get_session(sess_nodoc)

        assert r_nodoc["tipo"] == "OFRECIENDO_RADICACION"
        assert s_nodoc.estado == EstadoTicket.OFRECIENDO_RADICACION
        assert "No dispongo de un instructivo o procedimiento institucional documentado" in r_nodoc["mensaje"]
        assert "solicitudcomputo@unisimon.edu.co" in r_nodoc["mensaje"]
        assert "¿O prefieres que radique el caso de soporte técnico directamente en GLPI por ti ahora mismo?" in r_nodoc["mensaje"]
        print("  ✓ RouterLogic transicionó limpiamente a OFRECIENDO_RADICACION entregando canales y confirmación")

    # -------------------------------------------------------------
    # PRUEBA 4: Flujo Completo: Consulta No Documentada -> Confirmación -> Radicación en GLPI
    # -------------------------------------------------------------
    print("\n[PRUEBA 4] Flujo Completo de Radicación tras Caso No Documentado")
    sess_flow = "sess_flow_nodoc_to_ticket"
    router_logic.reset_session(sess_flow)

    # 1. Consulta sin manual documentado
    with patch.object(rag_service, "answer_query", new=AsyncMock(return_value={
        "response": MENSAJE_NO_DOCUMENTADO,
        "sources": [],
        "has_context": False,
        "retrieved_chunks": 0
    })):
        await router_logic.procesar_mensaje("Cargador de laptop quemado en bloque 3", session_id=sess_flow)
        assert router_logic.get_session(sess_flow).estado == EstadoTicket.OFRECIENDO_RADICACION

    # 2. Usuario dice "sí" -> Solicita Nombre
    r_conf = await router_logic.procesar_mensaje("sí por favor", session_id=sess_flow)
    assert r_conf["tipo"] == "RADICANDO_TICKET"
    assert router_logic.get_session(sess_flow).estado == EstadoTicket.PIDIENDO_NOMBRE

    # 3. Nombre
    r_name = await router_logic.procesar_mensaje("Carlos Julio Barreto", session_id=sess_flow)
    assert router_logic.get_session(sess_flow).estado == EstadoTicket.PIDIENDO_CORREO

    # 4. Correo
    r_email = await router_logic.procesar_mensaje("carlos.barreto@unisimon.edu.co", session_id=sess_flow)
    assert router_logic.get_session(sess_flow).estado == EstadoTicket.PIDIENDO_DESCRIPCION

    # 5. Descripción -> Ticket GLPI
    with patch("app.services.router_logic.glpi_client.crear_ticket", new=AsyncMock(return_value={"ticket_id": 10555, "status": "success"})):
        r_ticket = await router_logic.procesar_mensaje("El cargador del portátil HP asignado en bloque 3 piso 2 echó chispas y no enciende", session_id=sess_flow)
        assert r_ticket["tipo"] == "TICKET_CREADO"
        assert r_ticket["ticket_id"] == 10555
        assert "Carlos Julio Barreto" in r_ticket["mensaje"]
        assert "carlos.barreto@unisimon.edu.co" in r_ticket["mensaje"]
        print("  ✓ Ticket GLPI #10555 radicado exitosamente a partir de caso sin manual")

    # -------------------------------------------------------------
    # PRUEBA 5: Discriminación Estricta: Fallas vs Préstamos
    # -------------------------------------------------------------
    print("\n[PRUEBA 5] Discriminación Estricta de Fallas vs Préstamos")
    assert not RouterLogic.is_equipment_request("Tengo un problema con el computador de la sala 2")
    assert not RouterLogic.is_equipment_request("Mi portatil está muy lento y da pantalla azul")
    assert RouterLogic.is_equipment_request("Quiero solicitar un microfono para un evento")
    assert RouterLogic.is_equipment_request("Necesito que me presten una tablet")
    print("  ✓ Discriminación estricta verificada")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE (100% OK)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
