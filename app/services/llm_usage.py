"""Captura el uso LLM de una sola petición sin mezclar sesiones concurrentes."""

from contextvars import ContextVar, Token
from typing import Any, Dict, Optional


_request_usage: ContextVar[Optional[Dict[str, Any]]] = ContextVar("unimon_request_llm_usage", default=None)


def begin_llm_usage_capture() -> Token:
    """Inicia el acumulador aislado para la petición asíncrona actual."""
    return _request_usage.set({
        "prompt_tokens": 0,
        "cached_tokens": 0,
        "eval_tokens": 0,
        "llm_calls": 0,
        "complete": True,
    })


def record_llm_usage(
    prompt_tokens: Any = 0,
    cached_tokens: Any = 0,
    eval_tokens: Any = 0,
    usage_reported: bool = True,
) -> None:
    """Agrega una llamada LLM exitosa al acumulador de la petición actual."""
    usage = _request_usage.get()
    if usage is None:
        return

    usage["llm_calls"] += 1
    if not usage_reported:
        usage["complete"] = False
        return

    def nonnegative_int(value: Any) -> int:
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError, OverflowError):
            return 0

    prompt = nonnegative_int(prompt_tokens)
    cached = min(prompt, nonnegative_int(cached_tokens))
    usage["prompt_tokens"] += prompt
    usage["cached_tokens"] += cached
    usage["eval_tokens"] += nonnegative_int(eval_tokens)


def finish_llm_usage_capture(token: Token) -> Dict[str, Any]:
    """Cierra el acumulador y devuelve una instantánea antes de limpiar el contexto."""
    usage = _request_usage.get()
    snapshot = dict(usage) if usage is not None else {
        "prompt_tokens": 0,
        "cached_tokens": 0,
        "eval_tokens": 0,
        "llm_calls": 0,
        "complete": False,
    }
    _request_usage.reset(token)
    return snapshot
