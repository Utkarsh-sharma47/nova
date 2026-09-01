"""Deterministic query dataset covering every agreement / validation / decision state.

Seeded directly into the system of record so query tests exercise the real
repository reads rather than stubbed answers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from nova.extraction.fields import required_fields_for
from nova.persistence.models import (
    DecisionRecord,
    Document,
    DocumentVersion,
    ExtractedFieldRow,
    Shipment,
    ValidationRecordRow,
    VerificationRun,
)

REQUIRED_FIELDS = required_fields_for("commercial_invoice")


@dataclass(frozen=True)
class SeedDocument:
    """One document's persisted evidence shape."""

    invoice_number: str
    extraction_confidence: float
    aggregate_result: str
    disposition: str
    reason_codes: tuple[str, ...]
    mismatch_fields: tuple[str, ...] = ()
    uncertain_fields: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()
    age_days: int = 0
    rationale: str = ""
    safety_constraints: tuple[str, ...] = field(default=())


# Expected derived state is documented per row so tests assert against intent,
# not against whatever the code happens to produce.
SEED_DOCUMENTS: tuple[SeedDocument, ...] = (
    SeedDocument(
        invoice_number="INV-CLEAN-1001",
        extraction_confidence=0.96,
        aggregate_result="MATCH",
        disposition="AUTO_APPROVE",
        reason_codes=("ALL_CHECKS_MATCH",),
        rationale="All required fields matched customer expectations.",
    ),
    SeedDocument(
        invoice_number="INV-CLEAN-1002",
        extraction_confidence=0.94,
        aggregate_result="MATCH",
        disposition="AUTO_APPROVE",
        reason_codes=("ALL_CHECKS_MATCH",),
        rationale="All required fields matched customer expectations.",
    ),
    SeedDocument(
        invoice_number="INV-MESSY-2001",
        extraction_confidence=0.95,
        aggregate_result="MISMATCH",
        disposition="AMENDMENT_REQUEST",
        reason_codes=("VALIDATION_MISMATCH",),
        mismatch_fields=("incoterms", "hs_code", "gross_weight", "total_amount"),
        rationale="Four required fields disagree with the customer profile.",
        safety_constraints=("NO_AUTO_APPROVE_ON_MISMATCH",),
    ),
    SeedDocument(
        invoice_number="INV-UNSURE-3001",
        extraction_confidence=0.93,
        aggregate_result="UNCERTAIN",
        disposition="HUMAN_REVIEW",
        reason_codes=("VALIDATION_UNCERTAIN",),
        uncertain_fields=("consignee_name", "port_of_discharge"),
        rationale="Two required checks could not be resolved.",
        safety_constraints=("NO_AUTO_APPROVE_ON_UNCERTAIN",),
    ),
    SeedDocument(
        invoice_number="INV-LOWCONF-4001",
        extraction_confidence=0.42,
        aggregate_result="MATCH",
        disposition="HUMAN_REVIEW",
        reason_codes=("LOW_EXTRACTION_CONFIDENCE",),
        rationale="Extraction confidence is below the routing threshold.",
        safety_constraints=("NO_AUTO_APPROVE_ON_LOW_CONFIDENCE",),
    ),
    SeedDocument(
        invoice_number="INV-GAPS-5001",
        extraction_confidence=0.90,
        aggregate_result="MATCH",
        disposition="HUMAN_REVIEW",
        reason_codes=("MISSING_REQUIRED_EVIDENCE",),
        missing_fields=("hs_code",),
        rationale="A required field has no evidence in the document.",
        safety_constraints=("NO_AUTO_APPROVE_ON_MISSING_EVIDENCE",),
    ),
    SeedDocument(
        invoice_number="INV-OLD-6001",
        extraction_confidence=0.95,
        aggregate_result="MATCH",
        disposition="AUTO_APPROVE",
        reason_codes=("ALL_CHECKS_MATCH",),
        age_days=20,
        rationale="All required fields matched customer expectations.",
    ),
)


def seed_document(session: Session, *, customer_id: UUID, spec: SeedDocument) -> UUID:
    """Insert one document with extraction, validation, and decision evidence."""
    shipment_id = uuid4()
    document_id = uuid4()
    version_id = uuid4()
    run_id = uuid4()
    validation_id = uuid4()
    trace_id = uuid4()
    when = datetime.now(UTC) - timedelta(days=spec.age_days)

    session.add(
        Shipment(
            shipment_id=shipment_id,
            customer_id=customer_id,
            status="decided",
            customer_shipment_ref=f"SHIP-{spec.invoice_number}",
            created_at=when,
            updated_at=when,
        )
    )
    session.flush()
    session.add(
        Document(
            document_id=document_id,
            shipment_id=shipment_id,
            document_type="commercial_invoice",
            status="decided",
            display_name=f"{spec.invoice_number}.txt",
            created_at=when,
            updated_at=when,
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
            storage_uri=f"file://{spec.invoice_number}.txt",
            content_sha256=uuid4().hex + "0" * 32,
            media_type="text/plain",
            byte_size=64,
            original_filename=f"{spec.invoice_number}.txt",
        )
    )
    session.add(
        VerificationRun(
            verification_run_id=run_id,
            shipment_id=shipment_id,
            status="succeeded",
            document_version_ids=[str(version_id)],
            created_at=when,
        )
    )
    session.flush()

    for name in REQUIRED_FIELDS:
        missing = name in spec.missing_fields
        value = spec.invoice_number if name == "invoice_number" else f"value-{name}"
        session.add(
            ExtractedFieldRow(
                verification_run_id=run_id,
                document_version_id=version_id,
                field_key=name,
                value_json=None if missing else value,
                presence="MISSING" if missing else "KNOWN",
                confidence=None if missing else spec.extraction_confidence,
                is_missing=missing,
            )
        )

    checks = []
    for name in REQUIRED_FIELDS:
        if name in spec.missing_fields:
            # No evidence means no check ran; it must not read as a pass.
            continue
        if name in spec.mismatch_fields:
            outcome = "MISMATCH"
        elif name in spec.uncertain_fields:
            outcome = "UNCERTAIN"
        else:
            outcome = "MATCH"
        checks.append(
            {
                "check_id": f"chk-{spec.invoice_number}-{name}",
                "rule_id": str(uuid4()),
                "rule_code": f"equals.{name}",
                "field_name": name,
                "outcome": outcome,
                "reason": f"{name} {outcome.lower()}",
                "error_code": None if outcome == "MATCH" else f"{outcome}_{name.upper()}",
                "blocking": True,
            }
        )

    session.add(
        ValidationRecordRow(
            validation_id=validation_id,
            verification_run_id=run_id,
            shipment_id=shipment_id,
            document_id=document_id,
            document_version_id=version_id,
            status="completed",
            aggregate_result=spec.aggregate_result,
            engine_version="validator-engine-1",
            validator_version="validator-1",
            result_json={"status": "COMPLETED", "checks": checks},
            summary_json={
                "match": sum(1 for c in checks if c["outcome"] == "MATCH"),
                "mismatch": len(spec.mismatch_fields),
                "uncertain": len(spec.uncertain_fields),
            },
            trace_id=trace_id,
            completed_at=when,
            created_at=when,
        )
    )
    session.add(
        DecisionRecord(
            decision_id=uuid4(),
            verification_run_id=run_id,
            shipment_id=shipment_id,
            document_id=document_id,
            document_version_id=version_id,
            validation_result_id=validation_id,
            disposition=spec.disposition,
            policy_version="routing-policy-1",
            reason_codes=list(spec.reason_codes),
            reasons=list(spec.reason_codes),
            llm_rationale=spec.rationale,
            safety_constraints_applied=list(spec.safety_constraints),
            actor_type="router",
            input_fingerprint=f"fp-{spec.invoice_number}",
            trace_id=trace_id,
            decided_at=when,
        )
    )
    return document_id


def seed_query_dataset(session: Session, customer_id: UUID) -> dict[str, UUID]:
    """Seed the full dataset; returns invoice number -> document id."""
    return {
        spec.invoice_number: seed_document(session, customer_id=customer_id, spec=spec)
        for spec in SEED_DOCUMENTS
    }
