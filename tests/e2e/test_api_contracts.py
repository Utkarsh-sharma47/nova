"""Phase 10 API contract smoke — documented endpoints respond with expected shapes."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from tests.e2e.conftest import AUTH, ingest, invoice_body


def test_documented_endpoints_contract_smoke(
    client: tuple[TestClient, UUID, Path],
) -> None:
    test_client, customer_id, _ = client

    assert test_client.get("/health").status_code == 200
    assert test_client.get("/ready").status_code == 200
    assert test_client.get("/metrics").status_code == 200

    created = test_client.post(
        "/v1/customers",
        headers=AUTH,
        json={"name": f"Contract Customer {uuid4()}"},
    )
    assert created.status_code == 201
    assert "customer_id" in created.json()

    body = ingest(test_client, customer_id, invoice_body(), key="api-contract-01")
    document_id = body["document_id"]
    shipment_id = body["shipment_id"]

    listed = test_client.get(
        "/v1/documents",
        headers=AUTH,
        params={"customer_id": str(customer_id)},
    )
    assert listed.status_code == 200

    detail = test_client.get(f"/v1/documents/{document_id}", headers=AUTH)
    assert detail.status_code == 200
    assert detail.json()["document_id"] == document_id

    validation = test_client.get(f"/v1/documents/{document_id}/validation", headers=AUTH)
    assert validation.status_code == 200
    assert "overall_result" in validation.json()

    decision = test_client.get(f"/v1/documents/{document_id}/decision", headers=AUTH)
    assert decision.status_code == 200
    assert "decision" in decision.json()

    shipment = test_client.get(f"/v1/shipments/{shipment_id}", headers=AUTH)
    assert shipment.status_code == 200

    assert (
        test_client.get(f"/v1/shipments/{shipment_id}/validation", headers=AUTH).status_code
        == 200
    )
    assert (
        test_client.get(f"/v1/shipments/{shipment_id}/decision", headers=AUTH).status_code
        == 200
    )

    summary = test_client.get(
        "/v1/ops/summary",
        headers=AUTH,
        params={"customer_id": str(customer_id)},
    )
    assert summary.status_code == 200

    query = test_client.post(
        "/v1/query",
        headers=AUTH,
        json={
            "question": f"What is the status of shipment {shipment_id}?",
            "customer_id": str(customer_id),
            "scope": {"shipment_id": shipment_id},
        },
    )
    assert query.status_code == 200
    assert "status" in query.json()

    missing = test_client.get(f"/v1/documents/{uuid4()}", headers=AUTH)
    assert missing.status_code == 404
