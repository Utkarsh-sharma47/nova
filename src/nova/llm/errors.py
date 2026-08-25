"""LLM port error types (ADR-0005)."""

from __future__ import annotations

from typing import Any


class LLMError(Exception):
    retryable: bool = False
    code: str = "AI_PROVIDER_ERROR"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMTimeoutError(LLMError):
    retryable = True
    code = "AI_PROVIDER_TIMEOUT"


class LLMProviderError(LLMError):
    retryable = True
    code = "AI_PROVIDER_ERROR"


class LLMOutputError(LLMError):
    retryable = True
    code = "AI_OUTPUT_INVALID"


class LLMMalformedOutputError(LLMOutputError):
    retryable = True
    code = "AI_OUTPUT_MALFORMED"


class RetryExhaustedError(LLMError):
    retryable = False
    code = "AI_RETRY_EXHAUSTED"
