"""Mock LLM for tests, CI, and evaluation fixtures (no network, no API key)."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from typing import Any

from nova.llm.errors import LLMOutputError, LLMProviderError, LLMTimeoutError
from nova.llm.port import LLMRequest, LLMResponse

ResponseFactory = Callable[[LLMRequest], LLMResponse | str | dict[str, Any]]
Behavior = Callable[[LLMRequest], LLMResponse | Exception | str | dict[str, Any]]


class MockLLM:
    """Deterministic LLMPort for extractor, validator, and evaluation harnesses."""

    def __init__(
        self,
        *,
        response: str | dict[str, Any] | None = None,
        scripted: Sequence[str | dict[str, Any] | Exception] | None = None,
        factory: ResponseFactory | None = None,
        behaviors: Sequence[Behavior] | None = None,
        default_content: str | dict[str, Any] | None = None,
        provider: str = "mock",
        model: str = "mock-llm",
        latency_ms: int = 1,
        delay_ms: int = 0,
        fail_with: Exception | None = None,
        fail_times: int = 0,
        timeout: bool = False,
    ) -> None:
        self.provider = provider
        self.model = model
        self.latency_ms = latency_ms
        self.delay_ms = delay_ms
        self._response = response
        self._scripted = list(scripted or [])
        self._factory = factory
        self._behaviors = list(behaviors or [])
        self._default_content = default_content
        self._fail_with = fail_with
        self._fail_remaining = fail_times
        self._timeout = timeout
        self.calls: list[LLMRequest] = []
        self.call_count = 0

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls.append(request)
        self.call_count += 1
        if self._timeout:
            raise LLMTimeoutError(
                "Mock LLM timed out",
                details={"timeout_ms": request.timeout_ms},
            )
        if self.delay_ms > request.timeout_ms:
            raise LLMTimeoutError(
                f"MockLLM delayed {self.delay_ms}ms beyond timeout {request.timeout_ms}ms"
            )
        if self.delay_ms:
            time.sleep(min(self.delay_ms, 50) / 1000.0)
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
            and not self._behaviors
            and self._default_content is None
        ):
            raise self._fail_with

        started = time.perf_counter()
        payload = self._next_payload(request)
        elapsed = max(
            self.latency_ms,
            self.delay_ms,
            int((time.perf_counter() - started) * 1000),
        )
        if isinstance(payload, Exception):
            raise payload
        if isinstance(payload, LLMResponse):
            return payload
        content = payload if isinstance(payload, str) else json.dumps(payload)
        if request.response_format == "json":
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                raise LLMOutputError("Mock LLM returned non-JSON content") from exc
        messages = request.resolved_messages()
        last = messages[-1].content if messages else ""
        return LLMResponse(
            content=content,
            provider=self.provider,
            model=self.model,
            input_tokens=max(1, len(last) // 4),
            output_tokens=max(1, len(content) // 4),
            latency_ms=elapsed,
            raw_finish_reason="stop",
            prompt_id=request.prompt_id,
            prompt_version=request.prompt_version,
        )

    @property
    def timeout(self) -> bool:
        return self._timeout

    @timeout.setter
    def timeout(self, value: bool) -> None:
        self._timeout = value

    @property
    def fail_with(self) -> Exception | None:
        return self._fail_with

    @fail_with.setter
    def fail_with(self, value: Exception | None) -> None:
        self._fail_with = value

    @property
    def response(self) -> str | dict[str, Any] | None:
        return self._response

    @response.setter
    def response(self, value: str | dict[str, Any] | None) -> None:
        self._response = value

    @property
    def scripted(self) -> list[Any]:
        return self._scripted

    @scripted.setter
    def scripted(self, value: list[Any]) -> None:
        self._scripted = list(value)

    @property
    def behaviors(self) -> list[Behavior]:
        return self._behaviors

    @behaviors.setter
    def behaviors(self, value: list[Behavior]) -> None:
        self._behaviors = list(value)

    def _next_payload(
        self, request: LLMRequest
    ) -> str | dict[str, Any] | Exception | LLMResponse:
        if self._behaviors:
            return self._behaviors.pop(0)(request)
        if self._scripted:
            return self._scripted.pop(0)
        if self._factory is not None:
            result = self._factory(request)
            if isinstance(result, LLMResponse):
                return result
            return result
        if self._response is not None:
            return self._response
        if self._default_content is not None:
            return self._default_content
        if self._fail_with is not None:
            raise self._fail_with
        raise LLMProviderError("MockLLM has no configured response")


def scripted_json(payload: dict[str, Any]) -> Behavior:
    def _fn(_request: LLMRequest) -> dict[str, Any]:
        return payload

    return _fn


def scripted_text(text: str) -> Behavior:
    def _fn(_request: LLMRequest) -> str:
        return text

    return _fn


def scripted_error(exc: Exception) -> Behavior:
    def _fn(_request: LLMRequest) -> Exception:
        return exc

    return _fn
