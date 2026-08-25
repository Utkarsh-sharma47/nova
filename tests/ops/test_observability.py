"""Observability and configuration tests for Phase 3 ops quality."""

from __future__ import annotations

import json
import logging

import pytest
from pydantic import ValidationError

from nova.config import Settings, clear_settings_cache
from nova.observability.context import bind_ids, clear_ids
from nova.observability.logging import JsonFormatter, configure_logging


@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    clear_settings_cache()
    clear_ids()
    yield
    clear_settings_cache()
    clear_ids()


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
    assert payload["request_id"] == "req-1"
    assert payload["trace_id"] == "trc-1"


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
    record.extra_fields = {"api_key": "sk-secret", "path": "/health", "blob": b"secret-doc"}  # type: ignore[attr-defined]
    payload = json.loads(formatter.format(record))
    assert payload["api_key"] == "[REDACTED]"
    assert payload["blob"] == "[REDACTED]"
    assert payload["path"] == "/health"


def test_configure_logging_sets_json_handler() -> None:
    configure_logging(service="nova-api", environment="test", level="INFO")
    root = logging.getLogger()
    assert root.handlers
    assert isinstance(root.handlers[0].formatter, JsonFormatter)


def test_settings_reject_invalid_log_level() -> None:
    with pytest.raises(ValidationError):
        Settings(  # type: ignore[call-arg]
            database_url="postgresql+psycopg://nova:nova@localhost:5432/nova",
            log_level="VERBOSE",
            _env_file=None,
        )


def test_settings_accept_environment_alias() -> None:
    settings = Settings(  # type: ignore[call-arg]
        database_url="postgresql+psycopg://nova:nova@localhost:5432/nova",
        ENVIRONMENT="test",
        _env_file=None,
    )
    assert settings.app_env == "test"


def test_validate_runtime_rejects_placeholder_token() -> None:
    settings = Settings(  # type: ignore[call-arg]
        app_env="local",
        api_auth_token="change-me",
        database_url="postgresql+psycopg://nova:nova@localhost:5432/nova",
        _env_file=None,
    )
    with pytest.raises(ValueError, match="placeholder"):
        settings.validate_runtime()
