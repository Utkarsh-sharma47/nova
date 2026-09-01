"""Shared fixtures for Phase 10 E2E matrix tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from nova.api.app import create_app
from nova.application.rules import customer_metadata_with_expected_fields
from nova.config import Settings
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import Base, Customer
from tests.query.conftest import SeededWorld, _seed

AUTH = {"X-API-Key": "nova-test-token"}

PHASE10_INVOICE_EXPECTED: dict[str, str] = {
    "invoice_number": "INV-42",
    "invoice_date": "2026-02-01",
    "seller_name": "Acme Trading",
    "buyer_name": "Globex Corp",
    "consignee_name": "Globex Corp",
    "hs_code": "8471.30",
    "port_of_loading": "Shanghai",
    "port_of_discharge": "Los Angeles",
    "incoterms": "FOB",
    "description_of_goods": "Electronic components for Phase 10 E2E.",
    "gross_weight": "1250 KG",
    "currency": "USD",
    "total_amount": "1250.00",
}

PHASE10_BOL_EXPECTED: dict[str, str] = {
    "bl_number": "BL-9001",
    "vessel_name": "Pacific Star",
    "shipper_name": "Acme Trading",
    "consignee_name": "Globex Corp",
    "port_of_loading": "Shanghai",
    "port_of_discharge": "Los Angeles",
    "container_number": "MSKU1234567",
    "hs_code": "8471.30",
    "incoterms": "FOB",
    "description_of_goods": "Containerized electronics.",
    "gross_weight": "22000 KG",
    "invoice_number": "INV-BOL-1",
}


@pytest.fixture
def client(tmp_path: Path) -> Iterator[tuple[TestClient, UUID, Path]]:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'nova.db'}",
        document_storage_path=str(tmp_path / "documents"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)) as test_client:
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        with session_scope() as session:
            session.add(
                Customer(
                    customer_id=customer_id,
                    name="Phase10 Customer",
                    status="active",
                    metadata_json=customer_metadata_with_expected_fields(PHASE10_INVOICE_EXPECTED),
                )
            )
        yield test_client, customer_id, tmp_path


@pytest.fixture
def query_world(tmp_path: Path) -> Iterator[tuple[TestClient, SeededWorld]]:
    """Local re-export of the Phase 8 seeded query world for matrix cases 29–33."""
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'query.db'}",
        document_storage_path=str(tmp_path / "documents"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)) as test_client:
        Base.metadata.create_all(get_engine())
        with session_scope() as session:
            world = _seed(session)
        yield test_client, world


def invoice_body() -> bytes:
    """Synthetic invoice covering GoComet assignment fields + invoice extras."""
    return (
        b"COMMERCIAL INVOICE\n"
        b"Invoice Number: INV-42\n"
        b"Invoice Date: 2026-02-01\n"
        b"Seller: Acme Trading\n"
        b"Buyer: Globex Corp\n"
        b"Consignee: Globex Corp\n"
        b"Port of Loading: Shanghai\n"
        b"Port of Discharge: Los Angeles\n"
        b"HS Code: 8471.30\n"
        b"Incoterms: FOB\n"
        b"Gross Weight: 1250 KG\n"
        b"Currency: USD\n"
        b"Total Amount: 1250.00\n"
        b"Description of Goods: Electronic components for Phase 10 E2E.\n"
    )


def bol_body() -> bytes:
    """Synthetic bill of lading covering assignment + BoL fields."""
    return (
        b"BILL OF LADING\n"
        b"BL Number: BL-9001\n"
        b"Vessel Name: Pacific Star\n"
        b"Shipper Name: Acme Trading\n"
        b"Consignee Name: Globex Corp\n"
        b"Port of Loading: Shanghai\n"
        b"Port of Discharge: Los Angeles\n"
        b"Container Number: MSKU1234567\n"
        b"HS Code: 8471.30\n"
        b"Incoterms: FOB\n"
        b"Gross Weight: 22000 KG\n"
        b"Invoice Number: INV-BOL-1\n"
        b"Description of Goods: Containerized electronics.\n"
    )


def missing_invoice() -> bytes:
    return b"Invoice Number: INV-99\nSeller: Acme\n"


def ingest(
    test_client: TestClient,
    customer_id: UUID,
    body: bytes,
    *,
    document_type: str = "INVOICE",
    key: str = "p10-key-0001",
    filename: str = "doc.txt",
    content_type: str = "text/plain",
) -> dict[str, Any]:
    response = test_client.post(
        "/v1/documents",
        headers={**AUTH, "Idempotency-Key": key},
        data={"customer_id": str(customer_id), "document_type": document_type},
        files={"file": (filename, body, content_type)},
    )
    assert response.status_code == 202, response.text
    return response.json()


def upload_expect_error(
    test_client: TestClient,
    customer_id: UUID,
    body: bytes,
    *,
    key: str,
    filename: str,
    content_type: str,
    expected_status: int,
    expected_code: str,
) -> dict[str, Any]:
    response = test_client.post(
        "/v1/documents",
        headers={**AUTH, "Idempotency-Key": key},
        data={"customer_id": str(customer_id), "document_type": "INVOICE"},
        files={"file": (filename, body, content_type)},
    )
    assert response.status_code == expected_status, response.text
    payload = response.json()
    assert payload["error"]["code"] == expected_code
    assert "traceback" not in response.text.lower()
    assert "nova-test-token" not in response.text
    return payload
