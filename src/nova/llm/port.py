"""LLMPort abstraction (ADR-0005)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LLMMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str


class LLMRequest(BaseModel):
    """Supports message-list and system/user prompt styles (extractor + validator)."""

    model_config = ConfigDict(extra="forbid")

    messages: list[LLMMessage] = Field(default_factory=list)
    response_format: str = "json"
    temperature: float | None = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=4096, ge=1)
    timeout_ms: int = Field(default=60_000, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    prompt_id: str | None = None
    prompt_version: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    response_schema_name: str | None = None

    @model_validator(mode="after")
    def _require_messages_or_prompts(self) -> LLMRequest:
        if self.resolved_messages():
            return self
        raise ValueError("LLMRequest requires messages or system_prompt/user_prompt")

    def resolved_messages(self) -> list[LLMMessage]:
        if self.messages:
            return list(self.messages)
        out: list[LLMMessage] = []
        if self.system_prompt:
            out.append(LLMMessage(role="system", content=self.system_prompt))
        if self.user_prompt:
            out.append(LLMMessage(role="user", content=self.user_prompt))
        return out


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    provider: str
    model: str
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    raw_finish_reason: str | None = None
    prompt_id: str | None = None
    prompt_version: str | None = None


@runtime_checkable
class LLMPort(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...
