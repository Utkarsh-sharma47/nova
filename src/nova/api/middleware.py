"""ASGI middleware for correlation IDs."""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nova.observability.logging import bind_correlation, clear_correlation, ensure_uuid_str


class CorrelationIdMiddleware:
    """Pure ASGI middleware (avoids BaseHTTPMiddleware exception-handler issues)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        request_id = ensure_uuid_str(headers.get("x-request-id"))
        trace_id = ensure_uuid_str(headers.get("x-trace-id"))
        bind_correlation(request_id=request_id, trace_id=trace_id)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))
                raw_headers.append((b"x-request-id", request_id.encode("latin-1")))
                raw_headers.append((b"x-trace-id", trace_id.encode("latin-1")))
                message = {**message, "headers": raw_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        finally:
            clear_correlation()
