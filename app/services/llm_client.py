"""
Módulo cliente unificado para LLM (OpenAI API / Ollama Local).
Permite alternar entre proveedores mediante la variable LLM_PROVIDER en .env,
con soporte para GPT-5.6 Luna, GPT-4o-mini y modelos locales de Ollama con fallback automático.
"""

import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.config import get_settings

logger = logging.getLogger("unimon.llm_client")


class LLMClient:
    """Cliente unificado para comunicación con LLMs en la nube o locales."""

    def __init__(self):
        self.settings = get_settings()

    @property
    def provider(self) -> str:
        return (self.settings.llm_provider or "openai").lower().strip()

    @property
    def active_model(self) -> str:
        if self.provider == "openai":
            return self.settings.openai_model
        return self.settings.llm_model

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 768,
        temperature: Optional[float] = None,
        fallback_to_ollama: bool = False
    ) -> Dict[str, Any]:
        """
        Ejecuta una consulta conversacional completa con el LLM activo.
        
        En modo 'openai', el fallback a Ollama está COMPLETAMENTE DESHABILITADO
        para garantizar que el 100% de las inferencias provengan de la nube.
        """
        if self.provider == "openai":
            if not self.settings.openai_api_key:
                raise RuntimeError("LLM_PROVIDER está configurado como 'openai', pero no se encontró OPENAI_API_KEY en .env")
            # Modo estricto: solo OpenAI en la nube
            return await self._call_openai_chat(messages, max_tokens=max_tokens)

        # Modo Ollama local directo (únicamente si LLM_PROVIDER=ollama)
        return await self._call_ollama_chat(messages, max_tokens=max_tokens, temperature=temperature or 0.0)

    async def _call_openai_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 768
    ) -> Dict[str, Any]:
        """Llamada asíncrona a la API de OpenAI con soporte para modelos modernos como GPT-5.6 Luna."""
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
        model_name = self.settings.openai_model

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "max_completion_tokens": max(max_tokens, 600)
        }

        # Para modelos GPT-5 / Luna optimizamos la latencia con esfuerzo de razonamiento bajo
        if any(k in model_name for k in ["gpt-5", "o1", "o3", "luna"]):
            payload["reasoning_effort"] = "low"
        else:
            payload["temperature"] = 0.0

        timeout = self.settings.openai_timeout or 35.0

        print(f"\n[OPENAI CLOUD] >>> Enviando consulta al modelo: '{model_name}' en {url}...", flush=True)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "").strip()
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                cached_tokens = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
                regular_input = max(0, prompt_tokens - cached_tokens)

                print(
                    f"[OPENAI CLOUD] <<< Respuesta exitosa de '{model_name}'!\n"
                    f"               - Entrada regular ($0.20/1M):  {regular_input} tokens\n"
                    f"               - Entrada en CACHÉ ($0.02/1M): {cached_tokens} tokens\n"
                    f"               - Salida generada ($1.20/1M):  {completion_tokens} tokens\n",
                    flush=True
                )

                logger.info(
                    "[LLMClient] OpenAI '%s' respondió exitosamente (tokens: in=%s, cached=%s, out=%s).",
                    model_name, regular_input, cached_tokens, completion_tokens
                )

                return {
                    "content": content,
                    "prompt_tokens": prompt_tokens,
                    "cached_tokens": cached_tokens,
                    "eval_tokens": completion_tokens,
                    "model": model_name,
                    "provider": "openai",
                    "source": f"openai_{model_name}"
                }

            error_text = response.text
            print(f"[OPENAI CLOUD] [ERROR] Código {response.status_code}: {error_text}\n", flush=True)
            logger.error("[LLMClient] Error HTTP %s de OpenAI: %s", response.status_code, error_text)
            raise RuntimeError(f"OpenAI API error {response.status_code}: {error_text}")

    async def _call_ollama_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 768,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Llamada asíncrona al servicio de Ollama local."""
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "repeat_penalty": 1.15,
                "top_p": 0.9,
                "num_predict": max_tokens,
                "num_ctx": 8192
            }
        }

        async with httpx.AsyncClient(timeout=self.settings.ollama_timeout) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "").strip()
                prompt_tokens = data.get("prompt_eval_count", 0) or 0
                eval_tokens = data.get("eval_count", 0) or 0

                return {
                    "content": content,
                    "prompt_tokens": prompt_tokens,
                    "eval_tokens": eval_tokens,
                    "model": self.settings.llm_model,
                    "provider": "ollama",
                    "source": f"ollama_{self.settings.llm_model}"
                }

            raise RuntimeError(f"Ollama error {response.status_code}: {response.text}")

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 256,
        timeout: Optional[float] = None
    ) -> str:
        """Generación de texto simple asíncrona (ej. variaciones de consulta, resúmenes)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if self.provider == "openai" and self.settings.openai_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json"
                }
                url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
                payload: Dict[str, Any] = {
                    "model": self.settings.openai_model,
                    "messages": messages,
                    "max_completion_tokens": max(max_tokens, 450)
                }
                if any(k in self.settings.openai_model for k in ["gpt-5", "o1", "o3", "luna"]):
                    payload["reasoning_effort"] = "low"
                async with httpx.AsyncClient(timeout=timeout or self.settings.openai_timeout) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    logger.error("[LLMClient] Error HTTP %s de OpenAI en generate_async: %s", resp.status_code, resp.text)
                    raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error("[LLMClient] Falló generate_async con OpenAI: %s", e)
                raise e

        # Fallback / Modo directo a Ollama generate (únicamente si LLM_PROVIDER=ollama)
        try:
            ollama_url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
            async with httpx.AsyncClient(timeout=timeout or 5.0) as client:
                body: Dict[str, Any] = {
                    "model": self.settings.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": max_tokens}
                }
                if system_prompt:
                    body["system"] = system_prompt
                resp = await client.post(ollama_url, json=body)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception as e:
            logger.warning("[LLMClient] Falló generate_async con Ollama (%s)", e)

        return ""

    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 300,
        timeout: Optional[float] = None
    ) -> str:
        """Generación síncrona simple para procedimientos o análisis."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if self.provider == "openai" and self.settings.openai_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json"
                }
                url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
                payload = {
                    "model": self.settings.openai_model,
                    "messages": messages,
                    "max_completion_tokens": max(max_tokens, 450)
                }
                if any(k in self.settings.openai_model for k in ["gpt-5", "o1", "o3", "luna"]):
                    payload["reasoning_effort"] = "low"
                with httpx.Client(timeout=timeout or self.settings.openai_timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    logger.error("[LLMClient] Error HTTP %s de OpenAI en generate_sync: %s", resp.status_code, resp.text)
                    raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error("[LLMClient] Falló generate_sync con OpenAI: %s", e)
                raise e

        # Fallback / Modo directo a Ollama (únicamente si LLM_PROVIDER=ollama)
        try:
            ollama_url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
            with httpx.Client(timeout=timeout or 6.0) as client:
                body: Dict[str, Any] = {
                    "model": self.settings.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": max_tokens}
                }
                if system_prompt:
                    body["system"] = system_prompt
                resp = client.post(ollama_url, json=body)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception as e:
            logger.warning("[LLMClient] Falló generate_sync con Ollama (%s)", e)

        return ""

    async def check_health(self) -> Dict[str, Any]:
        """Comprueba la disponibilidad del proveedor activo."""
        if self.provider == "openai":
            if not self.settings.openai_api_key:
                return {
                    "active": False,
                    "provider": "openai",
                    "model": self.settings.openai_model,
                    "error": "No hay OPENAI_API_KEY configurada en .env"
                }
            try:
                headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}
                url = f"{self.settings.openai_base_url.rstrip('/')}/models/{self.settings.openai_model}"
                async with httpx.AsyncClient(timeout=4.0) as client:
                    r = await client.get(url, headers=headers)
                    if r.status_code == 200:
                        return {
                            "active": True,
                            "provider": "openai",
                            "model": self.settings.openai_model,
                            "endpoint": self.settings.openai_base_url
                        }
                    # Si el endpoint específico del modelo da 404 pero la key es válida:
                    r_models = await client.get(f"{self.settings.openai_base_url.rstrip('/')}/models", headers=headers)
                    if r_models.status_code == 200:
                        return {
                            "active": True,
                            "provider": "openai",
                            "model": self.settings.openai_model,
                            "endpoint": self.settings.openai_base_url
                        }
                    return {
                        "active": False,
                        "provider": "openai",
                        "model": self.settings.openai_model,
                        "error": f"OpenAI HTTP {r.status_code}"
                    }
            except Exception as e:
                return {
                    "active": False,
                    "provider": "openai",
                    "model": self.settings.openai_model,
                    "error": str(e)
                }

        # Ollama local
        try:
            url = f"{self.settings.ollama_base_url.rstrip('/')}/api/tags"
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    models = [m.get("name") for m in r.json().get("models", [])]
                    return {
                        "active": True,
                        "provider": "ollama",
                        "model": self.settings.llm_model,
                        "endpoint": self.settings.ollama_base_url,
                        "models_in_server": models
                    }
                return {
                    "active": False,
                    "provider": "ollama",
                    "model": self.settings.llm_model,
                    "error": f"Ollama HTTP {r.status_code}"
                }
        except Exception as e:
            return {
                "active": False,
                "provider": "ollama",
                "model": self.settings.llm_model,
                "error": str(e)
            }


_llm_client_instance: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Retorna una instancia singleton de LLMClient."""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
