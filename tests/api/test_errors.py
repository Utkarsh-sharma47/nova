"""API error envelope tests."""

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
from nova.domain.errors import NotFoundError
from nova.infrastructure.storage import LocalFilesystemDocumentStorage
from nova.persistence.database import Database


@pytest.fixture()
def error_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://nova:nova@localhost:5432/nova_test")
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token-not-for-production")
    clear_settings_cache()

    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health.router)

    @app.get("/boom")
    async def boom() -> None:
        raise NotFoundError(message="missing", details={"id": "x"})

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret stack")

    mock_db = AsyncMock(spec=Database)
    mock_db.ping = AsyncMock(return_value=True)
    app.state.database = mock_db
    app.state.storage = LocalFilesystemDocumentStorage(tmp_path / "uploads")

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    clear_settings_cache()


def test_app_error_envelope(error_client: TestClient) -> None:
    resp = error_client.get("/boom")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["retryable"] is False
    assert "trace_id" in body["error"]
    assert "X-Trace-Id" in resp.headers


def test_unhandled_hides_internals(error_client: TestClient) -> None:
    resp = error_client.get("/crash")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "secret stack" not in resp.text
