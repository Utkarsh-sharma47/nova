"""HTTP middleware: request/trace IDs, latency logging, metrics."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from nova.observability.context import bind_ids
from nova.observability.metrics import observe_http_request

logger = logging.getLogger("nova.http")

_REQUEST_ID_HEADERS = ("x-request-id", "x-correlation-id")
_TRACE_ID_HEADERS = ("x-trace-id",)


def _first_header(request: Request, names: tuple[str, ...]) -> str | None:
    for name in names:
        value = request.headers.get(name)
        if value and value.strip():
            return value.strip()
    return None


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id, trace_id = bind_ids(
            request_id=_first_header(request, _REQUEST_ID_HEADERS),
            trace_id=_first_header(request, _TRACE_ID_HEADERS),
        )
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "unhandled_error",
                extra={
                    "event": "http.request.error",
                    "duration_ms": round(duration_ms, 3),
                    "status": "error",
                    "path": request.url.path,
                    "method": request.method,
                    "http_status": 500,
                    "request_id": request_id,
                    "trace_id": trace_id,
                },
            )
            observe_http_request(
                method=request.method,
                path=request.url.path,
                status=500,
                duration_seconds=duration_ms / 1000,
            )
            raise
        else:
            duration_ms = (time.perf_counter() - start) * 1000
            duration_s = duration_ms / 1000
            observe_http_request(
                method=request.method,
                path=request.url.path,
                status=status,
                duration_seconds=duration_s,
            )
            level = logging.ERROR if status >= 500 else logging.INFO
            logger.log(
                level,
                "request_completed",
                extra={
                    "event": "http.request",
                    "duration_ms": round(duration_ms, 3),
                    "status": "ok" if status < 400 else "error",
                    "path": request.url.path,
                    "method": request.method,
                    "http_status": status,
                    "request_id": request_id,
                    "trace_id": trace_id,
                },
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            return response
