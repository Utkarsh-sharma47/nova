"""HTTP request correlation and completion logging."""

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


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id, trace_id = bind_ids(
            request.headers.get("X-Request-Id"),
            request.headers.get("X-Trace-Id"),
        )
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_seconds = time.perf_counter() - started
        duration_ms = round(duration_seconds * 1000, 3)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Trace-Id"] = trace_id
        observe_http_request(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_seconds=duration_seconds,
        )
        logger.info(
            "request_completed",
            extra={
                "event": "http.request",
                "duration_ms": duration_ms,
                "status": "ok" if response.status_code < 400 else "error",
                "path": request.url.path,
                "method": request.method,
                "http_status": response.status_code,
                "request_id": request_id,
                "trace_id": trace_id,
            },
        )
        return response
