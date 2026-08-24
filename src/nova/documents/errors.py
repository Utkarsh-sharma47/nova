"""Document processing error types and DOC_* codes."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from nova.contracts.errors import ErrorResponse, ErrorType


class DocumentProcessingError(Exception):
    """Raised when document validation or processing fails in a typed way."""

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
        trace_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.retryable = retryable
        self.details = details
        self.trace_id = trace_id
        self.request_id = request_id

    def to_error_response(self) -> ErrorResponse:
        return ErrorResponse(
            error_type=ErrorType.DOCUMENT_PROCESSING,
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            trace_id=self.trace_id,
            request_id=self.request_id,
            retryable=self.retryable,
        )


DOC_UNSUPPORTED_MEDIA_TYPE = "DOC_UNSUPPORTED_MEDIA_TYPE"
DOC_UNSUPPORTED_EXTENSION = "DOC_UNSUPPORTED_EXTENSION"
DOC_MIME_MISMATCH = "DOC_MIME_MISMATCH"
DOC_PAYLOAD_TOO_LARGE = "DOC_PAYLOAD_TOO_LARGE"
DOC_EMPTY = "DOC_EMPTY"
DOC_CORRUPT = "DOC_CORRUPT"
DOC_UNREADABLE = "DOC_UNREADABLE"
DOC_INVALID_FILENAME = "DOC_INVALID_FILENAME"
DOC_PATH_TRAVERSAL = "DOC_PATH_TRAVERSAL"
DOC_TOO_MANY_PAGES = "DOC_TOO_MANY_PAGES"
DOC_INTERNAL = "DOC_INTERNAL"
