"""
Módulo cliente unificado para LLM (Anthropic, OpenAI, Gemini y Ollama Local).
Permite alternar entre proveedores mediante la variable LLM_PROVIDER en .env,
con soporte para GPT-5.6 Luna, GPT-4o-mini y modelos locales de Ollama con fallback automático.
"""

import logging
import re
import asyncio
from typing import Any, Dict, List, Optional
import httpx

from app.config import get_settings
from app.services.llm_usage import record_llm_usage
from app.services.llm_endpoint_security import validate_custom_llm_base_url

logger = logging.getLogger("unimon.llm_client")


class LLMClient:
    """Cliente unificado para comunicación con LLMs en la nube o locales."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        base_settings = get_settings()
        updates: Dict[str, Any] = {}
        self.custom_config = dict(custom_config) if custom_config else None
        if provider is not None:
            normalized_provider = provider.lower().strip()
            if normalized_provider == "custom":
                if not self.custom_config:
                    raise ValueError("Falta la configuración del proveedor LLM personalizado.")
                updates["llm_provider"] = "custom"
            elif normalized_provider not in {"openai", "anthropic", "gemini", "ollama"}:
                raise ValueError("Proveedor LLM no admitido.")
            else:
                updates["llm_provider"] = normalized_provider
            if model is not None and normalized_provider != "custom":
                model_setting = {
                    "openai": "openai_model",
                    "anthropic": "anthropic_model",
                    "gemini": "gemini_model",
                    "ollama": "llm_model",
                }[normalized_provider]
                updates[model_setting] = model
        self.settings = base_settings.model_copy(update=updates) if updates else base_settings

    @property
    def provider(self) -> str:
        return (self.settings.llm_provider or "openai").lower().strip()

    @property
    def active_model(self) -> str:
        if self.provider == "custom" and self.custom_config:
            return str(self.custom_config.get("model") or "")
        if self.provider == "anthropic":
            return self.settings.anthropic_model
        if self.provider == "gemini":
            return self.settings.gemini_model
        elif self.provider == "openai":
            return self.settings.openai_model
        return self.settings.llm_model

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 768,
        temperature: Optional[float] = None,
        fallback_to_ollama: bool = True
    ) -> Dict[str, Any]:
        """
        Ejecuta una consulta conversacional completa con el LLM activo.
        
        En modo Cloud ('anthropic', 'openai' o 'gemini'), si el proveedor en la nube presenta fallas
        (error de API, timeout de red, cuota excedida o indisponibilidad), se conmuta
        automáticamente a Ollama local (modelo unimon:8b) como contingencia de alta disponibilidad.
        """
        if self.provider == "custom":
            try:
                return await self._call_custom_chat(messages, max_tokens=max_tokens, timeout=None)
            except Exception as exc:
                if not fallback_to_ollama:
                    raise
                logger.warning(
                    "[LLMClient] Falló el proveedor personalizado '%s' (%s); se intenta Ollama local.",
                    self.custom_config.get("provider_name", "personalizado") if self.custom_config else "personalizado",
                    type(exc).__name__,
                )
                result = await self._call_ollama_chat(
                    messages, max_tokens=max_tokens, temperature=temperature or 0.0
                )
                result["contingency"] = True
                result["fallback_from"] = "custom"
                return result

        if self.provider == "anthropic":
            if not self.settings.anthropic_api_key:
                logger.warning("[LLMClient] Sin ANTHROPIC_API_KEY. Conmutando a contingencia local Ollama (%s)...", self.settings.llm_model)
                res = await self._call_ollama_chat(messages, max_tokens=max_tokens, temperature=temperature or 0.0)
                res["contingency"] = True
                res["fallback_from"] = "anthropic"
                return res

            try:
                return await self._call_anthropic_chat(messages, max_tokens=max_tokens)
            except Exception as exc:
                logger.warning(
                    "[LLMClient] Falla en Anthropic ('%s'): %s. Activando contingencia local Ollama ('%s')...",
                    self.settings.anthropic_model, exc, self.settings.llm_model
                )
                try:
                    res = await self._call_ollama_chat(messages, max_tokens=max_tokens, temperature=temperature or 0.0)
                    res["contingency"] = True
                    res["fallback_from"] = "anthropic"
                    return res
                except Exception as ollama_exc:
                    logger.error("[LLMClient] Fallaron Anthropic (%s) y Ollama (%s)", exc, ollama_exc)
                    raise RuntimeError(f"Falla total: Anthropic ({exc}) y contingencia Ollama ({ollama_exc})")

        if self.provider == "gemini":
            if not self.settings.gemini_api_key:
                logger.warning("[LLMClient] Sin GEMINI_API_KEY. Conmutando a contingencia local Ollama (%s)...", self.settings.llm_model)
                res = await self._call_ollama_chat(messages, max_tokens=max_tokens, temperature=temperature or 0.0)
                res["contingency"] = True
                res["fallback_from"] = "gemini"
                return res

            try:
                return await self._call_gemini_chat(messages, max_tokens=max_tokens)
            except Exception as exc:
                logger.warning(
                    "[LLMClient] Falla en Gemini (%s): %s. Conmutando de inmediato a contingencia local Ollama ('%s')...",
                    self.settings.gemini_model, exc, self.settings.llm_model
                )
                print(
                    f"\n[CONTINGENCIA LLM] Google Gemini fallo: {exc}\n"
                    f"[FALLBACK LOCAL] Conmutando de inmediato a Ollama Local ({self.settings.llm_model})...\n",
                    flush=True
                )
                res = await self._call_ollama_chat(messages, max_tokens=max_tokens, temperature=temperature or 0.0)
                res["contingency"] = True
                res["fallback_from"] = "gemini"
                return res

        if self.provider == "openai":
            if not self.settings.openai_api_key:
                logger.warning("[LLMClient] Sin OPENAI_API_KEY. Conmutando a contingencia local Ollama (%s)...", self.settings.llm_model)
                print(
                    f"\n[CONTINGENCIA LLM] OPENAI_API_KEY no configurada.\n"
                    f"[FALLBACK LOCAL] Conmutando a Ollama Local ({self.settings.llm_model})...\n",
                    flush=True
                )
                res = await self._call_ollama_chat(messages, max_tokens=max_tokens, temperature=temperature or 0.0)
                res["contingency"] = True
                res["fallback_from"] = "openai"
                return res

            try:
                return await self._call_openai_chat(messages, max_tokens=max_tokens)
            except Exception as exc:
                logger.warning(
                    "[LLMClient] Falla en OpenAI ('%s'): %s. Activando de inmediato contingencia con Ollama Local ('%s')...",
                    self.settings.openai_model, exc, self.settings.llm_model
                )
                print(
                    f"\n[CONTINGENCIA LLM] OpenAI ({self.settings.openai_model}) fallo: {exc}\n"
                    f"[FALLBACK LOCAL] Conmutando de inmediato a Ollama Local ({self.settings.llm_model})...\n",
                    flush=True
                )
                try:
                    res = await self._call_ollama_chat(messages, max_tokens=max_tokens, temperature=temperature or 0.0)
                    res["contingency"] = True
                    res["fallback_from"] = "openai"
                    return res
                except Exception as ollama_exc:
                    logger.error(
                        "[LLMClient] Falla crítica: Falló OpenAI (%s) y la contingencia Ollama también falló (%s)",
                        exc, ollama_exc
                    )
                    raise RuntimeError(f"Falla total: OpenAI ({exc}) y contingencia Ollama ({ollama_exc})")

        # Modo Ollama local directo (únicamente si LLM_PROVIDER=ollama)
        return await self._call_ollama_chat(messages, max_tokens=max_tokens, temperature=temperature or 0.0)

    async def _call_gemini_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 768
    ) -> Dict[str, Any]:
        """
        Llamada asíncrona a la API de Google Gemini utilizando su API nativa generateContent
        para máxima velocidad y estabilidad (evitando cuellos de botella del proxy OpenAI).
        """
        model_name = self.settings.gemini_model
        key = self.settings.gemini_api_key
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"

        contents = []
        system_instruction = None
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("system", "developer"):
                system_instruction = {"parts": [{"text": content}]}
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max(max_tokens, 1500)
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        timeout = self.settings.gemini_timeout or 45.0

        print(f"\n[GEMINI CLOUD] >>> Enviando consulta al modelo: '{model_name}' (API Nativa)...", flush=True)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [{}])
                if not candidates:
                    raise RuntimeError("Gemini no devolvió candidatos de respuesta.")
                parts = candidates[0].get("content", {}).get("parts", [{}])
                content = parts[0].get("text", "").strip() if parts else ""
                usage = data.get("usageMetadata", {})
                prompt_tokens = usage.get("promptTokenCount", 0)
                completion_tokens = usage.get("candidatesTokenCount", 0)
                record_llm_usage(
                    prompt_tokens=prompt_tokens,
                    cached_tokens=usage.get("cachedContentTokenCount", 0),
                    eval_tokens=completion_tokens,
                    usage_reported=bool(usage),
                )

                print(
                    f"[GEMINI CLOUD] <<< Respuesta exitosa de '{model_name}'!\n"
                    f"               - Entrada:  {prompt_tokens} tokens\n"
                    f"               - Salida:   {completion_tokens} tokens\n",
                    flush=True
                )

                logger.info(
                    "[LLMClient] Gemini '%s' respondió exitosamente (tokens: in=%s, out=%s).",
                    model_name, prompt_tokens, completion_tokens
                )

                return {
                    "content": content,
                    "prompt_tokens": prompt_tokens,
                    "cached_tokens": 0,
                    "eval_tokens": completion_tokens,
                    "model": model_name,
                    "provider": "gemini",
                    "source": f"gemini_{model_name}"
                }

            logger.error("[LLMClient] Error HTTP %s de Gemini", response.status_code)
            raise RuntimeError(f"Gemini API error {response.status_code}")

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
        if any(k in model_name for k in ["gpt-6", "gpt-5", "o1", "o3", "luna"]):
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
                record_llm_usage(
                    prompt_tokens=prompt_tokens,
                    cached_tokens=cached_tokens,
                    eval_tokens=completion_tokens,
                    usage_reported=bool(usage),
                )
                regular_input = max(0, prompt_tokens - cached_tokens)

                is_g6 = "gpt-6" in model_name.lower()
                r_in = "$0.10" if is_g6 else "$0.20"
                r_c = "$0.01" if is_g6 else "$0.02"
                r_out = "$0.50" if is_g6 else "$1.20"
                print(
                    f"[OPENAI CLOUD] <<< Respuesta exitosa de '{model_name}'!\n"
                    f"               - Entrada regular ({r_in}/1M):  {regular_input} tokens\n"
                    f"               - Entrada en CACHÉ ({r_c}/1M): {cached_tokens} tokens\n"
                    f"               - Salida generada ({r_out}/1M):  {completion_tokens} tokens\n",
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

            logger.error("[LLMClient] Error HTTP %s de OpenAI", response.status_code)
            raise RuntimeError(f"OpenAI API error {response.status_code}")

    def _custom_request(self, messages: List[Dict[str, Any]], max_tokens: int) -> tuple[str, Dict[str, Any], Dict[str, str], str]:
        config = self.custom_config or {}
        protocol = str(config.get("protocol") or "openai-compatible")
        base_url = str(config.get("base_url") or "").rstrip("/")
        model_name = str(config.get("model") or self.active_model)
        api_key = str(config.get("api_key") or "")
        if protocol == "anthropic":
            payload = self._build_anthropic_payload(messages, max_tokens, model_name=model_name)
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            return f"{base_url}/messages", payload, headers, protocol
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max(1, int(max_tokens)),
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        return f"{base_url}/chat/completions", payload, headers, protocol

    @staticmethod
    def _openai_compatible_content(data: Dict[str, Any]) -> str:
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            return "\n".join(
                str(block.get("text", ""))
                for block in content
                if isinstance(block, dict) and block.get("text")
            ).strip()
        return str(content or "").strip()

    def _custom_result(self, data: Dict[str, Any], protocol: str) -> Dict[str, Any]:
        config = self.custom_config or {}
        model_name = str(config.get("model") or self.active_model)
        provider_name = str(config.get("provider_name") or "Proveedor personalizado")
        if protocol == "anthropic":
            usage = self._record_anthropic_usage(data.get("usage", {}))
            content = self._anthropic_content(data)
            prompt_tokens = usage["prompt_tokens"]
            cached_tokens = usage["cached_tokens"]
            completion_tokens = usage["eval_tokens"]
        else:
            content = self._openai_compatible_content(data)
            usage = data.get("usage", {})
            prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens = int(usage.get("completion_tokens", 0) or 0)
            cached_tokens = int((usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0)
            record_llm_usage(
                prompt_tokens=prompt_tokens,
                cached_tokens=cached_tokens,
                eval_tokens=completion_tokens,
                usage_reported=bool(usage),
            )
        safe_provider = re.sub(r"[^a-z0-9]+", "_", provider_name.casefold()).strip("_")[:40] or "custom"
        return {
            "content": content,
            "prompt_tokens": prompt_tokens,
            "cached_tokens": cached_tokens,
            "eval_tokens": completion_tokens,
            "model": model_name,
            "provider": "custom",
            "provider_name": provider_name,
            "source": f"{safe_provider}_{model_name}",
        }

    async def _call_custom_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 768,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        config = self.custom_config or {}
        try:
            base_url = await asyncio.to_thread(
                validate_custom_llm_base_url, str(config.get("base_url") or ""), resolve_dns=True
            )
        except ValueError as exc:
            raise RuntimeError("El endpoint LLM personalizado no pasó la validación de seguridad.") from exc
        url, payload, headers, protocol = self._custom_request(messages, max_tokens)
        # Reemplaza la URL validada para evitar que el valor almacenado se use sin normalizar.
        suffix = "/messages" if protocol == "anthropic" else "/chat/completions"
        url = f"{base_url}{suffix}"
        request_timeout = timeout or float(config.get("timeout") or 35.0)
        async with httpx.AsyncClient(timeout=request_timeout, follow_redirects=False) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"El proveedor LLM personalizado devolvió HTTP {response.status_code}.")
        return self._custom_result(response.json(), protocol)

    def _call_custom_chat_sync(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 300,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        config = self.custom_config or {}
        try:
            base_url = validate_custom_llm_base_url(
                str(config.get("base_url") or ""), resolve_dns=True
            )
        except ValueError as exc:
            raise RuntimeError("El endpoint LLM personalizado no pasó la validación de seguridad.") from exc
        _, payload, headers, protocol = self._custom_request(messages, max_tokens)
        suffix = "/messages" if protocol == "anthropic" else "/chat/completions"
        url = f"{base_url}{suffix}"
        request_timeout = timeout or float(config.get("timeout") or 35.0)
        with httpx.Client(timeout=request_timeout, follow_redirects=False) as client:
            response = client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"El proveedor LLM personalizado devolvió HTTP {response.status_code}.")
        return self._custom_result(response.json(), protocol)

    def _build_anthropic_payload(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Adapta los mensajes internos al formato Messages API de Anthropic."""
        system_parts: List[str] = []
        conversation: List[Dict[str, Any]] = []

        for message in messages:
            role = str(message.get("role", "user")).lower()
            content = message.get("content", "")
            if role == "system":
                if content:
                    system_parts.append(content if isinstance(content, str) else str(content))
            elif role in ("user", "assistant") and content is not None:
                conversation.append({"role": role, "content": content})
            elif role == "tool" and content is not None:
                # UniMon no usa tool-calling con Anthropic; conserva el resultado como contexto.
                conversation.append({"role": "user", "content": f"Resultado de herramienta:\n{content}"})

        if not conversation:
            raise ValueError("Anthropic requiere al menos un mensaje user o assistant.")

        payload: Dict[str, Any] = {
            "model": model_name or self.settings.anthropic_model,
            "max_tokens": max(1, int(max_tokens)),
            "messages": conversation,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        return payload

    @staticmethod
    def _anthropic_content(data: Dict[str, Any]) -> str:
        """Une los bloques de texto devueltos por Messages API."""
        return "\n".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text" and block.get("text")
        ).strip()

    @staticmethod
    def _record_anthropic_usage(usage: Dict[str, Any]) -> Dict[str, int]:
        """Registra tokens incluyendo lecturas/escrituras de caché si Anthropic las informa."""
        cached = int(usage.get("cache_read_input_tokens", 0) or 0)
        cache_created = int(usage.get("cache_creation_input_tokens", 0) or 0)
        input_tokens = int(usage.get("input_tokens", 0) or 0) + cached + cache_created
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        record_llm_usage(
            prompt_tokens=input_tokens,
            cached_tokens=cached,
            eval_tokens=output_tokens,
            usage_reported=bool(usage),
        )
        return {
            "prompt_tokens": input_tokens,
            "cached_tokens": cached,
            "eval_tokens": output_tokens,
        }

    async def _call_anthropic_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 768,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Llamada asíncrona a Claude mediante Anthropic Messages API."""
        model_name = self.settings.anthropic_model
        url = f"{self.settings.anthropic_base_url.rstrip('/')}/messages"
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = self._build_anthropic_payload(messages, max_tokens)

        print(f"\n[ANTHROPIC CLOUD] >>> Enviando consulta al modelo: '{model_name}'...", flush=True)
        async with httpx.AsyncClient(timeout=timeout or self.settings.anthropic_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error("[LLMClient] Error HTTP %s de Anthropic", response.status_code)
                raise RuntimeError(f"Anthropic API error {response.status_code}")

            data = response.json()
            content = self._anthropic_content(data)
            usage = self._record_anthropic_usage(data.get("usage", {}))
            logger.info(
                "[LLMClient] Anthropic '%s' respondió exitosamente (tokens: in=%s, cached=%s, out=%s).",
                model_name, usage["prompt_tokens"], usage["cached_tokens"], usage["eval_tokens"],
            )
            return {
                "content": content,
                **usage,
                "model": model_name,
                "provider": "anthropic",
                "source": f"anthropic_{model_name}",
            }

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

        print(f"\n[OLLAMA LOCAL] >>> Enviando consulta al modelo local: '{self.settings.llm_model}' en {url}...", flush=True)
        async with httpx.AsyncClient(timeout=self.settings.ollama_timeout) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "").strip()
                prompt_tokens = data.get("prompt_eval_count", 0) or 0
                eval_tokens = data.get("eval_count", 0) or 0
                record_llm_usage(
                    prompt_tokens=prompt_tokens,
                    eval_tokens=eval_tokens,
                    usage_reported=("prompt_eval_count" in data or "eval_count" in data),
                )

                print(
                    f"[OLLAMA LOCAL] <<< Respuesta exitosa de '{self.settings.llm_model}'!\n"
                    f"               - Entrada procesada: {prompt_tokens} tokens\n"
                    f"               - Salida generada:   {eval_tokens} tokens (Costo Local: $0.00 USD)\n",
                    flush=True
                )

                return {
                    "content": content,
                    "prompt_tokens": prompt_tokens,
                    "cached_tokens": 0,
                    "eval_tokens": eval_tokens,
                    "model": self.settings.llm_model,
                    "provider": "ollama",
                    "source": f"ollama_{self.settings.llm_model}"
                }

            logger.error("[LLMClient] Error HTTP %s de Ollama", response.status_code)
            raise RuntimeError(f"Ollama error {response.status_code}")

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

        if self.provider == "custom":
            try:
                result = await self._call_custom_chat(messages, max_tokens=max_tokens, timeout=timeout)
                return str(result.get("content") or "").strip()
            except Exception as exc:
                logger.warning(
                    "[LLMClient] Falló generate_async con el proveedor personalizado (%s); se usará la contingencia local.",
                    type(exc).__name__,
                )

        if self.provider == "gemini" and self.settings.gemini_api_key:
            try:
                model_name = self.settings.gemini_model
                key = self.settings.gemini_api_key
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                contents = [{"role": "user", "parts": [{"text": prompt}]}]
                payload: Dict[str, Any] = {
                    "contents": contents,
                    "generationConfig": {
                        "maxOutputTokens": max(max_tokens, 250)
                    }
                }
                if system_prompt:
                    payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

                async with httpx.AsyncClient(timeout=timeout or self.settings.gemini_timeout or 20.0) as client:
                    resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                    if resp.status_code == 200:
                        data = resp.json()
                        usage = data.get("usageMetadata", {})
                        record_llm_usage(
                            prompt_tokens=usage.get("promptTokenCount", 0),
                            cached_tokens=usage.get("cachedContentTokenCount", 0),
                            eval_tokens=usage.get("candidatesTokenCount", 0),
                            usage_reported=bool(usage),
                        )
                        candidates = data.get("candidates", [{}])
                        parts = candidates[0].get("content", {}).get("parts", [{}])
                        return parts[0].get("text", "").strip() if parts else ""
                    logger.warning("[LLMClient] Error HTTP %s de Gemini en generate_async: %s", resp.status_code, resp.text)
            except Exception as e:
                logger.warning("[LLMClient] Falló generate_async con Gemini (%s). Conmutando a contingencia Ollama...", e)

        if self.provider == "anthropic" and self.settings.anthropic_api_key:
            try:
                result = await self._call_anthropic_chat(messages, max_tokens=max_tokens, timeout=timeout)
                return result["content"]
            except Exception as e:
                logger.warning("[LLMClient] Falló generate_async con Anthropic (%s). Conmutando a contingencia Ollama...", e)

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
                if any(k in self.settings.openai_model for k in ["gpt-6", "gpt-5", "o1", "o3", "luna"]):
                    payload["reasoning_effort"] = "low"
                async with httpx.AsyncClient(timeout=timeout or self.settings.openai_timeout) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        usage = data.get("usage", {})
                        record_llm_usage(
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            cached_tokens=usage.get("prompt_tokens_details", {}).get("cached_tokens", 0),
                            eval_tokens=usage.get("completion_tokens", 0),
                            usage_reported=bool(usage),
                        )
                        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    logger.warning("[LLMClient] Error HTTP %s de OpenAI en generate_async: %s", resp.status_code, resp.text)
            except Exception as e:
                logger.warning("[LLMClient] Falló generate_async con OpenAI (%s). Conmutando a contingencia Ollama...", e)

        # Fallback / Modo directo a Ollama generate (únicamente si LLM_PROVIDER=ollama o contingencia)
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
                    data = resp.json()
                    record_llm_usage(
                        prompt_tokens=data.get("prompt_eval_count", 0),
                        eval_tokens=data.get("eval_count", 0),
                        usage_reported=("prompt_eval_count" in data or "eval_count" in data),
                    )
                    return data.get("response", "").strip()
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

        if self.provider == "custom":
            try:
                result = self._call_custom_chat_sync(messages, max_tokens=max_tokens, timeout=timeout)
                return str(result.get("content") or "").strip()
            except Exception as exc:
                logger.warning(
                    "[LLMClient] Falló generate_sync con el proveedor personalizado (%s); se usará la contingencia local.",
                    type(exc).__name__,
                )

        if self.provider == "gemini" and self.settings.gemini_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.settings.gemini_api_key}",
                    "Content-Type": "application/json"
                }
                url = f"{self.settings.gemini_base_url.rstrip('/')}/chat/completions"
                payload = {
                    "model": self.settings.gemini_model,
                    "messages": messages,
                    "max_completion_tokens": max(max_tokens, 450)
                }
                with httpx.Client(timeout=timeout or self.settings.gemini_timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    logger.warning("[LLMClient] Error HTTP %s de Gemini en generate_sync: %s", resp.status_code, resp.text)
            except Exception as e:
                logger.warning("[LLMClient] Falló generate_sync con Gemini (%s). Conmutando a contingencia Ollama...", e)

        if self.provider == "anthropic" and self.settings.anthropic_api_key:
            try:
                payload = self._build_anthropic_payload(messages, max_tokens)
                headers = {
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }
                url = f"{self.settings.anthropic_base_url.rstrip('/')}/messages"
                with httpx.Client(timeout=timeout or self.settings.anthropic_timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        self._record_anthropic_usage(data.get("usage", {}))
                        return self._anthropic_content(data)
                    logger.warning("[LLMClient] Error HTTP %s de Anthropic en generate_sync", resp.status_code)
            except Exception as e:
                logger.warning("[LLMClient] Falló generate_sync con Anthropic (%s). Conmutando a contingencia Ollama...", e)

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
                if any(k in self.settings.openai_model for k in ["gpt-6", "gpt-5", "o1", "o3", "luna"]):
                    payload["reasoning_effort"] = "low"
                with httpx.Client(timeout=timeout or self.settings.openai_timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    logger.warning("[LLMClient] Error HTTP %s de OpenAI en generate_sync: %s", resp.status_code, resp.text)
            except Exception as e:
                logger.warning("[LLMClient] Falló generate_sync con OpenAI (%s). Conmutando a contingencia Ollama...", e)

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
        if self.provider == "anthropic":
            if not self.settings.anthropic_api_key:
                return {
                    "active": False,
                    "provider": "anthropic",
                    "model": self.settings.anthropic_model,
                    "error": "No hay ANTHROPIC_API_KEY configurada en .env",
                }
            try:
                headers = {
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                }
                url = f"{self.settings.anthropic_base_url.rstrip('/')}/models"
                async with httpx.AsyncClient(timeout=4.0) as client:
                    response = await client.get(url, params={"limit": 1000}, headers=headers)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    available = any(model.get("id") == self.settings.anthropic_model for model in models)
                    return {
                        "active": available,
                        "provider": "anthropic",
                        "model": self.settings.anthropic_model,
                        "endpoint": self.settings.anthropic_base_url,
                        **({} if available else {"error": "La clave es válida, pero el modelo configurado no aparece disponible para esta cuenta."}),
                    }
                return {
                    "active": False,
                    "provider": "anthropic",
                    "model": self.settings.anthropic_model,
                    "error": f"Anthropic HTTP {response.status_code}",
                }
            except Exception as e:
                return {
                    "active": False,
                    "provider": "anthropic",
                    "model": self.settings.anthropic_model,
                    "error": str(e),
                }

        if self.provider == "gemini":
            if not self.settings.gemini_api_key:
                return {
                    "active": False,
                    "provider": "gemini",
                    "model": self.settings.gemini_model,
                    "error": "No hay GEMINI_API_KEY configurada en .env"
                }
            try:
                headers = {"Authorization": f"Bearer {self.settings.gemini_api_key}"}
                url = f"{self.settings.gemini_base_url.rstrip('/')}/models"
                async with httpx.AsyncClient(timeout=4.0) as client:
                    r = await client.get(url, headers=headers)
                    if r.status_code == 200:
                        return {
                            "active": True,
                            "provider": "gemini",
                            "model": self.settings.gemini_model,
                            "endpoint": self.settings.gemini_base_url
                        }
                    return {
                        "active": False,
                        "provider": "gemini",
                        "model": self.settings.gemini_model,
                        "error": f"Gemini HTTP {r.status_code}"
                    }
            except Exception as e:
                return {
                    "active": False,
                    "provider": "gemini",
                    "model": self.settings.gemini_model,
                    "error": str(e)
                }

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
