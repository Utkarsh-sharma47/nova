"""Request-scoped correlation identifiers."""

from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


def new_id() -> str:
    return str(uuid4())


def get_request_id() -> str | None:
    return request_id_var.get()


def get_trace_id() -> str | None:
    return trace_id_var.get()


def bind_ids(*, request_id: str | None = None, trace_id: str | None = None) -> tuple[str, str]:
    """Bind request/trace IDs into context; generate when missing."""
    rid = request_id or new_id()
    tid = trace_id or rid
    request_id_var.set(rid)
    trace_id_var.set(tid)
    return rid, tid
