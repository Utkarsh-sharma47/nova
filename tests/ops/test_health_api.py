"""API health, readiness, metrics, and correlation header tests."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from nova.api.app import create_app
from nova.config import clear_settings_cache
from nova.db.models import SchemaMeta


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nova:nova@localhost:5432/nova")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    clear_settings_cache()

    with (
        patch("nova.api.app.configure_engine"),
        patch("nova.api.app.dispose_engine"),
    ):
        application = create_app()
        with TestClient(application) as test_client:
            yield test_client
    clear_settings_cache()


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body
    assert response.headers.get("X-Request-ID")
    assert response.headers.get("X-Trace-ID")


def test_health_propagates_incoming_ids(client: TestClient) -> None:
    response = client.get(
        "/health",
        headers={"X-Request-ID": "req-fixed", "X-Trace-ID": "trc-fixed"},
    )
    assert response.headers["X-Request-ID"] == "req-fixed"
    assert response.headers["X-Trace-ID"] == "trc-fixed"


def test_ready_when_schema_present(client: TestClient) -> None:
    meta = SchemaMeta(key="schema_bootstrap", value="0001_schema_meta")
    mock_session = MagicMock()
    mock_session.scalar.return_value = meta
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_session
    mock_cm.__exit__.return_value = False

    with (
        patch("nova.api.routes.health.check_database_ready"),
        patch("nova.api.routes.health.session_scope", return_value=mock_cm),
    ):
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_ready_when_migrations_pending(client: TestClient) -> None:
    mock_session = MagicMock()
    mock_session.scalar.return_value = None
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_session
    mock_cm.__exit__.return_value = False

    with (
        patch("nova.api.routes.health.check_database_ready"),
        patch("nova.api.routes.health.session_scope", return_value=mock_cm),
    ):
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["reason"] == "migrations_pending"


def test_ready_when_database_unavailable(client: TestClient) -> None:
    with patch(
        "nova.api.routes.health.check_database_ready",
        side_effect=OSError("connection refused"),
    ):
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["reason"] == "database_unavailable"


def test_metrics_exposes_prometheus_text(client: TestClient) -> None:
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "nova_http_requests_total" in response.text
    assert "text/plain" in response.headers["content-type"]
