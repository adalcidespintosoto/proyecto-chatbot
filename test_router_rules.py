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
    print("VALIDACIÓN DE ASOCIACIÓN CONCEPTUAL Y RECUPERACIÓN (k=6, PROMPT CALIBRADO)")
    print("=" * 70)

    # -------------------------------------------------------------
    # PRUEBA 1: Verificación de Directrices del System Prompt Calibrado
    # -------------------------------------------------------------
    print("\n[PRUEBA 1] Directrices de Respuesta en System Prompt")
    assert "DIRECTRICES DE RESPUESTA:" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "dificultades de acceso (datos incorrectos, olvido de contraseña, bloqueo de usuario, problemas para entrar al portal o correo)" in STRICT_SYSTEM_PROMPT_TEMPLATE
    assert "UTILIZA esos pasos para guiar al usuario" in STRICT_SYSTEM_PROMPT_TEMPLATE
    print("  ✓ System prompt calibrado con directrices explícitas para problemas de acceso y credenciales")

    # -------------------------------------------------------------
    # PRUEBA 2: Búsqueda RAG con k=6 y Consulta Expandida
    # -------------------------------------------------------------
    print("\n[PRUEBA 2] Búsqueda RAG con k=6")
    mock_vs = MagicMock()
    doc_portal = Document(
        page_content="Pasos para restablecer clave en el portal estudiantil...",
        metadata={"source": "P-GT-11_Portales.pdf"}
    )
    mock_vs.similarity_search_with_relevance_scores.return_value = [(doc_portal, 0.78)]

    with patch.object(rag_service, "_vector_store", mock_vs), \
         patch("httpx.AsyncClient.post", new=AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"message": {"content": "Para ingresar al portal estudiantil..."}}))):

        res = await rag_service.answer_query("no puedo entrar al portal y dice datos incorrectos")
        
        # Verificar que similarity_search_with_relevance_scores fue llamado con k=6
        call_kwargs = mock_vs.similarity_search_with_relevance_scores.call_args[1]
        assert call_kwargs.get("k") == 6, f"Esperado k=6 pero fue {call_kwargs.get('k')}"
        assert res["has_context"] is True
        assert "P-GT-11_Portales.pdf" in res["sources"]
        print("  ✓ Búsqueda vectorial ejecutada con k=6 y recuperación semántica exitosa")

    # -------------------------------------------------------------
    # PRUEBA 3: Normalizador Léxico
    # -------------------------------------------------------------
    print("\n[PRUEBA 3] Normalización y Expansión Léxica")
    q1 = "no me coge la clave en el portal de la u y dice datos incorrectos"
    exp1 = normalize_and_expand_query(q1)
    assert "instructivo portales estudiantes" in exp1
    assert "problemas de acceso restablecimiento de contraseña" in exp1
    print("  ✓ Jerga estudiantil normalizada y expandida correctamente")

    # -------------------------------------------------------------
    # PRUEBA 4: Discriminación Estricta de Fallas vs Préstamos
    # -------------------------------------------------------------
    print("\n[PRUEBA 4] Discriminación Estricta")
    assert RouterLogic.is_equipment_request("quiero solicitar un pc como lo hago")
    assert not RouterLogic.is_equipment_request("no me coge la clave en el portal de la u y dice datos incorrectos")
    assert not RouterLogic.is_equipment_request("el cargador del portatil tiene mal contacto y me toca moverle el cable")
    print("  ✓ Discriminación estricta de solicitudes vs fallas verificada")

    # -------------------------------------------------------------
    # PRUEBA 5: Cancelación Universal
    # -------------------------------------------------------------
    print("\n[PRUEBA 5] Cancelación Universal ('no')")
    sess_c = "sess_cancel_test"
    router_logic.reset_session(sess_c)
    await router_logic.procesar_mensaje("Necesito un técnico", session_id=sess_c)
    assert router_logic.get_session(sess_c).estado == EstadoTicket.OFRECIENDO_RADICACION

    r_no = await router_logic.procesar_mensaje("no", session_id=sess_c)
    assert r_no["tipo"] == "CANCELADO"
    assert router_logic.get_session(sess_c).estado == EstadoTicket.IDLE
    print("  ✓ Rechazo con 'no' reseteó la sesión a IDLE")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE (100% OK)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
