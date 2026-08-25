"""Grounded query tests for document agreement / confidence intents."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from nova.api.app import create_app
from nova.config import Settings
from nova.extraction.fields import required_fields_for
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import (
    Base,
    Customer,
    DecisionRecord,
    Document,
    DocumentVersion,
    ExtractedFieldRow,
    Shipment,
    ValidationRecordRow,
    VerificationRun,
)
from tests.query.conftest import AUTH

_REQUIRED = required_fields_for("commercial_invoice")


def _add_document(
    session: Session,
    *,
    customer_id: UUID,
    agreement_kind: str,
    updated_at: datetime | None = None,
) -> tuple[UUID, UUID]:
    """Seed one document shaped for STRONG / PARTIAL / WEAK agreement."""
    shipment_id = uuid4()
    document_id = uuid4()
    version_id = uuid4()
    run_id = uuid4()
    validation_id = uuid4()
    decision_id = uuid4()
    now = updated_at or datetime.now(UTC)
    trace_id = uuid4()

    session.add(
        Shipment(
            shipment_id=shipment_id,
            customer_id=customer_id,
            status="decided",
            customer_shipment_ref=f"SHIP-{agreement_kind}-{shipment_id.hex[:8]}",
        )
    )
    session.flush()
    session.add(
        Document(
            document_id=document_id,
            shipment_id=shipment_id,
            document_type="commercial_invoice",
            status="decided",
            display_name=f"{agreement_kind}.txt",
            created_at=now,
            updated_at=now,
        )
    )
    session.flush()
    session.add(
        DocumentVersion(
            document_version_id=version_id,
            document_id=document_id,
            shipment_id=shipment_id,
            document_type="commercial_invoice",
            version_number=1,
            storage_uri=f"file://{agreement_kind}.txt",
            content_sha256=uuid4().hex + "0" * 32,
            media_type="text/plain",
            byte_size=20,
            original_filename=f"{agreement_kind}.txt",
        )
    )
    session.add(
        VerificationRun(
            verification_run_id=run_id,
            shipment_id=shipment_id,
            status="succeeded",
            document_version_ids=[str(version_id)],
        )
    )
    session.flush()

    confidence = 0.96 if agreement_kind != "LOW" else 0.4
    invoice_number = f"INV-{agreement_kind}-1"
    for name in _REQUIRED:
        value = invoice_number if name == "invoice_number" else f"value-{name}"
        session.add(
            ExtractedFieldRow(
                verification_run_id=run_id,
                document_version_id=version_id,
                field_key=name,
                value_json=value,
                presence="KNOWN",
                confidence=confidence,
                is_missing=False,
            )
        )

    if agreement_kind == "STRONG":
        outcomes = {name: "MATCH" for name in _REQUIRED}
        aggregate = "MATCH"
        disposition = "AUTO_APPROVE"
        reason_codes = ["ALL_MATCH"]
    elif agreement_kind == "PARTIAL":
        outcomes = {name: "MATCH" for name in _REQUIRED}
        outcomes["consignee_name"] = "UNCERTAIN"
        aggregate = "UNCERTAIN"
        disposition = "HUMAN_REVIEW"
        reason_codes = ["VALIDATION_UNCERTAIN"]
    else:
        outcomes = {name: "MATCH" for name in _REQUIRED}
        outcomes["consignee_name"] = "MISMATCH"
        aggregate = "MISMATCH"
        disposition = "AMENDMENT_REQUEST"
        reason_codes = ["VALIDATION_MISMATCH"]

    session.add(
        ValidationRecordRow(
            validation_id=validation_id,
            verification_run_id=run_id,
            shipment_id=shipment_id,
            document_id=document_id,
            document_version_id=version_id,
            status="completed",
            aggregate_result=aggregate,
            engine_version="validator-engine-1",
            validator_version="validator-1",
            result_json={
                "status": "COMPLETED",
                "checks": [
                    {
                        "check_id": f"chk-{name}",
                        "rule_id": str(uuid4()),
                        "rule_code": f"equals.{name}",
                        "field_name": name,
                        "outcome": outcome,
                        "reason": outcome,
                        "blocking": True,
                    }
                    for name, outcome in outcomes.items()
                ],
            },
            summary_json={"match": 0, "mismatch": 0, "uncertain": 0},
            trace_id=trace_id,
            completed_at=now,
        )
    )
    session.add(
        DecisionRecord(
            decision_id=decision_id,
            verification_run_id=run_id,
            shipment_id=shipment_id,
            document_id=document_id,
            document_version_id=version_id,
            validation_result_id=validation_id,
            disposition=disposition,
            policy_version="routing-policy-1",
            reason_codes=reason_codes,
            reasons=reason_codes,
            actor_type="router",
            input_fingerprint=f"fp-{agreement_kind}",
            trace_id=trace_id,
            decided_at=now,
        )
    )
    return document_id, shipment_id


@pytest.fixture
def agreement_world(tmp_path: Path) -> Iterator[tuple[TestClient, UUID, dict[str, UUID]]]:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'agreement-query.db'}",
        document_storage_path=str(tmp_path / "documents"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)) as client:
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        ids: dict[str, UUID] = {}
        with session_scope() as session:
            session.add(
                Customer(customer_id=customer_id, name="Agreement Customer", status="active")
            )
            session.flush()
            now = datetime.now(UTC)
            strong_id, _ = _add_document(
                session, customer_id=customer_id, agreement_kind="STRONG", updated_at=now
            )
            partial_id, _ = _add_document(
                session, customer_id=customer_id, agreement_kind="PARTIAL", updated_at=now
            )
            weak_id, _ = _add_document(
                session, customer_id=customer_id, agreement_kind="WEAK", updated_at=now
            )
            old_strong_id, _ = _add_document(
                session,
                customer_id=customer_id,
                agreement_kind="STRONG",
                updated_at=now - timedelta(days=14),
            )
            ids = {
                "strong": strong_id,
                "partial": partial_id,
                "weak": weak_id,
                "old_strong": old_strong_id,
            }
        yield client, customer_id, ids


def _query(client: TestClient, customer_id: UUID, question: str) -> dict[str, object]:
    response = client.post(
        "/v1/query",
        headers=AUTH,
        json={"question": question, "customer_id": str(customer_id)},
    )
    assert response.status_code == 200
    return response.json()


def test_count_strong_agreement(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, _ = agreement_world
    body = _query(client, customer_id, "How many strong agreement documents are there?")
    assert body["status"] == "RESULT"
    assert body["interpreted_intent"]["name"] == "count_documents_by_agreement"
    assert body["interpreted_intent"]["parameters"]["agreement"] == "STRONG_AGREEMENT"
    assert body["result"]["records"][0]["count"] == 2
    assert "STRONG_AGREEMENT" in body["result"]["answer_summary"]


def test_count_weak_agreement(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, _ = agreement_world
    body = _query(client, customer_id, "How many weak agreement documents are there?")
    assert body["status"] == "RESULT"
    assert body["result"]["records"][0]["count"] == 1


def test_count_partial_variations(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, _ = agreement_world
    for question in (
        "How many partial agreement documents are there?",
        "Count partial agreement docs.",
        "How many documents partially agree?",
    ):
        body = _query(client, customer_id, question)
        assert body["interpreted_intent"]["name"] == "count_documents_by_agreement"
        assert body["interpreted_intent"]["parameters"]["agreement"] == "PARTIAL_AGREEMENT"
        assert body["result"]["records"][0]["count"] == 1


def test_list_strong_agreement(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, ids = agreement_world
    body = _query(client, customer_id, "Show strong agreement documents.")
    assert body["status"] == "RESULT"
    assert body["interpreted_intent"]["name"] == "list_documents_by_agreement"
    listed = {row["document_id"] for row in body["result"]["records"]}
    assert str(ids["strong"]) in listed
    assert str(ids["old_strong"]) in listed
    assert str(ids["weak"]) not in listed
    assert "AUTO_APPROVE" in body["result"]["answer_summary"]
    assert "Confidence:" in body["result"]["answer_summary"]
    assert "Agreement: STRONG_AGREEMENT" in body["result"]["answer_summary"]


def test_list_weak_variations(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, ids = agreement_world
    for question in (
        "Show weak agreement documents.",
        "Show me documents with weak agreement.",
        "List weak agreement docs.",
    ):
        body = _query(client, customer_id, question)
        assert body["interpreted_intent"]["name"] == "list_documents_by_agreement"
        assert body["interpreted_intent"]["parameters"]["agreement"] == "WEAK_AGREEMENT"
        listed = {row["document_id"] for row in body["result"]["records"]}
        assert str(ids["weak"]) in listed


def test_count_strong_variations(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, _ = agreement_world
    for question in (
        "How many strong agreement docs?",
        "Count strong agreement documents.",
        "How many documents strongly agree?",
    ):
        body = _query(client, customer_id, question)
        assert body["interpreted_intent"]["name"] == "count_documents_by_agreement"
        assert body["result"]["records"][0]["count"] == 2


def test_require_attention_count(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, _ = agreement_world
    body = _query(client, customer_id, "How many documents require attention?")
    assert body["status"] == "RESULT"
    assert body["interpreted_intent"]["name"] == "count_documents_requiring_attention"
    # PARTIAL + WEAK (old/new strong excluded)
    assert body["result"]["records"][0]["count"] == 2


def test_count_auto_approved_and_human_review(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, _ = agreement_world
    auto = _query(client, customer_id, "How many documents were auto approved?")
    assert auto["interpreted_intent"]["name"] == "count_documents_by_decision"
    assert auto["result"]["records"][0]["count"] == 2

    review = _query(client, customer_id, "How many documents went to human review?")
    assert review["interpreted_intent"]["name"] == "count_documents_by_decision"
    assert review["result"]["records"][0]["count"] == 1


def test_count_mismatches(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, _ = agreement_world
    body = _query(client, customer_id, "How many documents have mismatches?")
    assert body["interpreted_intent"]["name"] == "count_documents_with_mismatches"
    assert body["result"]["records"][0]["count"] == 1


def test_strong_agreement_this_week_applies_time_filter(
    agreement_world: tuple[TestClient, UUID, dict[str, UUID]],
) -> None:
    client, customer_id, ids = agreement_world
    body = _query(
        client,
        customer_id,
        "How many documents are strong agreement this week?",
    )
    assert body["interpreted_intent"]["name"] == "count_documents_by_agreement"
    assert body["interpreted_intent"]["parameters"]["time_range"]["preset"] == "this_week"
    assert body["result"]["records"][0]["count"] == 1
    # Sanity: older strong exists but is excluded by the window.
    assert ids["old_strong"]
