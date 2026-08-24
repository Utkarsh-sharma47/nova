"""HTTP error envelope helpers and exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from nova.domain.errors import AppError
from nova.observability.logging import get_logger, get_trace_id, new_id

logger = get_logger(__name__)


def error_envelope(
    *,
    code: str,
    message: str,
    retryable: bool,
    details: dict[str, Any] | None = None,
    trace_id: str | None = None,
    status_code: int = 500,
) -> JSONResponse:
    tid = trace_id or get_trace_id() or new_id()
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "trace_id": tid,
            "retryable": retryable,
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body, headers={"X-Trace-Id": tid})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "app_error",
            extra={"error_code": exc.code, "status": exc.http_status},
        )
        return error_envelope(
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
            details=exc.details,
            status_code=exc.http_status,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_envelope(
            code="VALIDATION_FAILED",
            message="Request validation failed.",
            retryable=False,
            details={"errors": exc.errors()},
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        message = str(exc.detail) if exc.detail else "HTTP error."
        return error_envelope(
            code=code,
            message=message,
            retryable=False,
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error")
        return error_envelope(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            retryable=False,
            status_code=500,
        )
