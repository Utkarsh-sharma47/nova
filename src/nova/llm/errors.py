"""LLM provider / output errors (ADR-0005)."""

from __future__ import annotations

from typing import Any


class LLMError(Exception):
    """Base LLM failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "LLM_ERROR",
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable
        self.details = details


class LLMTimeoutError(LLMError):
    def __init__(self, message: str = "LLM request timed out", **kwargs: Any) -> None:
        super().__init__(message, code="TIMEOUT", retryable=True, **kwargs)


class LLMProviderError(LLMError):
    def __init__(
        self,
        message: str,
        *,
        retryable: bool = True,
        code: str = "PROVIDER_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, retryable=retryable, details=details)


class LLMOutputError(LLMError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, code="MALFORMED_OUTPUT", retryable=True, **kwargs)


class LLMMalformedOutputError(LLMOutputError):
    """Alias retained for callers expecting this name."""


class RetryExhaustedError(LLMError):
    def __init__(self, message: str = "LLM retries exhausted", **kwargs: Any) -> None:
        super().__init__(message, code="RETRY_EXHAUSTED", retryable=False, **kwargs)
