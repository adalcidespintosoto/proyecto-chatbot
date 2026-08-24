import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.documents import Document

from app.services.router_logic import router_logic, RouterLogic, EstadoTicket
from app.services.rag_service import rag_service, STRICT_SYSTEM_PROMPT_TEMPLATE

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def run_tests():
    print("=" * 70)
    print("VALIDACIÓN DE RESTAURACIÓN DE DIRECTRICES Y COMPORTAMIENTO CONVERSACIONAL")
    print("=" * 70)

    # -------------------------------------------------------------
    # PRUEBA 1: Verificación del System Prompt Restaurado
    # -------------------------------------------------------------
    print("\n[PRUEBA 1] System Prompt Estándar Restaurado")
    assert "Eres UniMon, el Asistente Virtual Oficial de Soporte Técnico y Gestión de TI de la Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta)" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "Seven, Kactus, Portal de Bienestar, Aula Extendida, Correo Institucional, carnetización/App Unisimon" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "No menciones términos inventados como 'Canal 1' o 'Canal 2'" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "{context}" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "{query}" in STRICT_SYSTEM_PROMPT_TEMPLATE
    print("  ✓ System Prompt estándar institucional verificado correctamente")

    # -------------------------------------------------------------
    # PRUEBA 2: Umbral de Similitud RAG (relevance_score >= 0.68)
    # -------------------------------------------------------------
    print("\n[PRUEBA 2] Umbral de Similitud RAG")
    mock_vs = MagicMock()
    doc_baja_similitud = Document(page_content="Fragmento irrelevante", metadata={"source": "Doc_Irrelevante.pdf"})
    mock_vs.similarity_search_with_relevance_scores.return_value = [
        (doc_baja_similitud, 0.52),
        (doc_baja_similitud, 0.61)
    ]

    with patch.object(rag_service, "_vector_store", mock_vs), \
         patch("httpx.AsyncClient.post", new=AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"message": {"content": "Respuesta institucional base."}}))):
        
        res_below = await rag_service.query_rag("Consulta general")
        assert res_below["retrieved_chunks"] == 0
        assert res_below["sources"] == []
        print("  ✓ Documentos con score < 0.68 descartados y sources=[]")

    doc_alta_similitud = Document(page_content="Fragmento sobre Seven", metadata={"source": "P-GT-11_Seven.pdf", "page": 1})
    mock_vs.similarity_search_with_relevance_scores.return_value = [
        (doc_alta_similitud, 0.85)
    ]

    with patch.object(rag_service, "_vector_store", mock_vs), \
         patch("httpx.AsyncClient.post", new=AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"message": {"content": "Respuesta con contexto Seven."}}))):
        
        res_above = await rag_service.query_rag("¿Cómo gestionar incidencias en Seven?")
        assert res_above["retrieved_chunks"] == 1
        assert "P-GT-11_Seven.pdf" in res_above["sources"]
        print("  ✓ Documento con score >= 0.68 incluido correctamente en sources")

    # -------------------------------------------------------------
    # PRUEBA 3: Flujo de Cancelación Universal en Radicación
    # -------------------------------------------------------------
    print("\n[PRUEBA 3] Flujo de Cancelación Universal")
    sess_c = "sess_cancel_test"
    router_logic.reset_session(sess_c)
    await router_logic.procesar_mensaje("Quiero radicar un ticket", session_id=sess_c)
    await router_logic.procesar_mensaje("sí", session_id=sess_c) # PIDIENDO_NOMBRE
    r_cancel = await router_logic.procesar_mensaje("cancelar", session_id=sess_c)
    assert r_cancel["tipo"] == "CANCELADO"
    assert "Entendido, he cancelado el proceso de radicación" in r_cancel["mensaje"]
    assert router_logic.get_session(sess_c).estado == EstadoTicket.IDLE
    print("  ✓ Cancelación exitosa y reseteo a IDLE")

    # -------------------------------------------------------------
    # PRUEBA 4: Secuencia de Radicación en 3 Pasos
    # -------------------------------------------------------------
    print("\n[PRUEBA 4] Secuencia de Radicación en 3 Pasos")
    sess_seq = "sess_seq_test"
    router_logic.reset_session(sess_seq)

    await router_logic.procesar_mensaje("Necesito un técnico presencial", session_id=sess_seq)
    r_conf = await router_logic.procesar_mensaje("sí por favor", session_id=sess_seq)
    assert r_conf["tipo"] == "RADICANDO_TICKET"
    assert router_logic.get_session(sess_seq).estado == EstadoTicket.PIDIENDO_NOMBRE

    # Paso 1: Nombre
    r_nom = await router_logic.procesar_mensaje("Alfonso López Michelsen", session_id=sess_seq)
    assert r_nom["tipo"] == "RADICANDO_TICKET"
    assert router_logic.get_session(sess_seq).estado == EstadoTicket.PIDIENDO_CORREO

    # Paso 2: Correo
    r_cor = await router_logic.procesar_mensaje("alfonso.lopez@unisimon.edu.co", session_id=sess_seq)
    assert r_cor["tipo"] == "RADICANDO_TICKET"
    assert router_logic.get_session(sess_seq).estado == EstadoTicket.PIDIENDO_DESCRIPCION

    # Paso 3: Descripción -> Radicación
    desc_txt = "Falla general en el acceso a la plataforma Seven durante cierre contable."
    with patch("app.services.router_logic.glpi_client.crear_ticket", new=AsyncMock(return_value={"ticket_id": 10001, "status": "success"})):
        r_rad = await router_logic.procesar_mensaje(desc_txt, session_id=sess_seq)
        assert r_rad["tipo"] == "TICKET_CREADO"
        assert r_rad["ticket_id"] == 10001
        assert "Alfonso López Michelsen" in r_rad["mensaje"]
        assert "alfonso.lopez@unisimon.edu.co" in r_rad["mensaje"]
        print("  ✓ Secuencia de 3 pasos y radicación en GLPI (#10001) completada con éxito")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE (100% OK)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
