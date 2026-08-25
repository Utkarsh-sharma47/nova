from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from nova.api.app import create_app
from nova.config import Settings
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import Base, Customer

AUTH = {"X-API-Key": "nova-test-token"}


@pytest.fixture
def client(tmp_path: Path) -> Iterator[tuple[TestClient, UUID]]:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'nova.db'}",
        document_storage_path=str(tmp_path / "documents"),
    )
    with TestClient(create_app(settings)) as test_client:
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        with session_scope() as session:
            session.add(Customer(customer_id=customer_id, name="Test Customer", status="active"))
        yield test_client, customer_id


def upload(
    client: TestClient,
    customer_id: UUID,
    *,
    key: str = "request-key-0001",
    body: bytes = b"invoice number 42",
    content_type: str = "text/plain",
    filename: str = "invoice.txt",
) -> object:
    return client.post(
        "/v1/documents",
        headers={**AUTH, "Idempotency-Key": key},
        data={"customer_id": str(customer_id), "document_type": "INVOICE"},
        files={"file": (filename, body, content_type)},
    )


def test_health_and_ready(client: tuple[TestClient, UUID]) -> None:
    test_client, _ = client
    assert test_client.get("/health").json() == {"status": "ok"}
    ready = test_client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"] == {"database": "ok", "object_storage": "ok"}
    assert ready.headers["X-Request-Id"]
    assert ready.headers["X-Trace-Id"]
    metrics = test_client.get("/metrics")
    assert metrics.status_code == 200
    assert "nova_http_requests_total" in metrics.text


def test_auth_and_missing_idempotency_key(client: tuple[TestClient, UUID]) -> None:
    test_client, customer_id = client
    unauthorized = test_client.post(
        "/v1/documents",
        data={"customer_id": str(customer_id)},
        files={"file": ("x.txt", b"x", "text/plain")},
    )
    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "UNAUTHENTICATED"
    missing = test_client.post(
        "/v1/documents",
        headers=AUTH,
        data={"customer_id": str(customer_id)},
        files={"file": ("x.txt", b"x", "text/plain")},
    )
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "MISSING_IDEMPOTENCY_KEY"


def test_ingest_replay_conflict_and_gets(client: tuple[TestClient, UUID]) -> None:
    test_client, customer_id = client
    first = upload(test_client, customer_id)
    assert first.status_code == 202
    body = first.json()
    assert body["status"] == "ACCEPTED"
    assert body["idempotent_replay"] is False
    assert body["trace_id"]

    replay = upload(test_client, customer_id)
    assert replay.status_code == 202
    assert replay.json()["document_id"] == body["document_id"]
    assert replay.json()["idempotent_replay"] is True

    conflict = upload(test_client, customer_id, body=b"different")
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSE_MISMATCH"

    document = test_client.get(f"/v1/documents/{body['document_id']}", headers=AUTH)
    assert document.status_code == 200
    assert document.json()["status"] == "DECIDED"
    assert document.json()["extraction"] is not None
    shipment = test_client.get(f"/v1/shipments/{body['shipment_id']}", headers=AUTH)
    assert shipment.status_code == 200
    assert shipment.json()["document_ids"] == [body["document_id"]]


def test_rejects_unsupported_mime_and_hides_stack_traces(
    client: tuple[TestClient, UUID],
) -> None:
    test_client, customer_id = client
    response = upload(
        test_client,
        customer_id,
        content_type="image/gif",
        filename="x.gif",
        body=b"GIF89a",
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert "traceback" not in response.text.lower()
    assert "nova-test-token" not in response.text


def test_accepts_png_and_serves_content(client: tuple[TestClient, UUID]) -> None:
    # Minimal 1x1 PNG
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    test_client, customer_id = client
    response = upload(
        test_client,
        customer_id,
        key="png-upload-0001",
        content_type="image/png",
        filename="scan.png",
        body=png,
    )
    assert response.status_code == 202
    document_id = response.json()["document_id"]
    detail = test_client.get(f"/v1/documents/{document_id}", headers=AUTH)
    assert detail.status_code == 200
    assert detail.json()["content"]["download_url"] == f"/v1/documents/{document_id}/content"
    assert detail.json()["content"]["media_type"] == "image/png"
    content = test_client.get(f"/v1/documents/{document_id}/content", headers=AUTH)
    assert content.status_code == 200
    assert content.headers["content-type"].startswith("image/png")
    assert content.content.startswith(b"\x89PNG")


def test_ready_reports_database_down(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        database_url="postgresql+psycopg://invalid:invalid@127.0.0.1:1/nova",
        document_storage_path=str(tmp_path),
        database_connect_timeout_seconds=1,
    )
    with TestClient(create_app(settings)) as test_client:
        response = test_client.get("/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert "invalid" not in response.text


def test_ready_rejects_connected_database_without_schema(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'empty.db'}",
        document_storage_path=str(tmp_path / "documents"),
    )
    with TestClient(create_app(settings)) as test_client:
        response = test_client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "fail"
