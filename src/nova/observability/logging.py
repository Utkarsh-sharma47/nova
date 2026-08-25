"""Structured JSON logs with secret redaction.

Stable log schema fields:
  timestamp, level, service, environment, trace_id, request_id,
  event, message, duration_ms, status, path, method, http_status, error_type

Never log secrets, API keys, Authorization headers, or document contents.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from nova.observability.context import get_request_id, get_trace_id

_SECRET_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "password",
        "secret",
        "token",
        "llm_api_key",
        "database_url",
        "cookie",
        "set-cookie",
        "content",
        "blob",
        "document_bytes",
        "body",
    }
)
_STANDARD_FIELDS = (
    "duration_ms",
    "status",
    "path",
    "method",
    "http_status",
    "error_code",
    "error_type",
)


def _redact(key: str, value: Any) -> Any:
    normalized = key.lower().replace("-", "_")
    if (
        normalized in _SECRET_KEYS
        or normalized.endswith("_key")
        or normalized.endswith("_token")
        or any(fragment in normalized for fragment in ("password", "secret", "authorization"))
    ):
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
        extras = getattr(record, "extra_fields", None)
        if isinstance(extras, dict):
            payload.update({str(key): _redact(str(key), value) for key, value in extras.items()})
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
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
