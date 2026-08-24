from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nova.application.ingestion import IngestCommand, IngestionService
from nova.infrastructure.storage import LocalFilesystemStorage
from nova.persistence.models import Base, Customer


def _service(tmp_path: Path) -> tuple[Session, IngestionService, IngestCommand]:
    engine = create_engine(f"sqlite:///{tmp_path / 'nova.db'}")
    Base.metadata.create_all(engine)
    session = Session(engine)
    customer_id = uuid4()
    session.add(Customer(customer_id=customer_id, name="Test", status="active"))
    session.commit()
    service = IngestionService(
        session,
        LocalFilesystemStorage(tmp_path / "documents"),
        max_document_size_bytes=1024,
        allowed_mime_types=("text/plain",),
    )
    command = IngestCommand(
        blob=b"invoice",
        filename="invoice.txt",
        media_type="text/plain",
        customer_id=customer_id,
        shipment_id=None,
        document_type="INVOICE",
        external_ref=None,
        idempotency_key="failure-test-0001",
        principal="principal",
        trace_id=str(uuid4()),
    )
    return session, service, command


def test_database_failure_removes_stored_blob(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session, service, command = _service(tmp_path)

    def fail_commit() -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="database unavailable"):
        service.ingest(command)

    assert not list((tmp_path / "documents").rglob("*.*"))
    session.close()


def test_unique_violation_rereads_concurrent_winner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session, service, command = _service(tmp_path)
    response = {
        "document_id": str(uuid4()),
        "shipment_id": str(uuid4()),
        "run_id": str(uuid4()),
        "status": "ACCEPTED",
        "idempotent_replay": False,
        "trace_id": "winner-trace",
    }
    calls = 0

    def idempotency(_principal_hash: str, _key: str) -> object | None:
        nonlocal calls
        calls += 1
        if calls == 1:
            return None
        return SimpleNamespace(
            request_fingerprint=service._fingerprint(  # noqa: SLF001
                command,
                hashlib.sha256(command.blob).hexdigest(),
            ),
            response_json=response,
        )

    def conflict() -> None:
        raise IntegrityError("INSERT", {}, RuntimeError("unique violation"))

    monkeypatch.setattr(service.repository, "idempotency", idempotency)
    monkeypatch.setattr(session, "commit", conflict)
    replay = service.ingest(command)

    assert replay["document_id"] == response["document_id"]
    assert replay["idempotent_replay"] is True
    assert replay["trace_id"] == command.trace_id
    assert not list((tmp_path / "documents").rglob("*.*"))
    session.close()
