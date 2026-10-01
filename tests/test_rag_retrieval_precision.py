from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.rag_service import (
    _is_onboarding_query,
    is_account_identifier_query,
    is_suspicious_email_query,
    rag_service,
    rerank_chunks,
    strip_chunk_boilerplate,
    _generic_lexical_candidates,
)


def make_doc(source, text, category="general"):
    return SimpleNamespace(
        page_content=text,
        metadata={"source": source, "category": category, "audience": "general"},
    )


def test_new_student_account_query_filters_financial_sources():
    question = "Soy nuevo en Barranquilla, ¿cómo sé cuál es mi usuario para entrar al correo institucional?"

    assert is_account_identifier_query(question)
    assert _is_onboarding_query(question)
    assert rag_service._build_query_filter(question) == {
        "$and": [
            {"audience": {"$in": ["estudiante", "general"]}},
            {"category": {"$ne": "financiero"}},
        ]
    }


def test_account_reranker_prefers_activation_and_drops_unrelated_login_docs():
    question = "Soy nuevo, ¿cómo obtengo mi usuario para el correo institucional?"
    activation = make_doc(
        "Activar Usuario y Correo institucional.pdf",
        "Activar usuario y correo institucional para estudiantes de primer semestre.",
    )
    microsoft = make_doc(
        "Credenciales microsoft.pdf",
        "Credenciales Microsoft institucionales y acceso con la cuenta de la universidad.",
    )
    financial = make_doc(
        "Instructivo Credito Empresarial.pptx",
        "Digite su usuario y contraseña institucional y presione el botón Acceder.",
        category="financiero",
    )
    irrelevant = make_doc("Mantenimiento.pdf", "Mantenimiento preventivo de computadores.")
    mock_model = MagicMock()
    mock_model.predict.return_value = [9.0, 1.0, 20.0, 10.0]

    with patch("app.services.rag_service.get_reranker", return_value=mock_model):
        ranked = rerank_chunks(
            question,
            [(financial, 0.84), (microsoft, 0.82), (irrelevant, 0.80), (activation, 0.81)],
            top_k=4,
            original_query=question,
        )

    assert [doc.metadata["source"] for doc, _ in ranked] == [
        "Activar Usuario y Correo institucional.pdf",
        "Credenciales microsoft.pdf",
    ]


def test_account_query_still_applies_source_guard_without_cross_encoder():
    question = "¿Cómo consulto mi usuario para el correo institucional?"
    unrelated = make_doc("Credito Empresarial.pptx", "Acceso al portal de créditos.", "financiero")

    with patch("app.services.rag_service.get_reranker", return_value=None):
        assert rerank_chunks(question, [(unrelated, 0.9)], original_query=question) == []


def test_suspicious_email_is_not_misclassified_as_account_activation():
    question = "Me llegó un correo rarísimo con un enlace urgente o me quitan la cuenta institucional. ¿A quién aviso?"

    assert is_suspicious_email_query(question)
    assert not is_account_identifier_query(question)
    assert rag_service._build_query_filter(question) == {"category": {"$ne": "financiero"}}


def test_phishing_reranker_selects_malware_procedure_only():
    question = "Me llegó un correo sospechoso con un enlace urgente, ¿a quién aviso?"
    security = make_doc(
        "P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf",
        "Ante cualquier correo sospechoso, no debe abrirlo e informar de inmediato al Oficial de Seguridad de la Información o a Dirección de TI para su inspección.",
    )
    report = make_doc("Reportes créditos de matriculados.pptx", "Generar reporte de créditos y matriculados.")
    portal = make_doc("instructivo portales estudiantes.pdf", "Ingrese su correo institucional para acceder al portal.")
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.1, 12.0, 10.0]

    with patch("app.services.rag_service.get_reranker", return_value=mock_model):
        ranked = rerank_chunks(
            question,
            [(security, 0.72), (report, 0.83), (portal, 0.80)],
            top_k=5,
            original_query=question,
        )

    assert len(ranked) == 1
    assert ranked[0][0].metadata["source"].startswith("P-GT-07")


@pytest.mark.asyncio
async def test_generic_lexical_fallback_recovers_evidence_when_vectors_miss():
    question = "Me llegó un correo sospechoso con un enlace urgente, ¿a quién aviso?"
    policy_text = (
        "4.3 Ante cualquier correo sospechoso el funcionario no debe abrirlo y debe informarle "
        "de inmediato al Oficial de Seguridad de la Información o en su defecto a la Dirección de TI para su inspección."
    )

    class FakeCollection:
        def count(self):
            return 1

        def get(self, **kwargs):
            return {"ids": ["policy"], "documents": [policy_text], "metadatas": [{
                "source": "P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf",
                "category": "general", "audience": "general",
            }]}

    class FakeVectorStore:
        _collection = FakeCollection()

        def similarity_search_with_relevance_scores(self, *args, **kwargs):
            return []

    llm_response = {
        "content": "No abras el correo. Informa al Oficial de Seguridad de la Información o a Dirección de TI.",
        "prompt_tokens": 1,
        "cached_tokens": 0,
        "eval_tokens": 1,
        "model": "mock",
        "source": "mock",
    }
    with patch.object(rag_service, "_vector_store", FakeVectorStore()):
        with patch("app.services.rag_service.async_generate_multi_query_variants", new=AsyncMock(return_value=[question])):
            with patch("app.services.rag_service.get_reranker", return_value=None):
                with patch.object(rag_service.llm_client, "chat_completion", new=AsyncMock(return_value=llm_response)):
                    result = await rag_service.query_rag(question, user_role="general")

    assert result["has_context"] is True
    assert result["retrieved_chunks"] == 1
    assert result["sources"] == ["P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf"]


def test_generic_lexical_candidates_retrieve_different_subject_without_domain_casework():
    target = "El usuario temporal para ingreso a la plataforma se encuentra en el recibo de matrícula."
    class Collection:
        def count(self):
            return 1

        def get(self, **kwargs):
            return {"documents": [target], "metadatas": [{"source": "Activar Usuario.pdf"}]}

    candidates = _generic_lexical_candidates(
        Collection(), ["¿Dónde encuentro el usuario temporal para entrar a la plataforma?"], None
    )
    assert candidates
    assert candidates[0][0].metadata["source"] == "Activar Usuario.pdf"


def test_boilerplate_cleanup_handles_quote_variants_and_vision_apologies():
    text = (
        "Digite su usuario y contraseña institucional para acceder al sistema y luego "
        "presione sobre el botón «Acceder».\n\n"
        "[Imagen: Lo siento, pero no puedo ayudar con la descripción de imágenes.]\n\n"
        "El usuario y correo institucional para estudiantes nuevos se consulta en el recibo de matrícula."
    )

    cleaned = strip_chunk_boilerplate(text)

    assert "Digite su usuario" not in cleaned
    assert "Lo siento" not in cleaned
    assert "recibo de matrícula" in cleaned
