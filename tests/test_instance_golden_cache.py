from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.bot_instance_service import BotRAGRuntime


class FixedEmbeddingModel:
    def encode(self, texts):
        return [FixedVector([0.1, 0.2, 0.3, 0.4]) for _ in texts]


class FixedVector(list):
    def tolist(self):
        return list(self)


def test_each_dependency_golden_cache_is_isolated(monkeypatch, tmp_path):
    import app.services.golden_cache_service as golden

    monkeypatch.setattr(golden, "CHROMA_PATH", str(tmp_path / "main"))
    monkeypatch.setattr(golden, "get_embedding_model", lambda: FixedEmbeddingModel())
    from app.services.bot_instance_service import bot_instance_manager

    monkeypatch.setattr(
        bot_instance_manager,
        "paths",
        lambda bot_id: SimpleNamespace(root=tmp_path / "instances" / bot_id),
    )
    golden._golden_collection = None
    golden._instance_golden_collections = {}
    query = "¿Cómo solicito el crédito interno de la dependencia?"

    assert golden.save_golden_case(
        "session-a", query, "En Casa Blanca, ingresa al módulo de crédito y registra la solicitud.",
        bot_id="casa-blanca",
    )
    assert golden.save_golden_case(
        "session-b", query, "En Bienestar, abre el portal y completa el formulario de crédito.",
        bot_id="bienestar",
    )

    result_a = golden.search_golden_case(query, bot_id="casa-blanca")
    result_b = golden.search_golden_case(query, bot_id="bienestar")
    assert result_a is not None and "Casa Blanca" in result_a[1]
    assert result_b is not None and "Bienestar" in result_b[1]
    assert golden.search_golden_case(query, bot_id="soporte-ti") is None

    assert golden.invalidate_golden_cache_entry(query, bot_id="casa-blanca")
    assert golden.search_golden_case(query, bot_id="casa-blanca") is None
    assert golden.search_golden_case(query, bot_id="bienestar") is not None

    for fallback in (
        "Por ahora no encuentro una guía cargada que respalde los pasos para ese tema.",
        "En este momento no pude generar una orientación confiable; comunícate con soporte.",
    ):
        assert not golden.is_valid_for_golden_cache(
            "¿Cómo hago el trámite de crédito?",
            fallback,
            bot_id="casa-blanca",
        )


def _runtime(bot_id="bienestar"):
    runtime = object.__new__(BotRAGRuntime)
    runtime.bot_id = bot_id
    runtime._histories = {}
    runtime._session_locks = {}
    runtime._lock_guard = threading.Lock()
    runtime._pending_feedback = {}
    runtime._index_lock = threading.RLock()
    return runtime


def _profile():
    return SimpleNamespace(
        display_name="BienestarBot",
        dependency_name="Bienestar Universitario",
        scope_description="Créditos y solicitudes de bienestar.",
        support_email="bienestar@example.edu",
        support_phone="+57 300 000 0000",
    )


@pytest.mark.asyncio
async def test_dependency_answer_offers_feedback_buttons_and_records_pending_pair(monkeypatch):
    import app.services.golden_cache_service as golden

    runtime = _runtime()
    document = SimpleNamespace(
        page_content="Para solicitar el crédito, abre el portal de Bienestar y completa el formulario.",
        metadata={"source_filename": "credito.md", "page_number": 1},
    )
    runtime._retrieve = lambda _question: [(document, 0.95)]
    runtime.rag = SimpleNamespace(
        llm_client=SimpleNamespace(
            chat_completion=lambda **_kwargs: asyncio.sleep(0, result={"content": "Completa el formulario de crédito en el portal."})
        )
    )
    monkeypatch.setattr(golden, "search_golden_case", lambda *_args, **_kwargs: None)

    result = await runtime.answer(_profile(), "session-1", "¿Cómo solicito el crédito interno?")

    assert result["quick_replies"] == [
        {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
        {"label": "🔄 No me funcionó", "payload": "RETRY_DIAGNOSIS"},
    ]
    assert runtime._pending_feedback["session-1"]["query"] == "¿Cómo solicito el crédito interno?"
    assert "formulario" in runtime._pending_feedback["session-1"]["response"]
    assert "bienestar@example.edu" not in runtime._pending_feedback["session-1"]["response"]


@pytest.mark.asyncio
async def test_positive_feedback_saves_to_only_the_current_dependency_cache(monkeypatch):
    import app.services.golden_cache_service as golden

    runtime = _runtime("casa-blanca")
    runtime._pending_feedback["session-2"] = {
        "created_at": datetime.now(timezone.utc),
        "query": "¿Cómo solicito financiación con ICETEX?",
        "response": "Sigue la ruta descrita en la guía de financiación de esta dependencia.",
    }
    calls = []
    monkeypatch.setattr(golden, "save_golden_case", lambda **kwargs: calls.append(kwargs) or True)

    result = await runtime.answer(_profile(), "session-2", "RESOLVED")

    assert calls[0]["bot_id"] == "casa-blanca"
    assert calls[0]["user_query"] == "¿Cómo solicito financiación con ICETEX?"
    assert result["feedback"] == "RESOLVED"
    assert result["quick_replies"] == []
    assert "confirmarlo" in result["response"].lower()
    assert "session-2" not in runtime._pending_feedback


@pytest.mark.asyncio
async def test_negative_feedback_invalidates_only_current_dependency_cache(monkeypatch):
    import app.services.golden_cache_service as golden

    runtime = _runtime("bienestar")
    runtime._pending_feedback["session-3"] = {
        "created_at": datetime.now(timezone.utc),
        "query": "¿Cómo solicito crédito interno?",
        "response": "Usa el portal de bienestar para diligenciar la solicitud.",
    }
    calls = []
    monkeypatch.setattr(golden, "invalidate_golden_cache_entry", lambda *args, **kwargs: calls.append((args, kwargs)) or True)

    result = await runtime.answer(_profile(), "session-3", "RETRY_DIAGNOSIS")

    assert calls[0][0][0] == "¿Cómo solicito crédito interno?"
    assert calls[0][1]["bot_id"] == "bienestar"
    assert result["feedback"] == "RETRY"
    assert result["quick_replies"] == []
    assert "mensaje de error" in result["response"].lower()
    assert "session-3" not in runtime._pending_feedback


@pytest.mark.asyncio
async def test_dependency_chat_api_returns_feedback_buttons(monkeypatch):
    from app.routers import chat as chat_router
    from app.services.bot_instance_service import bot_instance_manager

    profile = _profile()

    class Runtime:
        async def answer(self, _profile, _session_id, _question):
            return {
                "response": "Prueba la ruta indicada en el manual.",
                "sources": ["guia.md"],
                "retrieved_chunks": 1,
                "quick_replies": [
                    {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
                    {"label": "🔄 No me funcionó", "payload": "RETRY_DIAGNOSIS"},
                ],
            }

    monkeypatch.setattr(bot_instance_manager, "get", lambda _bot_id: profile)
    monkeypatch.setattr(bot_instance_manager, "get_runtime", lambda _bot_id: Runtime())
    monkeypatch.setattr(chat_router, "log_interaction", lambda **_kwargs: None)
    monkeypatch.setattr(chat_router, "get_route_usage", lambda: {"complete": True})

    result = await chat_router.process_chatbot_instance(
        "bienestar",
        chat_router.ChatRequest(mensaje="¿Cómo hago este trámite?", session_id="feedback-api-session"),
    )

    assert [item["label"] for item in result.quick_replies] == [
        "✅ Sí, me funcionó",
        "🔄 No me funcionó",
    ]
