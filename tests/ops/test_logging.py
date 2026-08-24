"""Structured logging schema and redaction tests."""

from __future__ import annotations

import json
import logging

from nova.observability.context import bind_ids
from nova.observability.logging import JsonFormatter, configure_logging


def test_json_formatter_includes_stable_schema_fields() -> None:
    bind_ids(request_id="req-1", trace_id="trc-1")
    formatter = JsonFormatter(service="nova-api", environment="test")
    record = logging.LogRecord(
        name="nova.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.event = "unit.test"  # type: ignore[attr-defined]
    record.duration_ms = 12.5  # type: ignore[attr-defined]
    record.status = "ok"  # type: ignore[attr-defined]
    record.path = "/health"  # type: ignore[attr-defined]
    record.method = "GET"  # type: ignore[attr-defined]
    record.http_status = 200  # type: ignore[attr-defined]

    payload = json.loads(formatter.format(record))
    for key in (
        "timestamp",
        "level",
        "service",
        "environment",
        "trace_id",
        "request_id",
        "event",
        "duration_ms",
        "status",
    ):
        assert key in payload
    assert payload["service"] == "nova-api"
    assert payload["request_id"] == "req-1"
    assert payload["trace_id"] == "trc-1"
    assert payload["event"] == "unit.test"


def test_extra_fields_redact_secrets() -> None:
    formatter = JsonFormatter(service="nova-api", environment="test")
    record = logging.LogRecord(
        name="nova.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="auth",
        args=(),
        exc_info=None,
    )
    record.extra_fields = {"api_key": "sk-secret", "path": "/health"}  # type: ignore[attr-defined]
    payload = json.loads(formatter.format(record))
    assert payload["api_key"] == "[REDACTED]"
    assert payload["path"] == "/health"


def test_configure_logging_sets_json_handler() -> None:
    configure_logging(service="nova-api", environment="test", level="INFO")
    root = logging.getLogger()
    assert root.handlers
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
