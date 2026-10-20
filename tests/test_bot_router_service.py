from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from app.services import bot_router_service


def test_clear_it_request_is_sent_to_router_with_unimon_as_explicit_destination(monkeypatch):
    profile = SimpleNamespace(
        bot_id="bienestar",
        display_name="Casa Blanca",
        dependency_name="Admisiones",
        scope_description="Financiamiento, matrícula, pagos e ICETEX.",
    )
    monkeypatch.setattr(bot_router_service.bot_instance_manager, "list", lambda: [profile])
    monkeypatch.setattr(bot_router_service, "_rank_specialists", lambda _question, candidates: candidates)
    monkeypatch.setattr(bot_router_service, "_specialization_text", lambda _profile: "ICETEX y matrícula")
    session_id = "router-topic-switch-test"
    monkeypatch.setitem(
        bot_router_service._recent_routes,
        session_id,
        (datetime.now(timezone.utc), "bienestar"),
    )

    class FakeClassifier:
        called = False

        async def chat_completion(self, messages, **_kwargs):
            self.called = True
            prompt = messages[1]["content"]
            assert '"bot_id": "unimon"' in prompt
            assert '"name": "UniMon Soporte TI"' in prompt
            assert '"bot_id": "bienestar"' not in prompt
            return {
                # Even if the model tries to preserve the previous finance route,
                # that destination is absent from the allowlist for a clear IT issue.
                "content": '{"bot_id":"bienestar","reason":"Conserva la ruta anterior."}'
            }

    classifier = FakeClassifier()
    monkeypatch.setattr(bot_router_service, "get_llm_client", lambda: classifier)

    result = asyncio.run(bot_router_service.select_chatbot(
        "Tengo un problema con mi PC que está lento, ¿qué hago?",
        session_id,
    ))

    assert result["bot_id"] == "unimon"
    assert session_id not in bot_router_service._recent_routes
    assert classifier.called is True


def test_clear_it_request_routes_only_among_unimon_and_explicit_it_specialists(monkeypatch):
    finance = SimpleNamespace(
        bot_id="admisiones",
        display_name="AdmisionesBot",
        dependency_name="Admisiones",
        scope_description="Financiamiento e ICETEX.",
    )
    it_support = SimpleNamespace(
        bot_id="soporte-ti",
        display_name="Soporte TI",
        dependency_name="Dirección de Tecnología e Información",
        scope_description="Atiende fallas de computadores, red y cuentas institucionales.",
    )
    monkeypatch.setattr(bot_router_service.bot_instance_manager, "list", lambda: [finance, it_support])
    monkeypatch.setattr(bot_router_service, "_rank_specialists", lambda _question, candidates: candidates)
    monkeypatch.setattr(bot_router_service, "_specialization_text", lambda _profile: "")

    class FakeClassifier:
        async def chat_completion(self, messages, **_kwargs):
            prompt = messages[1]["content"]
            assert '"bot_id": "admisiones"' not in prompt
            assert '"bot_id": "unimon"' in prompt
            return {"content": '{"bot_id":"soporte-ti","reason":"La consulta es soporte de TI."}'}

    monkeypatch.setattr(bot_router_service, "get_llm_client", FakeClassifier)

    result = asyncio.run(bot_router_service.select_chatbot(
        "Tengo un problema con mi computador que está lento.",
        "router-it-specialist-test",
    ))

    assert result["bot_id"] == "soporte-ti"


def test_non_it_query_shows_default_it_bot_and_dependency_to_router(monkeypatch):
    finance = SimpleNamespace(
        bot_id="bienestar",
        display_name="Casa Blanca",
        dependency_name="Admisiones",
        scope_description="Financiamiento, matrícula, pagos e ICETEX.",
    )
    monkeypatch.setattr(bot_router_service.bot_instance_manager, "list", lambda: [finance])
    monkeypatch.setattr(bot_router_service, "_rank_specialists", lambda _question, candidates: candidates)
    monkeypatch.setattr(bot_router_service, "_specialization_text", lambda _profile: "ICETEX y financiamiento")

    class FakeClassifier:
        async def chat_completion(self, messages, **_kwargs):
            prompt = messages[1]["content"]
            assert '"bot_id": "unimon"' in prompt
            assert '"bot_id": "bienestar"' in prompt
            return {"content": '{"bot_id":"bienestar","reason":"La consulta es sobre ICETEX."}'}

    monkeypatch.setattr(bot_router_service, "get_llm_client", FakeClassifier)

    result = asyncio.run(bot_router_service.select_chatbot(
        "Quiero financiar mis estudios con ICETEX, ¿cómo empiezo?",
        "router-catalog-test",
    ))

    assert result["bot_id"] == "bienestar"


def test_feedback_payload_returns_to_dependency_that_answered(monkeypatch):
    profile = SimpleNamespace(
        bot_id="bienestar",
        display_name="Casa Blanca",
        dependency_name="Admisiones",
        scope_description="Financiamiento, matrícula, pagos e ICETEX.",
    )
    monkeypatch.setattr(bot_router_service.bot_instance_manager, "list", lambda: [profile])
    session_id = "router-feedback-stays-on-specialist"
    monkeypatch.setitem(
        bot_router_service._recent_routes,
        session_id,
        (datetime.now(timezone.utc), "bienestar"),
    )

    result = asyncio.run(bot_router_service.select_chatbot("RESOLVED", session_id))

    assert result["bot_id"] == "bienestar"


def test_financial_question_remains_eligible_for_financial_specialist(monkeypatch):
    finance = SimpleNamespace(
        bot_id="bienestar",
        display_name="Casa Blanca",
        dependency_name="Admisiones",
        scope_description="Financiamiento, matrícula, pagos e ICETEX.",
    )
    monkeypatch.setattr(bot_router_service.bot_instance_manager, "list", lambda: [finance])
    monkeypatch.setattr(bot_router_service, "_rank_specialists", lambda _question, candidates: candidates)
    monkeypatch.setattr(bot_router_service, "_specialization_text", lambda _profile: "ICETEX y financiamiento")

    class FakeClassifier:
        async def chat_completion(self, *_args, **_kwargs):
            return {"content": '{"bot_id":"bienestar","reason":"La consulta es sobre ICETEX."}'}

    monkeypatch.setattr(bot_router_service, "get_llm_client", FakeClassifier)

    result = asyncio.run(bot_router_service.select_chatbot(
        "Quiero financiar mis estudios con ICETEX, ¿cómo empiezo?",
        "router-finance-test",
    ))

    assert result["bot_id"] == "bienestar"

