"""Integration tests: extraction persistence + document lifecycle + duplicate runs."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from nova.api.app import create_app
from nova.application.extraction import ExtractionApplicationService, build_default_llm
from nova.config import Settings
from nova.contracts.extraction import ExtractionStatus
from nova.extraction.service import ExtractorService
from nova.infrastructure.storage import LocalFilesystemStorage
from nova.llm.mock import MockLLM
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import (
    AgentExecution,
    Base,
    Customer,
    ExtractedFieldRow,
    ModelCallMetadata,
)

AUTH = {"X-API-Key": "nova-test-token"}


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
            session.add(Customer(customer_id=customer_id, name="Test Customer", status="active"))
        yield test_client, customer_id, tmp_path


def _invoice_body() -> bytes:
    return (
        b"Invoice Number: INV-42\n"
        b"Invoice Date: 2026-02-01\n"
        b"Seller: Acme Trading\n"
        b"Buyer: Globex Corp\n"
        b"Currency: USD\n"
        b"Total Amount: 1250.00\n"
    )


def test_ingest_runs_extraction_and_persists(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, customer_id, _ = client
    response = test_client.post(
        "/v1/documents",
        headers={**AUTH, "Idempotency-Key": "extract-key-0001"},
        data={"customer_id": str(customer_id), "document_type": "INVOICE"},
        files={"file": ("invoice.txt", _invoice_body(), "text/plain")},
    )
    assert response.status_code == 202
    body = response.json()
    document_id = body["document_id"]
    run_id = body["run_id"]

    detail = test_client.get(f"/v1/documents/{document_id}", headers=AUTH)
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["status"] == "EXTRACTED"
    assert payload["extraction"] is not None
    assert payload["extraction"]["status"] in {"SUCCEEDED", "PARTIAL"}
    assert payload["extraction"]["prompt_version"] == "extractor.v1"

    with session_scope() as session:
        fields = session.scalars(
            select(ExtractedFieldRow).where(ExtractedFieldRow.verification_run_id == UUID(run_id))
        ).all()
        assert len(fields) >= 1
        executions = session.scalars(
            select(AgentExecution).where(AgentExecution.verification_run_id == UUID(run_id))
        ).all()
        assert len(executions) == 1
        assert executions[0].prompt_version == "extractor.v1"
        calls = session.scalars(
            select(ModelCallMetadata).where(ModelCallMetadata.verification_run_id == UUID(run_id))
        ).all()
        assert len(calls) == 1


def test_duplicate_extraction_is_idempotent(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, customer_id, tmp_path = client
    response = test_client.post(
        "/v1/documents",
        headers={**AUTH, "Idempotency-Key": "extract-key-0002"},
        data={"customer_id": str(customer_id), "document_type": "INVOICE"},
        files={"file": ("invoice.txt", _invoice_body(), "text/plain")},
    )
    body = response.json()
    document_id = UUID(body["document_id"])
    run_id = UUID(body["run_id"])
    trace_id = UUID(body["trace_id"]) if _is_uuid(body["trace_id"]) else uuid4()

    with session_scope() as session:
        storage = LocalFilesystemStorage(tmp_path / "documents")
        service = ExtractionApplicationService(
            session,
            storage,
            ExtractorService(build_default_llm("mock", None, None)),
        )
        first = service.extract_for_run(
            document_id=document_id,
            verification_run_id=run_id,
            trace_id=trace_id,
        )
        second = service.extract_for_run(
            document_id=document_id,
            verification_run_id=run_id,
            trace_id=trace_id,
        )
        assert first.agent_execution_id == second.agent_execution_id
        count = len(
            session.scalars(
                select(AgentExecution).where(AgentExecution.verification_run_id == run_id)
            ).all()
        )
        assert count == 1


def test_extraction_failure_marks_document_failed(
    client: tuple[TestClient, UUID, Path],
) -> None:
    test_client, customer_id, tmp_path = client
    from sqlalchemy.orm import Session

    from nova.application.ingestion import IngestCommand, IngestionService
    from nova.persistence.database import get_engine

    engine = get_engine()
    with Session(engine) as session:
        storage = LocalFilesystemStorage(tmp_path / "documents")
        ingest = IngestionService(
            session,
            storage,
            max_document_size_bytes=10 * 1024 * 1024,
            allowed_mime_types=("application/pdf", "text/plain"),
            extractor=None,
            auto_extract=False,
        )
        accepted = ingest.ingest(
            IngestCommand(
                blob=_invoice_body(),
                filename="invoice.txt",
                media_type="text/plain",
                customer_id=customer_id,
                shipment_id=None,
                document_type="INVOICE",
                external_ref=None,
                idempotency_key="fail-extract-0001",
                principal="test",
                trace_id=str(uuid4()),
            )
        )
        document_id = UUID(accepted["document_id"])
        run_id = UUID(accepted["run_id"])

    with Session(engine) as session:
        storage = LocalFilesystemStorage(tmp_path / "documents")
        failing = ExtractionApplicationService(
            session,
            storage,
            ExtractorService(MockLLM(timeout=True), max_retries=0),
        )
        result = failing.extract_for_run(
            document_id=document_id,
            verification_run_id=run_id,
            trace_id=uuid4(),
        )
        session.commit()
        assert result.status is ExtractionStatus.FAILED

    detail = test_client.get(f"/v1/documents/{document_id}", headers=AUTH)
    assert detail.json()["status"] == "FAILED"


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
