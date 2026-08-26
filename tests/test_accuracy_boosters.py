"""
Tests automatizados para los módulos de aprendizaje y asertividad de UniMon:
- Semantic Golden Cache (save/retrieve/threshold)
- Query Expansion LLM (formatting/fallback)
- Cross-Encoder Reranker (prioritization/fallback)
- Integración de feedback RESOLVED con Golden Cache
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from types import SimpleNamespace


# =============================================================================
# Test 1: Golden Cache — Guardar y Recuperar
# =============================================================================
class TestGoldenCache:
    """Tests para el servicio de Semantic Golden Cache."""

    def test_golden_cache_save_and_retrieve(self, tmp_path):
        """Valida que un caso guardado se pueda recuperar con similitud >= 0.90."""
        # Patchear la ruta de ChromaDB a un directorio temporal
        with patch("app.services.golden_cache_service.CHROMA_PATH", str(tmp_path)):
            # Forzar reinicialización de singleton
            import app.services.golden_cache_service as gc
            gc._golden_collection = None

            # Guardar un caso validado
            saved = gc.save_golden_case(
                session_id="test_session_001",
                user_query="¿Cómo cambio la contraseña del portal de estudiantes?",
                bot_response="Para cambiar tu contraseña del portal, ingresa a https://unisimon.edu.co, selecciona 'Olvidé mi contraseña' y sigue los pasos.",
                role="estudiante"
            )
            assert saved is True

            # Buscar con la misma consulta (debería dar similitud ~1.0)
            result = gc.search_golden_case(
                "¿Cómo cambio la contraseña del portal de estudiantes?"
            )
            assert result is not None
            prev_query, prev_response, similarity = result
            assert similarity >= 0.90
            assert "contraseña" in prev_query.lower()
            assert "portal" in prev_response.lower()

    def test_golden_cache_no_match_below_threshold(self, tmp_path):
        """Valida que consultas disímiles NO retornen falsos positivos."""
        with patch("app.services.golden_cache_service.CHROMA_PATH", str(tmp_path)):
            import app.services.golden_cache_service as gc
            gc._golden_collection = None

            # Guardar un caso sobre contraseñas
            gc.save_golden_case(
                session_id="test_session_002",
                user_query="¿Cómo cambio la contraseña del portal?",
                bot_response="Ingresa al portal y selecciona 'Olvidé mi contraseña'.",
                role="estudiante"
            )

            # Buscar algo completamente diferente
            result = gc.search_golden_case(
                "¿Dónde queda el laboratorio de química orgánica?",
                threshold=0.90
            )
            # No debería haber match (la consulta es semánticamente muy diferente)
            assert result is None

    def test_golden_cache_rejects_empty_query(self, tmp_path):
        """Valida que no se guarden consultas vacías o muy cortas."""
        with patch("app.services.golden_cache_service.CHROMA_PATH", str(tmp_path)):
            import app.services.golden_cache_service as gc
            gc._golden_collection = None

            saved = gc.save_golden_case(
                session_id="test_short",
                user_query="ok",
                bot_response="respuesta",
                role="general"
            )
            assert saved is False


# =============================================================================
# Test 2: Query Expansion LLM
# =============================================================================
class TestQueryExpansion:
    """Tests para la expansión de consultas con LLM."""

    def test_query_expansion_formatting(self):
        """Valida que la expansión LLM devuelva términos institucionales concisos."""
        from app.services.rag_service import expand_and_normalize_query_llm

        # Simular una respuesta exitosa de Ollama
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Procedimiento para restablecer contraseña del portal institucional de estudiantes"
        }

        with patch("app.services.rag_service.httpx.post", return_value=mock_response):
            result = expand_and_normalize_query_llm(
                "no me acuerdo de mi clave del portal",
                user_role="estudiante"
            )
            assert result != "no me acuerdo de mi clave del portal"
            assert len(result) > 10
            assert "contraseña" in result.lower() or "portal" in result.lower() or "restablecer" in result.lower()

    def test_query_expansion_fallback_on_error(self):
        """Valida que si Ollama falla, retorna la consulta original."""
        from app.services.rag_service import expand_and_normalize_query_llm

        with patch("app.services.rag_service.httpx.post", side_effect=Exception("Connection refused")):
            result = expand_and_normalize_query_llm(
                "no me entra a teams",
                user_role="estudiante"
            )
            assert result == "no me entra a teams"

    def test_query_expansion_fallback_on_empty_response(self):
        """Valida que respuestas vacías de Ollama no reemplacen el query original."""
        from app.services.rag_service import expand_and_normalize_query_llm

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": ""}

        with patch("app.services.rag_service.httpx.post", return_value=mock_response):
            result = expand_and_normalize_query_llm(
                "como subo notas al sistema",
                user_role="profesor"
            )
            assert result == "como subo notas al sistema"


# =============================================================================
# Test 3: Cross-Encoder Reranker
# =============================================================================
class TestReranker:
    """Tests para el Cross-Encoder Reranker."""

    def test_reranker_prioritization(self):
        """Valida que el Cross-Encoder priorice fragmentos relevantes."""
        from app.services.rag_service import rerank_chunks

        # Crear documentos mock simulando LangChain Document
        doc_relevant = SimpleNamespace(
            page_content="Para restablecer la contraseña del portal institucional, ingrese a https://unisimon.edu.co y seleccione 'Olvidé mi contraseña'.",
            metadata={"source": "portal_estudiantes.pdf"}
        )
        doc_irrelevant = SimpleNamespace(
            page_content="El programa de mantenimiento preventivo de equipos se ejecuta trimestralmente según procedimiento P-GT-01.",
            metadata={"source": "mantenimiento.pdf"}
        )
        doc_partial = SimpleNamespace(
            page_content="Las contraseñas de los sistemas institucionales deben cumplir con la política de seguridad vigente.",
            metadata={"source": "politica_seguridad.pdf"}
        )
        doc_noise = SimpleNamespace(
            page_content="El comité de investigación se reúne el primer lunes de cada mes para revisar los avances.",
            metadata={"source": "comite.pdf"}
        )

        # Simular retrieval con scores de ChromaDB
        retrieved = [
            (doc_irrelevant, 0.55),
            (doc_noise, 0.52),
            (doc_relevant, 0.60),
            (doc_partial, 0.58),
        ]

        # Mockear el cross-encoder para simular reranking
        mock_reranker = MagicMock()
        mock_reranker.predict.return_value = [0.1, 0.05, 0.95, 0.6]

        with patch("app.services.rag_service.get_reranker", return_value=mock_reranker):
            result = rerank_chunks("¿Cómo restablezco mi contraseña del portal?", retrieved, top_k=3)

            assert len(result) == 3
            # El documento más relevante semánticamente debe estar primero
            top_doc = result[0][0]
            assert "contraseña" in top_doc.page_content.lower() or "portal" in top_doc.page_content.lower()

    def test_reranker_fallback_without_model(self):
        """Valida que sin modelo CrossEncoder, retorna los primeros top_k nativos."""
        from app.services.rag_service import rerank_chunks

        doc1 = SimpleNamespace(page_content="Documento 1", metadata={})
        doc2 = SimpleNamespace(page_content="Documento 2", metadata={})
        doc3 = SimpleNamespace(page_content="Documento 3", metadata={})
        doc4 = SimpleNamespace(page_content="Documento 4", metadata={})

        retrieved = [(doc1, 0.8), (doc2, 0.7), (doc3, 0.6), (doc4, 0.5)]

        with patch("app.services.rag_service.get_reranker", return_value=None):
            result = rerank_chunks("test query", retrieved, top_k=2)
            assert len(result) == 2
            assert result[0][0].page_content == "Documento 1"
            assert result[1][0].page_content == "Documento 2"

    def test_reranker_passthrough_small_list(self):
        """Valida que listas menores o iguales a top_k pasen sin reranking."""
        from app.services.rag_service import rerank_chunks

        doc1 = SimpleNamespace(page_content="Documento único", metadata={})
        retrieved = [(doc1, 0.9)]

        result = rerank_chunks("test query", retrieved, top_k=3)
        assert len(result) == 1
        assert result[0][0].page_content == "Documento único"


# =============================================================================
# Test 4: Feedback RESOLVED dispara Golden Cache save
# =============================================================================
class TestFeedbackGoldenIntegration:
    """Tests para la integración del feedback con el Golden Cache."""

    @pytest.mark.asyncio
    async def test_feedback_resolved_triggers_golden_save(self):
        """Valida que el clic en '✅ Sí, me funcionó' guarde en golden_resolved_qa."""
        from app.services.router_logic import RouterLogic, ticket_sessions, TicketSession, EstadoTicket

        session_id = "test_feedback_golden_001"
        session = TicketSession(
            session_id=session_id,
            estado=EstadoTicket.DIAGNOSTICO,
            user_role="estudiante",
            last_user_query="¿Cómo cambio mi contraseña del portal?",
            last_bot_response="Ingresa al portal, selecciona 'Olvidé mi contraseña' y sigue los pasos.",
            intentos_diagnostico=1,
            diagnosis_attempts=1,
            falla="contraseña portal"
        )
        ticket_sessions[session_id] = session

        with patch("app.services.router_logic.save_golden_case") as mock_save:
            result = await RouterLogic.procesar_mensaje("RESOLVED", session_id)

            # Debe haber invocado save_golden_case
            mock_save.assert_called_once_with(
                session_id=session_id,
                user_query="¿Cómo cambio mi contraseña del portal?",
                bot_response="Ingresa al portal, selecciona 'Olvidé mi contraseña' y sigue los pasos.",
                role="estudiante"
            )
            # El resultado debe ser FINALIZADO
            assert result["tipo"] == "FINALIZADO"

        # Cleanup
        if session_id in ticket_sessions:
            del ticket_sessions[session_id]

    def test_conditional_si_in_query_does_not_trigger_ticket_escalation(self):
        """Valida que consultas con la conjunción condicional 'si' no se interpreten erróneamente como radicación."""
        from app.services.router_logic import RouterLogic

        query_with_si = "¿Cómo hago para saber cuál es mi usuario y activar mi correo si soy nuevo en la universidad?"
        assert RouterLogic.is_report_request(query_with_si) is False

        query_with_si_2 = "¿Qué debo hacer si se me bloqueó la cuenta de teams?"
        assert RouterLogic.is_report_request(query_with_si_2) is False

        # Confirmar que solicitudes reales de ticket sí activan is_report_request
        assert RouterLogic.is_report_request("vamos a reportar") is True
        assert RouterLogic.is_report_request("radicar el caso") is True
        assert RouterLogic.is_report_request("crear ticket") is True

