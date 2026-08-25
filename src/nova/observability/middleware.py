"""Pure ASGI middleware for correlation IDs, metrics, and request logging.

Uses raw ASGI instead of BaseHTTPMiddleware to avoid Starlette exception-handler
edge cases when domain errors are raised from routes.
"""

from __future__ import annotations

import logging
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nova.observability.context import bind_ids, clear_ids
from nova.observability.metrics import observe_http_request

logger = logging.getLogger("nova.http")


class ObservabilityMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request_id, trace_id = bind_ids(
            headers.get("x-request-id"),
            headers.get("x-trace-id"),
        )
        state = scope.setdefault("state", {})
        if isinstance(state, dict):
            state["request_id"] = request_id
            state["trace_id"] = trace_id

        started = time.perf_counter()
        status_code = 500
        path = scope.get("path", "unmatched")
        method = scope.get("method", "GET")

        async def send_with_headers(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 500))
                raw_headers = list(message.get("headers", []))
                raw_headers.append((b"x-request-id", request_id.encode("latin-1")))
                raw_headers.append((b"x-trace-id", trace_id.encode("latin-1")))
                message = {**message, "headers": raw_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        finally:
            duration_seconds = time.perf_counter() - started
            duration_ms = round(duration_seconds * 1000, 3)
            observe_http_request(
                method=method,
                path=str(path),
                status=status_code,
                duration_seconds=duration_seconds,
            )
            logger.info(
                "request_completed",
                extra={
                    "event": "http.request",
                    "duration_ms": duration_ms,
                    "status": "ok" if status_code < 400 else "error",
                    "path": path,
                    "method": method,
                    "http_status": status_code,
                    "request_id": request_id,
                    "trace_id": trace_id,
                },
            )
            clear_ids()
