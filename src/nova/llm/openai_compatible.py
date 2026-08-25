"""OpenAI-compatible chat + vision adapter behind LLMPort.

Network calls only when credentials are present. Domain code never imports this
module directly — use ``build_default_llm``.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

from nova.llm.errors import LLMProviderError, LLMTimeoutError
from nova.llm.port import LLMRequest, LLMResponse

logger = logging.getLogger("nova.llm.openai")

_DEFAULT_BASE = "https://api.openai.com/v1"
_DEFAULT_MODEL = "gpt-4o-mini"


class OpenAICompatibleLLM:
    """HTTP adapter for OpenAI Chat Completions (text + optional image parts)."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
        provider_name: str = "openai",
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("OpenAICompatibleLLM requires a non-empty api_key")
        self._api_key = api_key.strip()
        self._model = model or _DEFAULT_MODEL
        self._base_url = (base_url or _DEFAULT_BASE).rstrip("/")
        self._provider_name = provider_name

    def complete(self, request: LLMRequest) -> LLMResponse:
        messages = _to_openai_messages(request)
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": request.temperature if request.temperature is not None else 0.0,
        }
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.response_format == "json":
            body["response_format"] = {"type": "json_object"}

        payload = json.dumps(body).encode("utf-8")
        url = f"{self._base_url}/chat/completions"
        http_request = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        timeout_s = max(1.0, request.timeout_ms / 1000.0)
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(http_request, timeout=timeout_s) as response:
                raw = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise LLMTimeoutError(
                "OpenAI request timed out",
                details={"timeout_ms": request.timeout_ms},
            ) from exc
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise LLMProviderError(
                f"OpenAI HTTP {exc.code}",
                details={"status": exc.code, "body": detail},
            ) from exc
        except urllib.error.URLError as exc:
            raise LLMProviderError(
                "OpenAI transport error",
                details={"reason": str(exc.reason)},
            ) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("OpenAI returned non-JSON body") from exc

        choices = parsed.get("choices") or []
        if not choices:
            raise LLMProviderError("OpenAI response missing choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("OpenAI response missing message content")
        usage = parsed.get("usage") or {}
        return LLMResponse(
            content=content,
            provider=self._provider_name,
            model=str(parsed.get("model") or self._model),
            input_tokens=_as_int(usage.get("prompt_tokens")),
            output_tokens=_as_int(usage.get("completion_tokens")),
            latency_ms=latency_ms,
            raw_finish_reason=str(choices[0].get("finish_reason") or "") or None,
            prompt_id=request.prompt_id,
            prompt_version=request.prompt_version,
        )


def _to_openai_messages(request: LLMRequest) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    resolved = request.resolved_messages()
    for index, message in enumerate(resolved):
        is_last_user = index == len(resolved) - 1 and message.role == "user"
        if is_last_user and request.images:
            parts: list[dict[str, Any]] = [{"type": "text", "text": message.content}]
            for image in request.images:
                media = image.media_type if image.media_type != "image/jpg" else "image/jpeg"
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media};base64,{image.data_base64}",
                        },
                    }
                )
            messages.append({"role": message.role, "content": parts})
        else:
            messages.append({"role": message.role, "content": message.content})
    return messages


def _as_int(value: object) -> int | None:
    if isinstance(value, int) and value >= 0:
        return value
    return None
