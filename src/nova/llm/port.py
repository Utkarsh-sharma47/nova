"""LLMPort abstraction — no provider hard-coding in domain logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMRequest:
    messages: list[LLMMessage]
    response_format: str = "json"
    temperature: float | None = 0.0
    timeout_ms: int = 60_000
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: dict[str, Any] | None = None


class LLMPort(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Synchronous completion. Raise LLMError subclasses on failure."""
        ...
