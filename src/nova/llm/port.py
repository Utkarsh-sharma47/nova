"""LLMPort abstraction (ADR-0005)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class LLMMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str


class LLMRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[LLMMessage] = Field(min_length=1)
    response_format: str = "json"
    temperature: float | None = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=4096, ge=1)
    timeout_ms: int = Field(default=60_000, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    prompt_id: str | None = None
    prompt_version: str | None = None


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    provider: str
    model: str
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    raw_finish_reason: str | None = None


@runtime_checkable
class LLMPort(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...
