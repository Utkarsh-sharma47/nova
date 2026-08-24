"""Structured JSON logs with secret redaction."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from nova.observability.context import get_request_id, get_trace_id

_SECRET_FRAGMENTS = ("authorization", "api_key", "password", "secret", "token", "cookie")
_STANDARD_FIELDS = (
    "duration_ms",
    "status",
    "path",
    "method",
    "http_status",
    "error_code",
)


def _redact(key: str, value: Any) -> Any:
    normalized = key.lower().replace("-", "_")
    if any(fragment in normalized for fragment in _SECRET_FRAGMENTS):
        return "[REDACTED]"
    return value


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str, environment: str) -> None:
        super().__init__()
        self.service = service
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "service": self.service,
            "environment": self.environment,
            "trace_id": getattr(record, "trace_id", None) or get_trace_id(),
            "request_id": getattr(record, "request_id", None) or get_request_id(),
            "event": getattr(record, "event", record.name),
            "message": record.getMessage(),
        }
        for field in _STANDARD_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        extras = getattr(record, "extra_fields", {})
        if isinstance(extras, dict):
            payload.update({_key: _redact(_key, value) for _key, value in extras.items()})
        if record.exc_info and record.exc_info[0]:
            payload["error_type"] = record.exc_info[0].__name__
            payload["exception_present"] = True
        return json.dumps(payload, default=str)


def configure_logging(service: str, environment: str, level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service, environment))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
