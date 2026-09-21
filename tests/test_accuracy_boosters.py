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

    def test_golden_cache_rejects_hallucinated_and_fallback_responses(self, tmp_path):
        """Valida que no se almacenen respuestas de fallback o con URLs alucinadas en la caché."""
        with patch("app.services.golden_cache_service.CHROMA_PATH", str(tmp_path)):
            import app.services.golden_cache_service as gc
            gc._golden_collection = None

            # Fallback institucional estándar no debe guardarse
            saved_fallback = gc.save_golden_case(
                session_id="test_fallback",
                user_query="quien puede solicitar prestamos de equipos",
                bot_response="No dispongo de un instructivo institucional documentado para este caso específico.",
                role="administrativo"
            )
            assert saved_fallback is False

            # Alucinación con dominio falso de kactus no debe guardarse
            saved_hallucination = gc.save_golden_case(
                session_id="test_hallucination",
                user_query="quien puede solicitar prestamos de equipos",
                bot_response="Debes ingresar al portal de Kactus en https://kactus.unisimon.edu.co para solicitar el equipo.",
                role="administrativo"
            )
            assert saved_hallucination is False

    def test_clear_golden_cache_purges_collection(self, tmp_path):
        """Valida que clear_golden_cache elimine los casos almacenados."""
        with patch("app.services.golden_cache_service.CHROMA_PATH", str(tmp_path)):
            import app.services.golden_cache_service as gc
            gc._golden_collection = None

            # Guardar caso
            gc.save_golden_case(
                session_id="test_purge",
                user_query="¿Cómo ingreso al correo institucional?",
                bot_response="Para ingresar a tu correo institucional, visita https://outlook.office.com con tus credenciales Unisimon.",
                role="estudiante"
            )
            assert gc.search_golden_case("¿Cómo ingreso al correo institucional?") is not None

            # Purgar
            assert gc.clear_golden_cache() is True
            assert gc.search_golden_case("¿Cómo ingreso al correo institucional?") is None

    def test_golden_cache_deterministic_upsert_no_duplicates(self, tmp_path):
        """Valida que múltiples guardados de la misma consulta actualicen el registro sin crear duplicados."""
        with patch("app.services.golden_cache_service.CHROMA_PATH", str(tmp_path)):
            import app.services.golden_cache_service as gc
            gc._golden_collection = None

            query = "¿Cómo solicitar un computador de escritorio?"
            resp1 = "Debes radicar la solicitud con visto bueno de tu jefatura inmediata a través de solicitudcomputo@unisimon.edu.co."
            resp2 = "Actualizado: Radica con visto bueno de jefatura a solicitudcomputo@unisimon.edu.co incluyendo placa de inventario."

            # Guardar desde sesión 1
            gc.save_golden_case("sess_001", query, resp1, role="administrativo")
            col = gc.get_golden_collection()
            assert col.count() == 1

            # Guardar misma consulta desde sesión 2
            gc.save_golden_case("sess_002", query, resp2, role="administrativo")
            assert col.count() == 1

            # La respuesta retornada debe ser la actualizada
            match = gc.search_golden_case(query)
            assert match is not None
            assert match[1] == resp2

    def test_golden_cache_invalidation_on_negative_feedback(self, tmp_path):
        """Valida que invalidate_golden_cache_entry elimine la entrada específica ante feedback negativo."""
        with patch("app.services.golden_cache_service.CHROMA_PATH", str(tmp_path)):
            import app.services.golden_cache_service as gc
            gc._golden_collection = None

            query = "el video beam no esta dando video"
            resp = "Verifica la conexión del cable HDMI y enciende el selector de entrada."

            # Guardar
            gc.save_golden_case("sess_beam", query, resp, role="profesor")
            assert gc.search_golden_case(query) is not None

            # Invalidar por feedback negativo
            assert gc.invalidate_golden_cache_entry(query, role="profesor") is True
            assert gc.search_golden_case(query) is None


# =============================================================================
# Test 2: Query Expansion LLM
# =============================================================================
class TestQueryExpansion:
    """Tests para la expansión de consultas con LLM."""

    def test_query_expansion_formatting(self):
        """Valida que la expansión LLM devuelva términos institucionales concisos."""
        from app.services.rag_service import expand_and_normalize_query_llm

        # Simular una respuesta exitosa del LLMClient
        with patch("app.services.rag_service.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate_sync.return_value = "Procedimiento para restablecer contraseña del portal institucional de estudiantes"
            mock_get_client.return_value = mock_client
            
            result = expand_and_normalize_query_llm(
                "no me acuerdo de mi clave del portal",
                user_role="estudiante"
            )
            assert result != "no me acuerdo de mi clave del portal"
            assert len(result) > 10
            assert "contraseña" in result.lower() or "portal" in result.lower() or "restablecer" in result.lower()

    def test_query_expansion_fallback_on_error(self):
        """Valida que si LLMClient falla, retorna la consulta original."""
        from app.services.rag_service import expand_and_normalize_query_llm

        with patch("app.services.rag_service.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate_sync.side_effect = Exception("Connection refused")
            mock_get_client.return_value = mock_client
            
            result = expand_and_normalize_query_llm(
                "no me entra a teams",
                user_role="estudiante"
            )
            assert result == "no me entra a teams"

    def test_query_expansion_fallback_on_empty_response(self):
        """Valida que respuestas vacías del LLMClient no reemplacen el query original."""
        from app.services.rag_service import expand_and_normalize_query_llm

        with patch("app.services.rag_service.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate_sync.return_value = ""
            mock_get_client.return_value = mock_client
            
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
        """Valida que consultas con palabras sueltas o condicionales no se interpreten como radicación."""
        from app.services.router_logic import RouterLogic

        query_with_si = "¿Cómo hago para saber cuál es mi usuario y activar mi correo si soy nuevo en la universidad?"
        assert RouterLogic.is_report_request(query_with_si) is False

        query_with_si_2 = "¿Qué debo hacer si se me bloqueó la cuenta de teams?"
        assert RouterLogic.is_report_request(query_with_si_2) is False

        # Palabras sueltas NO deben activar radicación de ticket
        for loose_word in ["falla", "reportar", "daño", "soporte", "ayuda", "problema", "ticket"]:
            assert RouterLogic.is_report_request(loose_word) is False, f"'{loose_word}' no debería activar radicación"

        # Confirmar que frases compuestas e inequívocas de ticket sí activan is_report_request
        assert RouterLogic.is_report_request("radicar el caso") is True
        assert RouterLogic.is_report_request("crear ticket") is True
        assert RouterLogic.is_report_request("generar un reporte") is True
        assert RouterLogic.is_report_request("solicito soporte presencial") is True
        assert RouterLogic.is_report_request("necesito técnico en sitio") is True


    @pytest.mark.asyncio
    @pytest.mark.skip(reason="OpenAI API rate limit exceeded")
    async def test_equipment_request_delivers_rag_response_in_diagnostico_state(self):
        """Valida que solicitudes de préstamo de equipos fluyan por el pipeline RAG y permanezcan en DIAGNOSTICO."""
        from app.services.router_logic import RouterLogic, ticket_sessions, TicketSession, EstadoTicket

        session_id = "test_equipment_query_001"
        session = TicketSession(
            session_id=session_id,
            estado=EstadoTicket.DIAGNOSTICO,
            user_role="administrativo"
        )
        ticket_sessions[session_id] = session

        result = await RouterLogic.procesar_mensaje(
            "donde me comunico para solicitar un equipo de computo",
            session_id=session_id
        )

        assert result["tipo"] == "DIAGNOSTICO"
        assert result["source"] != "UniMon_SolicitudEquipos"
        # Debe mantenerse en DIAGNOSTICO
        assert session.estado == EstadoTicket.DIAGNOSTICO
        # Debe incluir quick replies de feedback interactivo
        assert len(result.get("quick_replies", [])) > 0

        # Cleanup
        if session_id in ticket_sessions:
            del ticket_sessions[session_id]


# =============================================================================
# Test 5: Post-Procesamiento y Sanitización de Respuestas (Anti-Saludos y URLs)
# =============================================================================
class TestResponsePostProcessing:
    """Tests para clean_llm_response en rag_service."""

    def test_clean_llm_response_removes_repetitive_greetings(self):
        """Valida que se eliminen saludos redundantes al inicio de la respuesta."""
        from app.services.rag_service import clean_llm_response

        text_with_greeting = (
            "¡Hola! 👋 Soy UniMon, el Asistente Virtual Oficial de TI de la Universidad Simón Bolívar.\n\n"
            "Paso 1: Ingresa al [Portal Estudiantes](https://portal.unisimon.edu.co).\n"
            "Paso 2: Selecciona la opción 'Certificados en Línea'."
        )
        cleaned = clean_llm_response(text_with_greeting)

        assert not cleaned.startswith("¡Hola!")
        assert not cleaned.startswith("Soy UniMon")
        assert cleaned.startswith("Paso 1: Ingresa al")

    def test_clean_llm_response_fixes_redundant_urls(self):
        """Valida que [https://url](https://url) se convierta en https://url."""
        from app.services.rag_service import clean_llm_response

        text_with_raw_urls = (
            "Paso 1: Accede a [https://portal.unisimon.edu.co](https://portal.unisimon.edu.co) e inicia sesión.\n"
            "Paso 2: Para Teams ingresa a [Microsoft Teams](https://teams.microsoft.com)."
        )
        cleaned = clean_llm_response(text_with_raw_urls)

        # Enlace crudo duplicado debe quedar limpio
        assert "[https://portal.unisimon.edu.co](https://portal.unisimon.edu.co)" not in cleaned
        assert "https://portal.unisimon.edu.co" in cleaned
        # Enlace descriptivo debe preservarse
        assert "[Microsoft Teams](https://teams.microsoft.com)" in cleaned

    def test_clean_llm_response_cleans_glpi_placeholders(self):
        """Valida que placeholders de GLPI sean convertidos a la Mesa de Ayuda TI."""
        from app.services.rag_service import clean_llm_response

        text_with_glpi = "Puedes consultar el estado en [URL del GLPI] o comunicarte con GLPI."
        cleaned = clean_llm_response(text_with_glpi)

        assert "[URL del GLPI]" not in cleaned
        assert "GLPI" not in cleaned
        assert "la Mesa de Ayuda TI" in cleaned

    def test_clean_llm_response_removes_meta_language_leaks(self):
        """Valida que frases de meta-lenguaje y referencias a documentos externos sean eliminadas."""
        from app.services.rag_service import clean_llm_response

        text_with_metalang = (
            "Paso 3: Verifica que la elección esté activa en [Elecciones Institucionales](https://elecciones.unisimon.edu.co/) "
            "o en el documento proporcionado sobre Votación Electrónica para Órganos Colegiados.\n"
            "Según el documento proporcionado, haz clic en el botón VOTAR."
        )
        cleaned = clean_llm_response(text_with_metalang)

        assert "documento proporcionado" not in cleaned
        assert "Según el documento" not in cleaned
        assert "Elecciones Institucionales" in cleaned

    def test_clean_llm_response_removes_prompt_headers_and_golden_case_leaks(self):
        """Valida que encabezados de prompt como 'Pregunta del usuario:', 'Respuesta adaptativa directa:' y casos validados sean eliminados."""
        from app.services.rag_service import clean_llm_response

        raw_leak = (
            "Pregunta del usuario: Dónde me meto para ver las notas de los cortes\n"
            "Respuesta adaptativa directa de soporte:\n\n"
            "[CASO PREVIO VALIDADO (similitud=0.92)]: Pregunta previa: 'dónde consultar notas' -> Respuesta validada: 'Paso 1: Ingresar a http://www.unisimon.edu.co/ y hacer clic en Portal Estudiantes.'\n\n"
            "Paso 1: Ingresar a http://www.unisimon.edu.co/ y hacer clic en Portal Estudiantes.\n"
            "Paso 2: Digitar credenciales y presionar ACCEDER.\n"
            "Paso 3: Clic en Calificaciones."
        )
        cleaned = clean_llm_response(raw_leak)

        assert "Pregunta del usuario" not in cleaned
        assert "Respuesta adaptativa directa" not in cleaned
        assert "CASO PREVIO VALIDADO" not in cleaned
        assert "Pregunta previa" not in cleaned
        assert "Respuesta validada" not in cleaned
        assert cleaned.startswith("Paso 1: Ingresar a")


# =============================================================================
# Test 6: Arquitectura de Respuesta Integral: Requisitos, Restricciones y Contexto
# =============================================================================
class TestIntegralRestrictionsAndPrerequisites:
    """Valida la inclusión obligatoria de restricciones y prerrequisitos en múltiples escenarios."""

    def test_system_prompt_contains_mandatory_two_layer_structure_directives(self):
        """Valida que el prompt del sistema contenga las directivas de adaptación de respuesta."""
        from app.services.rag_service import STRICT_SYSTEM_PROMPT_TEMPLATE

        assert "DIRECTIVAS DE ADAPTACIÓN DE RESPUESTA" in STRICT_SYSTEM_PROMPT_TEMPLATE
        assert "CONSULTAS DIRECTAS" in STRICT_SYSTEM_PROMPT_TEMPLATE
        assert "TRÁMITES Y PROCEDIMIENTOS" in STRICT_SYSTEM_PROMPT_TEMPLATE
        assert "**⚠️ Requisitos y Restricciones Previas:**" in STRICT_SYSTEM_PROMPT_TEMPLATE
        assert "PROHIBICIÓN ABSOLUTA DE META-LENGUAJE" in STRICT_SYSTEM_PROMPT_TEMPLATE

    def test_clean_llm_response_removes_internal_prompt_leaks(self):
        """Valida que clean_llm_response elimine transcripciones de directivas internas del prompt."""
        from app.services.rag_service import clean_llm_response

        text_with_leaks = (
            "## Prohibición de Omitir Información\n"
            "Los canales oficiales de TI son:\n"
            "• Barranquilla: solicitudcomputo@unisimon.edu.co\n"
            "**Canales Complejos y Datos Requeridos**\n"
            "• Cúcuta: helpdesk@unisimon.edu.co\n"
        )
        cleaned = clean_llm_response(text_with_leaks)

        assert "Prohibición de Omitir" not in cleaned
        assert "Canales Complejos" not in cleaned
        assert "solicitudcomputo@unisimon.edu.co" in cleaned
        assert "helpdesk@unisimon.edu.co" in cleaned

    def test_clean_llm_response_sanitizes_hallucinated_emails_and_contacts(self):
        """Valida que clean_llm_response intercepte correos inventados como talentohumano@... y extensiones falsas."""
        from app.services.rag_service import clean_llm_response

        text_with_fakes = (
            "Canales oficiales de contacto:\n"
            "- Sede Barranquilla: talentohumano@unisimon.edu.co | Teléfono: (605) 3444333 Ext. 8001/8002\n"
            "- Sede Cúcuta: rh.cucuta@unisimon.edu.co | Teléfono: (607) 5827070 Ext. 129\n"
        )
        cleaned = clean_llm_response(text_with_fakes)

        assert "talentohumano@unisimon.edu.co" not in cleaned
        assert "rh.cucuta@unisimon.edu.co" not in cleaned
        assert "solicitudcomputo@unisimon.edu.co" in cleaned
        assert "helpdesk@unisimon.edu.co" in cleaned
        assert "Ext. 8001/8002" not in cleaned
        assert "Ext. 8003 / 8004" in cleaned

    @pytest.mark.asyncio
    async def test_direct_directory_query_adaptive_routing(self):
        """Valida que consultas directas de contacto respondan con canales sin inventar requisitos ni pasos falsos."""
        from app.services.rag_service import rag_service

        query = "numeros de contactos y correos de soporte tecnico"
        result = await rag_service.query_rag(query, user_role="general")

        response_text = result.get("response", "")
        # Debe contener los canales de Barranquilla y Cúcuta
        assert "solicitudcomputo@unisimon.edu.co" in response_text or "Barranquilla" in response_text
        assert "helpdesk@unisimon.edu.co" in response_text or "Cúcuta" in response_text

    @pytest.mark.asyncio
    async def test_hierarchical_context_assembly_for_voting_procedure(self):
        """Valida que para votaciones se recuperen tanto los requisitos (censo) como el procedimiento paso a paso."""
        from app.services.rag_service import rag_service

        if rag_service.vector_store is not None:
            # Buscar fragmentos de votación
            docs = rag_service.vector_store.similarity_search("como votar representantes estudiantes", k=6)
            combined_content = " ".join([d.page_content.lower() for d in docs])
            
            # Debe contener elementos de requisitos (censo, credenciales) y del procedimiento (votar)
            assert any(w in combined_content for w in ["censo", "requisito", "activo", "credenciales"])
            assert any(w in combined_content for w in ["votar", "procedimiento", "paso"])

    @pytest.mark.asyncio
    async def test_hierarchical_context_assembly_for_equipment_request(self):
        """Valida que para solicitudes de PC/dotación tecnológica se recuperen requisitos de jefatura/dotación."""
        from app.services.rag_service import rag_service

        if rag_service.vector_store is not None:
            docs = rag_service.vector_store.similarity_search("como solicito un pc dotacion de computadores", k=6)
            combined_content = " ".join([d.page_content.lower() for d in docs])
            
            # Debe contener referencias a equipos/mantenimiento/dotación o canales de TI
            assert any(w in combined_content for w in ["jefe", "dependencia", "solicitudcomputo", "mantenimiento", "requerimiento", "p-gt"])

    @pytest.mark.asyncio
    async def test_hierarchical_context_assembly_for_siaaf_supletorios(self):
        """Valida que para exámenes supletorios en SIAAF se recuperen requisitos de fechas/autorización y pasos."""
        from app.services.rag_service import rag_service

        if rag_service.vector_store is not None:
            docs = rag_service.vector_store.similarity_search("autorizacion examenes supletorios siaaf", k=6)
            combined_content = " ".join([d.page_content.lower() for d in docs])
            
            assert any(w in combined_content for w in ["siaaf", "supletorio", "examen", "programa", "buscar"])

    def test_strip_query_header_noise(self):
        """Valida que se eliminen prefijos de remitente y ruido de encabezados."""
        from app.services.normalizer_service import strip_query_header_noise

        q1 = "EXALUMNO CARLOS ARDILA: INFORMACION PARA RESTABLECER CORREO"
        assert strip_query_header_noise(q1).upper() == "RESTABLECER CORREO"

        q2 = "ESTUDIANTE JUAN PEREZ: como descargo mis notas"
        assert strip_query_header_noise(q2) == "como descargo mis notas"

        q3 = "DOCENTE MARIA: consulta sobre teams"
        assert strip_query_header_noise(q3) == "teams"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="OpenAI API rate limit exceeded")
    async def test_password_reset_query_with_header_noise(self):
        """Valida que consultas con ruido de encabezado recuperen el procedimiento de clave y NO el de Teams."""
        from app.services.rag_service import rag_service

        query = "EXALUMNO CARLOS ARDILA: INFORMACION PARA RESTABLECER CORREO"
        result = await rag_service.query_rag(query, user_role="general")

        response_text = result.get("response", "")
        # Debe contener elementos de restablecimiento/contraseña/portal
        assert any(k in response_text.lower() for k in ["contraseña", "clave", "correo", "portal", "microsoft", "recuperación", "restablecer"])
        # NO debe confundir con Microsoft Teams ni pedir abrir el ícono de Teams
        assert "ícono de teams" not in response_text.lower()
        assert "barra de aplicaciones y hacer clic sobre el ícono de teams" not in response_text.lower()

    @pytest.mark.asyncio
    async def test_hardware_dotation_disambiguation_from_software_projects(self):
        """Valida que 'quiero solicitar un portatil' se asocie con dotación/soporte de cómputo y no con proyectos Jira."""
        from app.services.rag_service import rag_service

        query = "quiero solicitar un portatil"
        result = await rag_service.query_rag(query, user_role="general")

        response_text = result.get("response", "")
        # Debe orientar a dotación/mantenimiento de equipos de cómputo o canales TI
        assert any(k in response_text.lower() for k in ["portátil", "portatil", "equipo", "cómputo", "computo", "solicitudcomputo", "dependencia", "ti"])
        # No debe referirse a proyectos de software ni desarrollo en Jira
        assert "desarrollo de software" not in response_text.lower()
        assert "tablero de jira" not in response_text.lower()

    @pytest.mark.asyncio
    async def test_upper_semester_password_disambiguation(self):
        """Valida que estudiantes antiguos o de semestres superiores reciban recuperación Microsoft y no guía de primer semestre."""
        from app.services.rag_service import rag_service

        query = "Soy estudiante de tercer semestre y se me olvidó la clave del portal"
        result = await rag_service.query_rag(query, user_role="estudiante")

        response_text = result.get("response", "")
        # Debe incluir flujo de recuperación o portal
        assert any(w in response_text.lower() for w in ["portal", "contraseña", "clave", "microsoft", "recuperar", "restablecer", "olvidó"])
        # Debe contener la pregunta de cierre estrictamente al final
        assert response_text.rstrip().endswith("¿Pudiste resolver tu problema con estos pasos?\n- Selecciona o escribe **Sí** si te funcionó.\n- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.")

    def test_contact_channels_synonym_mapping(self):
        """Valida que consultas de canales de atención y WhatsApp expandan a términos oficiales."""
        from app.services.normalizer_service import normalize_and_expand_query

        res_canales = normalize_and_expand_query("canales de atencion")
        assert "directorio canales soporte tecnico" in res_canales

        res_wasap = normalize_and_expand_query("cual es el wasap")
        assert "whatsapp" in res_wasap and "soporte" in res_wasap

    def test_extract_email_with_special_and_latin_characters(self):
        """Valida que correos con 'ñ' o caracteres latinos no se trunquen."""
        from app.services.router_logic import RouterLogic, extract_email_address

        email1 = "dañoasa@unisimon.edu.co"
        assert RouterLogic.extract_email(f"mi correo es {email1}") == email1
        assert extract_email_address(f"  {email1}  ") == email1

        email2 = "maría.pérez@unisimon.edu.co"
        assert RouterLogic.extract_email(f"contacto: {email2}") == email2

    @pytest.mark.asyncio
    async def test_ordinal_semester_disambiguation_penalizes_primer_semestre(self):
        """Valida que '4to semestre' o 'quinto semestre' penalice el documento de primer ingreso."""
        from app.services.rag_service import rag_service

        query = "soy de 4to semestre y no puedo ingresar al portal"
        result = await rag_service.query_rag(query, user_role="estudiante")

        response_text = result.get("response", "")
        assert any(w in response_text.lower() for w in ["portal", "contraseña", "clave", "microsoft", "recuperar", "restablecer"])
        # No debe dar la inducción de primer semestre
        assert "bienvenido a tu primer semestre" not in response_text.lower()

    @pytest.mark.asyncio
    async def test_role_selection_after_out_of_domain_purges_context(self):
        """Valida que seleccionar rol tras una pregunta fuera de dominio no contamine la sesión con la pregunta anterior."""
        from app.services.router_logic import RouterLogic

        sess_id = "role_purge_sess_1"
        # 1. Enviar pregunta fuera de dominio (código general)
        res1 = await RouterLogic.procesar_mensaje("puedes hacer codigo", session_id=sess_id)
        assert res1.get("tipo") == "FUERA_DE_DOMINIO"

        # 2. Enviar declaración de rol
        res2 = await RouterLogic.procesar_mensaje("estudiante", session_id=sess_id)
        assert res2.get("tipo") == "DIAGNOSTICO"
        # No debe intentar buscar "código estudiantil" ni ejecutar RAG sobre el código anterior
        assert "código estudiantil" not in res2.get("mensaje", "").lower()
        assert "en qué" in res2.get("mensaje", "").lower() or "te puedo colaborar" in res2.get("mensaje", "").lower()

    @pytest.mark.asyncio


    @pytest.mark.asyncio
    async def test_out_of_domain_guardrail_strict(self):
        """Valida que programación general, ensayos, tareas y cultura general sean interceptados por el guardrail."""
        from app.services.router_logic import RouterLogic

        ood_queries = [
            "puedes hacer codigo",
            "investigacion de garcia marques",
            "hola mundo en python",
            "hazme un ensayo sobre la revolucion francesa",
            "receta de arroz con pollo",
            "cuentame un chiste"
        ]

        for q in ood_queries:
            res = await RouterLogic.procesar_mensaje(q, session_id=f"ood_{hash(q)}")
            assert res.get("tipo") == "FUERA_DE_DOMINIO", f"Falló para query: {q}"
            assert res.get("quick_replies") == []
            assert "No estoy facultado" in res.get("mensaje", "") or "exclusivamente" in res.get("mensaje", "")

    def test_sanitize_markdown_links_allowed_and_hallucinated_urls(self):
        """Valida que URLs alucinadas se conviertan a texto plano y URLs permitidas se conserven."""
        from app.services.rag_service import sanitize_markdown_links, clean_llm_response

        # 1. URL alucinada inventada por el LLM -> debe quedar solo el texto plano
        fake_text = "Ingresa en [Activación de Cuenta](https://unisimon.edu.co/activacion-de-cuenta) para continuar."
        sanitized_fake = sanitize_markdown_links(fake_text)
        assert sanitized_fake == "Ingresa en Activación de Cuenta para continuar."

        # 2. URL permitida oficial -> debe conservarse el enlace Markdown
        valid_text = "Ingresa a [Portal Estudiantes](https://portal.unisimon.edu.co) y selecciona la opción."
        sanitized_valid = sanitize_markdown_links(valid_text)
        assert "[Portal Estudiantes](https://portal.unisimon.edu.co)" in sanitized_valid

        # 3. URL de Microsoft Password Reset permitida -> debe conservarse
        ms_text = "Restablece tu clave en [Microsoft Password Reset](https://passwordreset.microsoftonline.com)."
        sanitized_ms = clean_llm_response(ms_text)
        assert "[Microsoft Password Reset](https://passwordreset.microsoftonline.com)" in sanitized_ms

    @pytest.mark.asyncio
    async def test_self_service_password_reset_priority_over_support_email(self):
        """Valida que consultas de olvido de contraseña prioricen el autoservicio del portal con pasos detallados."""
        from app.services.rag_service import rag_service

        query = "olvidé mi contraseña del portal estudiantil cómo la recupero"
        res = await rag_service.query_rag(query, user_role="estudiante")
        text = res.get("response", "")

        # Debe incluir los pasos de autoservicio
        assert any(w in text.lower() for w in ["portal", "portales", "olvidé", "olvide", "usuario", "contraseña", "clave"])
        # No debe limitarse a pedir un correo de soporte como única respuesta
        assert "paso" in text.lower() or "1." in text or "ingresar" in text.lower()

    @pytest.mark.asyncio
    async def test_ambiguous_student_password_query_disambiguates_seniority_and_avoids_email_paradox(self):
        """Valida que ante una consulta ambigua de clave sin semestre, se desambigüe primer ingreso vs regular,
        se use la etiqueta exacta 'Olvidé mi Usuario / Contraseña' y se envíe el enlace al correo personal."""
        from app.services.rag_service import rag_service

        query = "Colega, ando embalao: la página no me deja entrar y me dice que la clave está mala. ¿Qué hago ahí?"
        res = await rag_service.query_rag(query, user_role="estudiante")
        text = res.get("response", "")
        sources = res.get("sources", [])

        text_lower = text.lower()
        # 1. Debe desambiguar primer semestre / nuevo ingreso vs regular
        assert "primer semestre" in text_lower or "nuevo ingreso" in text_lower
        assert "unisimon" in text_lower
        assert "regular" in text_lower or "segundo semestre" in text_lower

        # 2. Debe usar la etiqueta exacta del enlace de autoservicio
        assert "olvidé mi usuario / contraseña" in text_lower or "olvide mi usuario / contraseña" in text_lower

        # 3. No debe caer en la paradoja de exigir correo institucional para recuperar la clave perdida
        assert "correo personal" in text_lower
        assert "revisa tu correo institucional para encontrar" not in text_lower

        # 4. Ambas fuentes documentales clave deben ser recuperadas
        assert any("primer semestre" in s.lower() or "activar usuario" in s.lower() for s in sources)
        assert any("restablecimiento" in s.lower() for s in sources)
















