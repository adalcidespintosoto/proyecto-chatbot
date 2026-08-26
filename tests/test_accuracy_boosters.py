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









