"""Domain and application errors safe to project through the API."""

from __future__ import annotations

from typing import Any


class NovaError(Exception):
    code = "INTERNAL_ERROR"
    status_code = 500
    retryable = False
    safe_message = "An internal error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message or self.safe_message)
        self.message = message or self.safe_message
        self.details = details or {}


class ValidationFailure(NovaError):
    code = "VALIDATION_FAILED"
    status_code = 422
    safe_message = "The request failed validation."


class UnsupportedMediaType(ValidationFailure):
    code = "UNSUPPORTED_MEDIA_TYPE"
    safe_message = "The document media type is not supported."


class DocumentUnreadable(ValidationFailure):
    code = "DOCUMENT_UNREADABLE"
    safe_message = "The document could not be read."


class PayloadTooLarge(ValidationFailure):
    code = "PAYLOAD_TOO_LARGE"
    status_code = 413
    safe_message = "The document exceeds the configured size limit."


class UnsafeFilename(ValidationFailure):
    code = "UNSAFE_FILENAME"
    safe_message = "The document filename is unsafe."


class MissingIdempotencyKey(NovaError):
    code = "MISSING_IDEMPOTENCY_KEY"
    status_code = 400
    safe_message = "Idempotency-Key header is required."


class IdempotencyMismatch(NovaError):
    code = "IDEMPOTENCY_KEY_REUSE_MISMATCH"
    status_code = 409
    safe_message = "The idempotency key was already used for a different request."


class ExternalReferenceConflict(NovaError):
    code = "EXTERNAL_REF_CONFLICT"
    status_code = 409
    safe_message = "The external reference belongs to different document content."


class NotFound(NovaError):
    status_code = 404
    safe_message = "The requested resource was not found."


class CustomerNotFound(NotFound):
    code = "CUSTOMER_NOT_FOUND"


class DocumentNotFound(NotFound):
    code = "DOCUMENT_NOT_FOUND"


class ShipmentNotFound(NotFound):
    code = "SHIPMENT_NOT_FOUND"


class ValidationNotFound(NotFound):
    code = "VALIDATION_NOT_FOUND"
    safe_message = "Validation result is not available yet."
    retryable = True


class DecisionNotFound(NotFound):
    code = "DECISION_NOT_FOUND"
    safe_message = "Decision result is not available yet."
    retryable = True


class InvalidLifecycleTransition(NovaError):
    code = "INVALID_LIFECYCLE_TRANSITION"
    status_code = 409
    safe_message = "The requested lifecycle transition is not allowed."
