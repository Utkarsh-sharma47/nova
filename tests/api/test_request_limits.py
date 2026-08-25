"""Tests for early HTTP request body size rejection."""

from __future__ import annotations

from fastapi.testclient import TestClient

from nova.api.app import create_app
from nova.config import Settings


def test_oversized_content_length_is_rejected() -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        max_document_size_bytes=1024,
        max_request_body_bytes=2048,
        document_storage_path="./var/test-documents-limits",
    )
    client = TestClient(create_app(settings))
    response = client.post(
        "/v1/documents",
        headers={
            "Authorization": "Bearer nova-test-token",
            "Content-Length": "4096",
            "Content-Type": "multipart/form-data; boundary=x",
            "Idempotency-Key": "size-limit-test",
        },
        content=b"",
    )
    assert response.status_code == 413
    body = response.json()
    assert body["error"]["code"] == "PAYLOAD_TOO_LARGE"
