"""Application exception types mapped to the Phase 2 API error model."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error."""

    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."
    http_status: int = 500
    retryable: bool = False

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        self.message = message or type(self).message
        self.details = details
        if code is not None:
            self.code = code
        super().__init__(self.message)


class BadRequestError(AppError):
    code = "BAD_REQUEST"
    message = "Malformed request."
    http_status = 400


class MissingIdempotencyKeyError(BadRequestError):
    code = "MISSING_IDEMPOTENCY_KEY"
    message = "Idempotency-Key header is required for document ingestion."


class UnauthenticatedError(AppError):
    code = "UNAUTHENTICATED"
    message = "Authentication required."
    http_status = 401


class InvalidApiKeyError(AppError):
    code = "INVALID_API_KEY"
    message = "Invalid API key."
    http_status = 401


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    message = "Not allowed."
    http_status = 403


class NotFoundError(AppError):
    code = "NOT_FOUND"
    message = "Resource not found."
    http_status = 404


class CustomerNotFoundError(NotFoundError):
    code = "CUSTOMER_NOT_FOUND"
    message = "No customer exists for the given customer_id."


class ShipmentNotFoundError(NotFoundError):
    code = "SHIPMENT_NOT_FOUND"
    message = "No shipment exists for the given shipment_id."


class DocumentNotFoundError(NotFoundError):
    code = "DOCUMENT_NOT_FOUND"
    message = "No document exists for the given document_id."


class ConflictError(AppError):
    code = "CONFLICT"
    message = "Request conflicts with current state."
    http_status = 409


class IdempotencyKeyReuseMismatchError(ConflictError):
    code = "IDEMPOTENCY_KEY_REUSE_MISMATCH"
    message = "Idempotency-Key was reused with a different request fingerprint."


class ExternalRefConflictError(ConflictError):
    code = "EXTERNAL_REF_CONFLICT"
    message = "external_ref already exists with different document content."


class ValidationFailedError(AppError):
    code = "VALIDATION_FAILED"
    message = "Request validation failed."
    http_status = 422


class UnsupportedDocumentTypeError(ValidationFailedError):
    code = "UNSUPPORTED_DOCUMENT_TYPE"
    message = "Document type or media type is not supported."


class PayloadTooLargeError(ValidationFailedError):
    code = "PAYLOAD_TOO_LARGE"
    message = "Uploaded document exceeds the maximum allowed size."
    http_status = 413


class InvalidDocumentTransitionAppError(ConflictError):
    code = "INVALID_DOCUMENT_TRANSITION"
    message = "Requested document status transition is not allowed."


class PersistenceError(AppError):
    code = "PERSISTENCE_ERROR"
    message = "Database operation failed."
    http_status = 503
    retryable = True


class DependencyUnavailableError(AppError):
    code = "DEPENDENCY_UNAVAILABLE"
    message = "A required dependency is unavailable."
    http_status = 503
    retryable = True


class StorageError(AppError):
    code = "STORAGE_ERROR"
    message = "Document storage operation failed."
    http_status = 500
