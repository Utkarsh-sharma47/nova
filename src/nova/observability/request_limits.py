"""Reject oversized HTTP bodies early using Content-Length when present."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from nova.config import Settings


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, settings: Settings) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._max_bytes = settings.max_request_body_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "INVALID_CONTENT_LENGTH",
                            "message": "Content-Length must be an integer.",
                            "trace_id": str(getattr(request.state, "trace_id", "unavailable")),
                            "retryable": False,
                        }
                    },
                )
            if length > self._max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": "Request body exceeds the configured size limit.",
                            "trace_id": str(getattr(request.state, "trace_id", "unavailable")),
                            "retryable": False,
                        }
                    },
                )
        return await call_next(request)
