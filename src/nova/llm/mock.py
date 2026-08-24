"""MockLLM constructor shapes expected by evaluation fixtures."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from nova.contracts.common import UsageMetrics
from nova.llm.errors import LLMProviderError, LLMTimeoutError
from nova.llm.port import LLMPort, LLMRequest, LLMResponse

Behavior = Callable[[LLMRequest], LLMResponse | Exception | str | dict[str, Any]]


@dataclass
class MockLLM:
    """Scripted LLM for CI and evaluation fixtures."""

    response: Any | None = None
    timeout: bool = False
    fail_with: Exception | None = None
    scripted: list[Any] = field(default_factory=list)
    behaviors: list[Behavior] = field(default_factory=list)
    default_content: str | dict[str, Any] | None = None
    model: str = "mock-llm"
    provider: str = "mock"
    call_count: int = 0
    delay_ms: int = 0

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        if self.timeout:
            raise LLMTimeoutError("MockLLM timeout")
        if self.fail_with is not None:
            raise self.fail_with
        if self.delay_ms > request.timeout_ms:
            raise LLMTimeoutError(
                f"MockLLM delayed {self.delay_ms}ms beyond timeout {request.timeout_ms}ms"
            )
        if self.delay_ms:
            time.sleep(min(self.delay_ms, 50) / 1000.0)

        outcome: Any
        if self.behaviors:
            outcome = self.behaviors.pop(0)(request)
        elif self.scripted:
            outcome = self.scripted.pop(0)
        elif self.response is not None:
            outcome = self.response
        elif self.default_content is not None:
            outcome = self.default_content
        else:
            raise LLMProviderError("MockLLM has no scripted behavior")

        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, LLMResponse):
            return outcome

        content: Any = outcome
        if isinstance(outcome, dict):
            # Agent judgment path prefers JSON string for json.loads
            content = json.dumps(outcome)

        usage = UsageMetrics(
            input_tokens=10,
            output_tokens=20,
            latency_ms=max(self.delay_ms, 1),
            attempt=1,
        )
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            prompt_id=request.prompt_id,
            prompt_version=request.prompt_version,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=usage.latency_ms,
            usage=usage,
        )


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


_MOCK_AS_PORT: LLMPort = MockLLM(response={"outcome": "UNCERTAIN", "reason": "default"})
