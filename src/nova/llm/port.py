"""Provider-agnostic LLM port (ADR-0005)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from nova.contracts.common import UsageMetrics


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """Supports both message-list and system/user prompt styles."""

    messages: list[LLMMessage] = field(default_factory=list)
    prompt_id: str | None = None
    prompt_version: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    response_schema_name: str | None = None
    response_format: str | None = None
    temperature: float | None = 0.0
    max_tokens: int | None = 1024
    timeout_ms: int = 10_000
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolved_messages(self) -> list[LLMMessage]:
        if self.messages:
            return list(self.messages)
        out: list[LLMMessage] = []
        if self.system_prompt:
            out.append(LLMMessage(role="system", content=self.system_prompt))
        if self.user_prompt:
            out.append(LLMMessage(role="user", content=self.user_prompt))
        return out


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: Any  # str or already-parsed dict/list
    model: str
    provider: str
    prompt_id: str | None = None
    prompt_version: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    usage: UsageMetrics | None = None
    raw: dict[str, Any] | None = None


class LLMPort(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Perform one completion. Must honor timeout_ms."""
