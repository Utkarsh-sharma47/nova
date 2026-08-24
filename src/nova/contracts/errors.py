"""Application error contract."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from nova.contracts.common import ContractModel


class ErrorType(StrEnum):
    VALIDATION = "ValidationError"
    DOCUMENT_PROCESSING = "DocumentProcessingError"
    AI_PROVIDER = "AIProviderError"
    AI_OUTPUT = "AIOutputError"
    TIMEOUT = "TimeoutError"
    RETRY_EXHAUSTED = "RetryExhaustedError"
    PERSISTENCE = "PersistenceError"
    NOT_FOUND = "NotFoundError"
    CONFLICT = "ConflictError"
    AUTHENTICATION = "AuthenticationError"
    AUTHORIZATION = "AuthorizationError"


class ErrorResponse(ContractModel):
    contract_version: str = "1.0.0"
    error_type: ErrorType
    error_code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] | None = None
    trace_id: UUID | None = None
    request_id: UUID | None = None
    retryable: bool
