"""Decision table failsafe constraint tests (SQLite)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from nova.contracts.routing import DecisionActorType, DecisionKind
from nova.persistence.models import (
    Base,
    Customer,
    DecisionRecord,
    Document,
    DocumentVersion,
    Shipment,
    VerificationRun,
)
from nova.router.persistence import FailsafeAutoApproveError, assert_failsafe_cannot_auto_approve
from nova.router.service import RouterService

_FIXTURES = Path(__file__).resolve().parents[1] / "agents" / "router" / "fixtures.py"
_spec = importlib.util.spec_from_file_location("router_fixtures", _FIXTURES)
assert _spec and _spec.loader
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
make_request = _fixtures.make_request


def _seed(session: Session) -> dict[str, object]:
    customer_id = uuid4()
    shipment_id = uuid4()
    document_id = uuid4()
    version_id = uuid4()
    run_id = uuid4()
    session.add(
        Customer(customer_id=customer_id, name="Acme", status="active", metadata_json={})
    )
    session.add(
        Shipment(
            shipment_id=shipment_id,
            customer_id=customer_id,
            status="routing",
            metadata_json={},
        )
    )
    session.add(
        Document(
            document_id=document_id,
            shipment_id=shipment_id,
            document_type="bill_of_lading",
            status="extracted",
            ingestion_channel="upload",
        )
    )
    session.flush()
    session.add(
        DocumentVersion(
            document_version_id=version_id,
            document_id=document_id,
            shipment_id=shipment_id,
            document_type="bill_of_lading",
            version_number=1,
            storage_uri="file:///tmp/x",
            content_sha256="a" * 64,
            media_type="application/pdf",
            byte_size=1,
        )
    )
    session.add(
        VerificationRun(
            verification_run_id=run_id,
            shipment_id=shipment_id,
            status="running",
            trigger="test",
            document_version_ids=[str(version_id)],
        )
    )
    session.flush()
    return {
        "shipment_id": shipment_id,
        "document_id": document_id,
        "version_id": version_id,
        "run_id": run_id,
    }


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _fk(dbapi_conn, _connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    # Enforce CHECK constraints on SQLite (off by default for legacy reasons).
    with engine.begin() as conn:
        conn.execute(text("PRAGMA ignore_check_constraints=OFF"))
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_failsafe_cannot_insert_auto_approve(db_session: Session) -> None:
    ids = _seed(db_session)
    row = DecisionRecord(
        decision_id=uuid4(),
        verification_run_id=ids["run_id"],  # type: ignore[arg-type]
        shipment_id=ids["shipment_id"],  # type: ignore[arg-type]
        document_id=ids["document_id"],  # type: ignore[arg-type]
        document_version_id=ids["version_id"],  # type: ignore[arg-type]
        validation_result_id=uuid4(),
        disposition="AUTO_APPROVE",
        policy_version="1.0.0",
        actor_type="system_failsafe",
        trace_id=uuid4(),
        reason_codes=[],
        reasons=[],
        triggering_check_ids=[],
        safety_constraints_applied=["SC_AGENT_FAILURE"],
        reasoning_json={},
        input_fingerprint="x" * 64,
        evidence_refs=[],
    )
    db_session.add(row)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_router_can_insert_auto_approve(db_session: Session) -> None:
    ids = _seed(db_session)
    row = DecisionRecord(
        decision_id=uuid4(),
        verification_run_id=ids["run_id"],  # type: ignore[arg-type]
        shipment_id=ids["shipment_id"],  # type: ignore[arg-type]
        document_id=ids["document_id"],  # type: ignore[arg-type]
        document_version_id=ids["version_id"],  # type: ignore[arg-type]
        validation_result_id=uuid4(),
        disposition="AUTO_APPROVE",
        policy_version="1.0.0",
        actor_type="router",
        trace_id=uuid4(),
        reason_codes=["RC_ALL_BLOCKING_MATCH"],
        reasons=["ok"],
        triggering_check_ids=[str(uuid4())],
        safety_constraints_applied=[],
        reasoning_json={},
        input_fingerprint="y" * 64,
        evidence_refs=["ev-1"],
    )
    db_session.add(row)
    db_session.flush()
    assert row.disposition == "AUTO_APPROVE"


def test_assert_failsafe_helper() -> None:
    decision = RouterService().decide(make_request(), force_failsafe=True)
    assert decision.actor_type is DecisionActorType.SYSTEM_FAILSAFE
    with pytest.raises(FailsafeAutoApproveError):
        illegal = decision.model_copy(
            update={
                "decision": DecisionKind.AUTO_APPROVE,
                "requires_human_attention": False,
                "safety_constraints_applied": [],
            }
        )
        assert_failsafe_cannot_auto_approve(illegal)
