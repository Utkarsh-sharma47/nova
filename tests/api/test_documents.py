"""Document ingestion API integration tests (requires PostgreSQL)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nova.api.main import create_app
from nova.config import clear_settings_cache
from nova.persistence.repositories import CustomerRepository

pytestmark = pytest.mark.integration


@pytest.fixture()
def integration_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, str]]:
    db_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://nova:nova@localhost:5432/nova_test",
    )
    token = "test-token-not-for-production"
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("API_AUTH_TOKEN", token)
    monkeypatch.setenv("DOCUMENT_STORAGE_PATH", str(uploads))
    monkeypatch.setenv("APP_ENV", "test")
    clear_settings_cache()
    yield {"database_url": db_url, "token": token, "uploads": str(uploads)}
    clear_settings_cache()


@pytest.fixture()
def migrated_db(integration_env: dict[str, str]) -> Iterator[str]:
    url = integration_env["database_url"]

    async def _probe() -> None:
        engine = create_async_engine(url, pool_pre_ping=True)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        finally:
            await engine.dispose()

    import asyncio

    try:
        asyncio.run(_probe())
    except Exception as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")

    from alembic import command
    from alembic.config import Config

    os.environ["DATABASE_URL"] = url
    command.upgrade(Config("alembic.ini"), "head")
    yield url

    async def _truncate() -> None:
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "TRUNCATE idempotency_records, verification_runs, document_versions, "
                    "documents, shipments, customers RESTART IDENTITY CASCADE"
                )
            )
        await engine.dispose()

    asyncio.run(_truncate())


@pytest.fixture()
def api_client(
    integration_env: dict[str, str], migrated_db: str
) -> Iterator[tuple[TestClient, str]]:
    clear_settings_cache()
    app = create_app()
    with TestClient(app) as client:
        yield client, integration_env["token"]


def _seed_customer(database_url: str) -> str:
    import asyncio

    async def _run() -> str:
        engine = create_async_engine(database_url, pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        async with factory() as session:
            repo = CustomerRepository(session)
            customer = await repo.create(name=f"Test Customer {uuid4().hex[:6]}")
            await session.commit()
            customer_id = str(customer.customer_id)
        await engine.dispose()
        return customer_id

    return asyncio.run(_run())


def test_ingest_requires_auth(
    api_client: tuple[TestClient, str], migrated_db: str
) -> None:
    client, _token = api_client
    customer_id = _seed_customer(migrated_db)
    resp = client.post(
        "/v1/documents",
        data={"customer_id": customer_id},
        files={"file": ("a.txt", b"hello", "text/plain")},
        headers={"Idempotency-Key": "idem-key-01"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] in {"UNAUTHENTICATED", "INVALID_API_KEY"}


def test_ingest_requires_idempotency_key(
    api_client: tuple[TestClient, str], migrated_db: str
) -> None:
    client, token = api_client
    customer_id = _seed_customer(migrated_db)
    resp = client.post(
        "/v1/documents",
        data={"customer_id": customer_id},
        files={"file": ("a.txt", b"hello", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"


def test_ingest_success_and_replay(
    api_client: tuple[TestClient, str], migrated_db: str
) -> None:
    client, token = api_client
    customer_id = _seed_customer(migrated_db)
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "idem-key-replay-01",
    }
    data = {"customer_id": customer_id, "document_type": "INVOICE"}

    first = client.post(
        "/v1/documents",
        data=data,
        files={"file": ("invoice.txt", b"invoice-bytes-1", "text/plain")},
        headers=headers,
    )
    assert first.status_code == 202, first.text
    body = first.json()
    assert body["status"] == "ACCEPTED"
    assert body["idempotent_replay"] is False
    assert body["document_id"]
    assert body["run_id"]

    second = client.post(
        "/v1/documents",
        data=data,
        files={"file": ("invoice.txt", b"invoice-bytes-1", "text/plain")},
        headers=headers,
    )
    assert second.status_code == 202, second.text
    replay = second.json()
    assert replay["idempotent_replay"] is True
    assert replay["document_id"] == body["document_id"]
    assert replay["run_id"] == body["run_id"]


def test_ingest_idempotency_mismatch(
    api_client: tuple[TestClient, str], migrated_db: str
) -> None:
    client, token = api_client
    customer_id = _seed_customer(migrated_db)
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "idem-key-mismatch-01",
    }
    first = client.post(
        "/v1/documents",
        data={"customer_id": customer_id, "document_type": "OTHER"},
        files={"file": ("a.txt", b"payload-a", "text/plain")},
        headers=headers,
    )
    assert first.status_code == 202, first.text

    second = client.post(
        "/v1/documents",
        data={"customer_id": customer_id, "document_type": "OTHER"},
        files={"file": ("a.txt", b"payload-b-different", "text/plain")},
        headers=headers,
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSE_MISMATCH"


def test_ingest_rejects_unsupported_media(
    api_client: tuple[TestClient, str], migrated_db: str
) -> None:
    client, token = api_client
    customer_id = _seed_customer(migrated_db)
    resp = client.post(
        "/v1/documents",
        data={"customer_id": customer_id},
        files={"file": ("x.bin", b"\x00\x01", "application/octet-stream")},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "idem-key-media-01",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "UNSUPPORTED_DOCUMENT_TYPE"


def test_ingest_x_api_key(
    api_client: tuple[TestClient, str], migrated_db: str
) -> None:
    client, token = api_client
    customer_id = _seed_customer(migrated_db)
    resp = client.post(
        "/v1/documents",
        data={"customer_id": customer_id},
        files={"file": ("a.txt", b"hello-x-api", "text/plain")},
        headers={
            "X-API-Key": token,
            "Idempotency-Key": "idem-key-xapi-01",
        },
    )
    assert resp.status_code == 202, resp.text
