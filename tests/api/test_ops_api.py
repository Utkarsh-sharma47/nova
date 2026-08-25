"""API tests for Phase 9 ops summary and document list endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from nova.api.app import create_app
from nova.config import Settings
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import Base, Customer, Document, Shipment

AUTH = {"X-API-Key": "nova-test-token"}


@pytest.fixture
def client(tmp_path: Path) -> Iterator[tuple[TestClient, UUID]]:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'ops.db'}",
        document_storage_path=str(tmp_path / "documents"),
    )
    with TestClient(create_app(settings)) as test_client:
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        with session_scope() as session:
            session.add(Customer(customer_id=customer_id, name="Ops Customer", status="active"))
            shipment_id = uuid4()
            session.add(
                Shipment(
                    shipment_id=shipment_id,
                    customer_id=customer_id,
                    status="open",
                    customer_shipment_ref="OPS-1",
                )
            )
            session.flush()
            session.add(
                Document(
                    document_id=uuid4(),
                    shipment_id=shipment_id,
                    document_type="commercial_invoice",
                    status="in_pipeline",
                    display_name="pending.txt",
                )
            )
            session.add(
                Document(
                    document_id=uuid4(),
                    shipment_id=shipment_id,
                    document_type="bill_of_lading",
                    status="failed",
                    display_name="failed.txt",
                )
            )
        yield test_client, customer_id


def test_create_customer(client: tuple[TestClient, UUID]) -> None:
    test_client, _ = client
    response = test_client.post(
        "/v1/customers",
        headers=AUTH,
        json={"name": "Demo Customer"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Demo Customer"
    assert UUID(body["customer_id"])
    assert body["trace_id"]
    with session_scope() as session:
        customer = session.get(Customer, UUID(body["customer_id"]))
        assert customer is not None
        expected = customer.metadata_json.get("expected_fields")
        assert isinstance(expected, dict)
        assert expected["consignee_name"] == "Harbor Goods BV"
        assert expected["hs_code"] == "8471.30"


def test_ops_summary_and_list(client: tuple[TestClient, UUID]) -> None:
    test_client, customer_id = client
    summary = test_client.get(
        "/v1/ops/summary",
        headers=AUTH,
        params={"customer_id": str(customer_id)},
    )
    assert summary.status_code == 200
    body = summary.json()
    assert body["totals"]["documents"] == 2
    assert body["totals"]["processing"] == 1
    assert body["totals"]["failed"] == 1
    assert body["validation_outcomes"] == {"MATCH": 0, "MISMATCH": 0, "UNCERTAIN": 0}
    assert body["agreement_outcomes"] == {
        "STRONG_AGREEMENT": 0,
        "PARTIAL_AGREEMENT": 0,
        "WEAK_AGREEMENT": 2,
    }
    assert body["totals"]["weak_agreement"] == 2
    assert len(body["recent_documents"]) == 2
    assert {item["agreement"] for item in body["recent_documents"]} == {"WEAK_AGREEMENT"}

    listed = test_client.get(
        "/v1/documents",
        headers=AUTH,
        params={"customer_id": str(customer_id), "limit": 10},
    )
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 2
    assert {item["status"] for item in items} == {"PROCESSING", "FAILED"}
