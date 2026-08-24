"""LLM error types (ADR-0005)."""

from __future__ import annotations

from typing import Any


class LLMError(Exception):
    code: str = "AI_PROVIDER_ERROR"
    retryable: bool = False

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMTimeoutError(LLMError):
    code = "AI_PROVIDER_TIMEOUT"
    retryable = True


class LLMProviderError(LLMError):
    code = "AI_PROVIDER_FAILURE"
    retryable = True


class LLMOutputError(LLMError):
    code = "AI_OUTPUT_ERROR"
    retryable = True


class LLMMalformedOutputError(LLMOutputError):
    code = "AI_OUTPUT_MALFORMED"
    retryable = True


class RetryExhaustedError(LLMError):
    code = "AI_RETRY_EXHAUSTED"
    retryable = False
