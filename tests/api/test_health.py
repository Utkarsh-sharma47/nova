"""Health unit tests with mocked database."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from nova.api.errors import register_exception_handlers
from nova.api.middleware import CorrelationIdMiddleware
from nova.api.routes import health
from nova.config import clear_settings_cache
from nova.infrastructure.storage import LocalFilesystemDocumentStorage
from nova.persistence.database import Database


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://nova:nova@localhost:5432/nova_test")
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token-not-for-production")
    clear_settings_cache()

    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health.router)

    mock_db = AsyncMock(spec=Database)
    mock_db.ping = AsyncMock(return_value=True)
    app.state.database = mock_db
    app.state.storage = LocalFilesystemDocumentStorage(tmp_path / "uploads")

    with TestClient(app) as test_client:
        yield test_client
    clear_settings_cache()


def test_health_no_auth(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_ok(client: TestClient) -> None:
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "ok"


def test_ready_db_fail(client: TestClient) -> None:
    client.app.state.database.ping = AsyncMock(return_value=False)  # type: ignore[attr-defined]
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["status"] == "not_ready"
