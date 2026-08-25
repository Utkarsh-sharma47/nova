from __future__ import annotations

from fastapi.testclient import TestClient
from tests.query.conftest import AUTH, SeededWorld


def _query(client: TestClient, payload: dict[str, object]) -> object:
    return client.post("/v1/query", headers=AUTH, json=payload)


def test_get_shipment(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": f"What is the status of shipment {world.shipment_id}?",
            "customer_id": str(world.customer_id),
            "scope": {"shipment_id": str(world.shipment_id)},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RESULT"
    assert body["interpreted_intent"]["name"] == "get_shipment"
    record = body["result"]["records"][0]
    assert record["shipment_id"] == str(world.shipment_id)
    assert record["status"] == "decided"
    assert str(world.document_id) in record["document_ids"]


def test_get_document(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": f"Show document {world.document_id} status",
            "customer_id": str(world.customer_id),
            "scope": {"document_id": str(world.document_id)},
        },
    )
    body = response.json()
    assert body["status"] == "RESULT"
    assert body["interpreted_intent"]["name"] == "get_document"
    assert body["result"]["records"][0]["document_id"] == str(world.document_id)
    assert body["result"]["records"][0]["status"] == "EXTRACTED"


def test_validation_failure_query(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": "What is the validation status and failures?",
            "customer_id": str(world.customer_id),
            "scope": {"document_id": str(world.document_id)},
        },
    )
    body = response.json()
    assert body["status"] == "RESULT"
    assert body["interpreted_intent"]["name"] == "get_document_validation"
    record = body["result"]["records"][0]
    assert record["validation_id"] == str(world.validation_id)
    assert record["overall_result"] == "MISMATCH"
    assert record["failure_count"] == 1
    assert record["failures"][0]["reason_code"] == "CONSIGNEE_MISMATCH"
    assert record["failures"][0]["field"] == "consignee_name"


def test_decision_query(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": "What is the decision for this document?",
            "customer_id": str(world.customer_id),
            "scope": {"document_id": str(world.document_id)},
        },
    )
    body = response.json()
    assert body["status"] == "RESULT"
    assert body["interpreted_intent"]["name"] == "get_document_decision"
    record = body["result"]["records"][0]
    assert record["decision_id"] == str(world.decision_id)
    assert record["decision"] == "AMENDMENT_REQUEST"
    assert "VALIDATION_MISMATCH" in record["reason_codes"]


def test_list_shipments_by_decision(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": "Which shipments are waiting on human review?",
            "customer_id": str(world.customer_id),
        },
    )
    body = response.json()
    assert body["status"] == "RESULT"
    assert body["interpreted_intent"]["name"] == "list_shipments_by_decision"
    assert body["interpreted_intent"]["parameters"]["decision"] == "HUMAN_REVIEW"
    ids = {row["shipment_id"] for row in body["result"]["records"]}
    assert str(world.review_shipment_id) in ids
    assert str(world.shipment_id) not in ids


def test_list_documents_for_shipment(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": "List documents for this shipment",
            "customer_id": str(world.customer_id),
            "scope": {"shipment_id": str(world.shipment_id)},
        },
    )
    body = response.json()
    assert body["status"] == "RESULT"
    assert body["result"]["records"][0]["document_id"] == str(world.document_id)


def test_summarize_run(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": f"Summarize verification run {world.run_id}",
            "customer_id": str(world.customer_id),
            "scope": {"run_id": str(world.run_id)},
        },
    )
    body = response.json()
    assert body["status"] == "RESULT"
    record = body["result"]["records"][0]
    assert record["run_id"] == str(world.run_id)
    assert record["extracted_field_count"] == 1
    assert record["extracted_fields"][0]["field"] == "invoice_number"
    assert record["extracted_fields"][0]["value"] == "INV-100"
    assert record["validation"]["overall_result"] == "MISMATCH"
    assert record["decision"]["decision"] == "AMENDMENT_REQUEST"


def test_missing_shipment(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": f"Get shipment {world.missing_shipment_id}",
            "customer_id": str(world.customer_id),
            "scope": {"shipment_id": str(world.missing_shipment_id)},
        },
    )
    body = response.json()
    assert body["status"] == "EMPTY"
    assert body["result"]["records"] == []
    assert "No matching shipment" in body["result"]["answer_summary"]


def test_missing_document(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": f"Get document {world.missing_document_id}",
            "customer_id": str(world.customer_id),
            "scope": {"document_id": str(world.missing_document_id)},
        },
    )
    body = response.json()
    assert body["status"] == "EMPTY"
    assert "No matching document" in body["result"]["answer_summary"]


def test_no_results_for_decision_filter(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": "Which shipments are AUTO_APPROVE?",
            "customer_id": str(world.customer_id),
        },
    )
    body = response.json()
    assert body["status"] == "EMPTY"
    assert body["result"]["records"] == []
    assert "AUTO_APPROVE" in body["result"]["answer_summary"]


def test_unsupported_query(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": "Predict the vessel ETA for next month's Asia routes",
            "customer_id": str(world.customer_id),
        },
    )
    body = response.json()
    assert body["status"] == "UNSUPPORTED"
    assert body["unsupported"]["reason_code"] in {
        "INTENT_NOT_SUPPORTED",
        "OUT_OF_SCOPE",
    }
    assert body["result"] is None


def test_cross_customer_isolation(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": f"Get shipment {world.shipment_id}",
            "customer_id": str(world.other_customer_id),
            "scope": {"shipment_id": str(world.shipment_id)},
        },
    )
    body = response.json()
    assert body["status"] == "EMPTY"
    assert body["result"]["records"] == []


def test_factual_values_exist_in_database(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = _query(
        client,
        {
            "question": "What is the validation status and failures?",
            "customer_id": str(world.customer_id),
            "scope": {"document_id": str(world.document_id)},
        },
    )
    body = response.json()
    record = body["result"]["records"][0]
    assert record["validation_id"] == str(world.validation_id)
    assert record["document_id"] == str(world.document_id)
    assert record["shipment_id"] == str(world.shipment_id)
    assert record["overall_result"] == "MISMATCH"
