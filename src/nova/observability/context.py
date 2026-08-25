"""Request-local correlation IDs."""

from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)


def bind_ids(request_id: str | None = None, trace_id: str | None = None) -> tuple[str, str]:
    request_value = request_id or str(uuid4())
    trace_value = trace_id or str(uuid4())
    _request_id.set(request_value)
    _trace_id.set(trace_value)
    return request_value, trace_value


def get_request_id() -> str | None:
    return _request_id.get()


def get_trace_id() -> str | None:
    return _trace_id.get()
