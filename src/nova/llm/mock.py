"""Mock LLM for tests and default local/CI environments (no network, no API key)."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from typing import Any

from nova.llm.errors import LLMOutputError, LLMProviderError, LLMTimeoutError
from nova.llm.port import LLMRequest, LLMResponse

ResponseFactory = Callable[[LLMRequest], LLMResponse | str | dict[str, Any]]


class MockLLM:
    """Deterministic LLMPort implementation for CI and local default."""

    def __init__(
        self,
        *,
        response: str | dict[str, Any] | None = None,
        scripted: Sequence[str | dict[str, Any] | Exception] | None = None,
        factory: ResponseFactory | None = None,
        provider: str = "mock",
        model: str = "mock-extractor-v1",
        latency_ms: int = 1,
        fail_with: Exception | None = None,
        fail_times: int = 0,
        timeout: bool = False,
    ) -> None:
        self.provider = provider
        self.model = model
        self.latency_ms = latency_ms
        self._response = response
        self._scripted = list(scripted or [])
        self._factory = factory
        self._fail_with = fail_with
        self._fail_remaining = fail_times
        self._timeout = timeout
        self.calls: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls.append(request)
        if self._timeout:
            raise LLMTimeoutError(
                "Mock LLM timed out",
                details={"timeout_ms": request.timeout_ms},
            )
        if self._fail_remaining > 0:
            self._fail_remaining -= 1
            if self._fail_with is not None:
                raise self._fail_with
            raise LLMProviderError("Mock LLM transient provider failure")
        if (
            self._fail_with is not None
            and self._response is None
            and self._factory is None
            and not self._scripted
        ):
            raise self._fail_with

        started = time.perf_counter()
        payload = self._next_payload(request)
        elapsed = max(self.latency_ms, int((time.perf_counter() - started) * 1000))
        if isinstance(payload, Exception):
            raise payload
        content = payload if isinstance(payload, str) else json.dumps(payload)
        if request.response_format == "json":
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                raise LLMOutputError("Mock LLM returned non-JSON content") from exc
        return LLMResponse(
            content=content,
            provider=self.provider,
            model=self.model,
            input_tokens=max(1, len(request.messages[-1].content) // 4),
            output_tokens=max(1, len(content) // 4),
            latency_ms=elapsed,
            raw_finish_reason="stop",
        )

    def _next_payload(self, request: LLMRequest) -> str | dict[str, Any] | Exception:
        if self._scripted:
            return self._scripted.pop(0)
        if self._factory is not None:
            result = self._factory(request)
            if isinstance(result, LLMResponse):
                return result.content
            return result
        if self._response is not None:
            return self._response
        if self._fail_with is not None:
            raise self._fail_with
        raise LLMProviderError("MockLLM has no configured response")
