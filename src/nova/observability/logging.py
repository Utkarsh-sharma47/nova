"""Structured logging and request/trace correlation."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


def new_id() -> str:
    return str(uuid4())


def get_request_id() -> str | None:
    return request_id_var.get()


def get_trace_id() -> str | None:
    return trace_id_var.get()


def bind_correlation(*, request_id: str | None = None, trace_id: str | None = None) -> None:
    if request_id is not None:
        request_id_var.set(request_id)
    if trace_id is not None:
        trace_id_var.set(trace_id)


def clear_correlation() -> None:
    request_id_var.set(None)
    trace_id_var.set(None)


class JsonLogFormatter(logging.Formatter):
    """Minimal JSON log formatter without external dependencies."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = get_request_id()
        tid = get_trace_id()
        if rid:
            payload["request_id"] = rid
        if tid:
            payload["trace_id"] = tid
        for key in (
            "document_id",
            "shipment_id",
            "customer_id",
            "run_id",
            "idempotency_key",
            "idempotency_replay",
            "error_code",
            "status",
            "duration_ms",
            "content_sha256",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            payload["exc_present"] = True
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def ensure_uuid_str(value: str | UUID | None) -> str:
    if value is None:
        return new_id()
    return str(value)
