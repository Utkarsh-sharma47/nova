"""Deterministic fixtures for Phase 8 query tests."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from nova.api.app import create_app
from nova.config import Settings
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import (
    Base,
    Customer,
    DecisionRecord,
    Document,
    DocumentVersion,
    ExtractedFieldRow,
    Shipment,
    ValidationCheckRow,
    ValidationRow,
    VerificationRun,
)

AUTH = {"X-API-Key": "nova-test-token"}


@dataclass
class SeededWorld:
    customer_id: UUID
    other_customer_id: UUID
    shipment_id: UUID
    missing_shipment_id: UUID
    document_id: UUID
    missing_document_id: UUID
    run_id: UUID
    validation_id: UUID
    decision_id: UUID
    review_shipment_id: UUID
    review_document_id: UUID
    review_decision_id: UUID


def _seed(session: Session) -> SeededWorld:
    customer_id = uuid4()
    other_customer_id = uuid4()
    shipment_id = uuid4()
    document_id = uuid4()
    version_id = uuid4()
    run_id = uuid4()
    validation_id = uuid4()
    decision_id = uuid4()
    review_shipment_id = uuid4()
    review_document_id = uuid4()
    review_version_id = uuid4()
    review_run_id = uuid4()
    review_decision_id = uuid4()
    now = datetime.now(UTC)

    session.add_all(
        [
            Customer(customer_id=customer_id, name="Query Customer", status="active"),
            Customer(customer_id=other_customer_id, name="Other Customer", status="active"),
            Shipment(
                shipment_id=shipment_id,
                customer_id=customer_id,
                status="decided",
                customer_shipment_ref="SHIP-1",
            ),
            Shipment(
                shipment_id=review_shipment_id,
                customer_id=customer_id,
                status="decided",
                customer_shipment_ref="SHIP-REVIEW",
            ),
        ]
    )
    session.flush()
    session.add_all(
        [
            Document(
                document_id=document_id,
                shipment_id=shipment_id,
                document_type="commercial_invoice",
                status="extracted",
                display_name="invoice.txt",
            ),
            Document(
                document_id=review_document_id,
                shipment_id=review_shipment_id,
                document_type="bill_of_lading",
                status="extracted",
                display_name="bol.txt",
            ),
        ]
    )
    session.flush()
    session.add_all(
        [
            DocumentVersion(
                document_version_id=version_id,
                document_id=document_id,
                shipment_id=shipment_id,
                document_type="commercial_invoice",
                version_number=1,
                storage_uri="file://invoice.txt",
                content_sha256="a" * 64,
                media_type="text/plain",
                byte_size=12,
                original_filename="invoice.txt",
            ),
            DocumentVersion(
                document_version_id=review_version_id,
                document_id=review_document_id,
                shipment_id=review_shipment_id,
                document_type="bill_of_lading",
                version_number=1,
                storage_uri="file://bol.txt",
                content_sha256="b" * 64,
                media_type="text/plain",
                byte_size=10,
                original_filename="bol.txt",
            ),
            VerificationRun(
                verification_run_id=run_id,
                shipment_id=shipment_id,
                status="succeeded",
                document_version_ids=[str(version_id)],
            ),
            VerificationRun(
                verification_run_id=review_run_id,
                shipment_id=review_shipment_id,
                status="succeeded",
                document_version_ids=[str(review_version_id)],
            ),
        ]
    )
    session.flush()
    session.add(
        ExtractedFieldRow(
            verification_run_id=run_id,
            document_version_id=version_id,
            field_key="invoice_number",
            value_json="INV-100",
            presence="PRESENT",
            confidence=0.95,
            is_missing=False,
        )
    )
    session.add(
        ValidationRow(
            validation_id=validation_id,
            verification_run_id=run_id,
            shipment_id=shipment_id,
            document_id=document_id,
            status="completed",
            aggregate_result="MISMATCH",
            document_version_ids=[str(version_id)],
            completed_at=now,
        )
    )
    session.flush()
    session.add(
        ValidationCheckRow(
            validation_id=validation_id,
            rule_key="rule_consignee_match",
            check_sequence=1,
            result="MISMATCH",
            field_key="consignee_name",
            reason_code="CONSIGNEE_MISMATCH",
            reason_detail="Extracted consignee does not match allow-list.",
            evaluator="deterministic",
        )
    )
    session.add_all(
        [
            DecisionRecord(
                decision_id=decision_id,
                verification_run_id=run_id,
                shipment_id=shipment_id,
                document_id=document_id,
                document_version_id=version_id,
                validation_id=validation_id,
                disposition="AMENDMENT_REQUEST",
                policy_version="routing-policy-1",
                reason_codes=["VALIDATION_MISMATCH"],
                reasons=["Validation MISMATCH on consignee_name"],
                actor_type="router",
                input_fingerprint="fp-1",
                decided_at=now,
            ),
            DecisionRecord(
                decision_id=review_decision_id,
                verification_run_id=review_run_id,
                shipment_id=review_shipment_id,
                document_id=review_document_id,
                document_version_id=review_version_id,
                disposition="HUMAN_REVIEW",
                policy_version="routing-policy-1",
                reason_codes=["LOW_CONFIDENCE"],
                reasons=["Confidence below policy threshold"],
                actor_type="router",
                input_fingerprint="fp-2",
                decided_at=now,
            ),
        ]
    )
    return SeededWorld(
        customer_id=customer_id,
        other_customer_id=other_customer_id,
        shipment_id=shipment_id,
        missing_shipment_id=uuid4(),
        document_id=document_id,
        missing_document_id=uuid4(),
        run_id=run_id,
        validation_id=validation_id,
        decision_id=decision_id,
        review_shipment_id=review_shipment_id,
        review_document_id=review_document_id,
        review_decision_id=review_decision_id,
    )


@pytest.fixture
def query_world(tmp_path: Path) -> Iterator[tuple[TestClient, SeededWorld]]:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'query.db'}",
        document_storage_path=str(tmp_path / "documents"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)) as client:
        Base.metadata.create_all(get_engine())
        with session_scope() as session:
            world = _seed(session)
        yield client, world
