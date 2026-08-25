"""End-to-end Part 1 pipeline integration tests (Phase 7).

Uses MockLLM only — no live provider credentials.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from nova.agents.validator.agent import ValidatorAgent
from nova.api.app import create_app
from nova.application.extraction import ExtractionApplicationService, build_default_llm
from nova.application.pipeline import PipelineOrchestrator
from nova.application.validation_persistence import SqlValidationStore
from nova.config import Settings
from nova.contracts.common import FieldPresence, UncertaintyFlag
from nova.contracts.extraction import ExtractedField, ExtractionResult, ExtractionStatus
from nova.contracts.routing import DecisionKind
from nova.contracts.validation import CustomerRuleSnapshot, ValidationOutcome
from nova.domain.errors import InvalidLifecycleTransition
from nova.domain.lifecycle import DocumentStatus, assert_document_transition
from nova.extraction.service import ExtractorService
from nova.infrastructure.storage import LocalFilesystemStorage
from nova.llm.errors import LLMProviderError
from nova.llm.mock import MockLLM
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import (
    AgentExecution,
    Base,
    Customer,
    DecisionRecord,
    Document,
    DocumentVersion,
    Shipment,
    ValidationRecordRow,
    VerificationRun,
)
from nova.router.llm import LlmAssistSuggestion
from nova.router.service import RouterService
from nova.validation_store import FailingValidationStore

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
        b"Consignee: Globex Corp\n"
        b"HS Code: 8471.30\n"
        b"Port of Loading: Singapore\n"
        b"Port of Discharge: Rotterdam\n"
        b"Incoterms: FOB\n"
        b"Description of Goods: Widget assemblies\n"
        b"Gross Weight: 1250 KG\n"
        b"Currency: USD\n"
        b"Total Amount: 1250.00\n"
    )


def _bol_body() -> bytes:
    return (
        b"BL Number: BL-9001\n"
        b"Vessel Name: Pacific Star\n"
        b"Shipper Name: Acme Trading\n"
        b"Consignee Name: Globex Corp\n"
        b"Port of Loading: Shanghai\n"
        b"Port of Discharge: Los Angeles\n"
        b"Container Number: MSKU1234567\n"
        b"HS Code: 8471.30\n"
        b"Incoterms: CIF\n"
        b"Description of Goods: Widget assemblies\n"
        b"Gross Weight: 1250 KG\n"
        b"Invoice Number: INV-42\n"
    )


def _missing_invoice() -> bytes:
    return b"Invoice Number: INV-99\nSeller: Acme\n"


def _ingest(
    test_client: TestClient,
    customer_id: UUID,
    body: bytes,
    document_type: str = "INVOICE",
    key: str = "request-key-0001",
) -> dict[str, Any]:
    response = test_client.post(
        "/v1/documents",
        headers={**AUTH, "Idempotency-Key": key},
        data={"customer_id": str(customer_id), "document_type": document_type},
        files={"file": ("doc.txt", body, "text/plain")},
    )
    assert response.status_code == 202, response.text
    return response.json()


def _seed_run(
    session: Any,
    storage: LocalFilesystemStorage,
    *,
    blob: bytes,
    sha: str,
) -> tuple[UUID, UUID, UUID]:
    customer_id = uuid4()
    session.add(Customer(customer_id=customer_id, name="C", status="active"))
    shipment = Shipment(customer_id=customer_id, status="open")
    session.add(shipment)
    session.flush()
    document_id = uuid4()
    version_id = uuid4()
    run_id = uuid4()
    uri = storage.put(document_id, version_id, "x.txt", blob)
    session.add(
        Document(
            document_id=document_id,
            shipment_id=shipment.shipment_id,
            document_type="commercial_invoice",
            status="content_available",
            ingestion_channel="upload",
            current_version_id=version_id,
        )
    )
    session.flush()
    session.add(
        DocumentVersion(
            document_version_id=version_id,
            document_id=document_id,
            shipment_id=shipment.shipment_id,
            document_type="commercial_invoice",
            version_number=1,
            storage_uri=uri,
            content_sha256=sha,
            media_type="text/plain",
            byte_size=len(blob),
            original_filename="x.txt",
        )
    )
    session.add(
        VerificationRun(
            verification_run_id=run_id,
            shipment_id=shipment.shipment_id,
            status="queued",
            trigger="test",
            document_version_ids=[str(version_id)],
        )
    )
    session.flush()
    return document_id, run_id, customer_id


def _orchestrator(
    session: Any,
    storage: LocalFilesystemStorage,
    **kwargs: Any,
) -> PipelineOrchestrator:
    """Build orchestrator with auto_commit=False (required inside session_scope/begin())."""
    kwargs.setdefault("auto_commit", False)
    return PipelineOrchestrator(session, storage, **kwargs)


def test_01_valid_invoice_pipeline(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, customer_id, _ = client
    body = _ingest(
        test_client,
        customer_id,
        body=_invoice_body(),
        document_type="INVOICE",
        key="p7-inv-01",
    )
    document_id = body["document_id"]

    detail = test_client.get(f"/v1/documents/{document_id}", headers=AUTH)
    assert detail.status_code == 200
    assert detail.json()["status"] == "DECIDED"
    assert detail.json()["extraction"] is not None

    validation = test_client.get(f"/v1/documents/{document_id}/validation", headers=AUTH)
    assert validation.status_code == 200
    assert validation.json()["overall_result"] == "MATCH"

    decision = test_client.get(f"/v1/documents/{document_id}/decision", headers=AUTH)
    assert decision.status_code == 200
    assert decision.json()["decision"] == "AUTO_APPROVE"

    shipment = test_client.get(f"/v1/shipments/{body['shipment_id']}", headers=AUTH).json()
    assert shipment["latest_decision"]["decision"] == "AUTO_APPROVE"


def test_02_valid_bol_pipeline(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, customer_id, _ = client
    body = _ingest(
        test_client,
        customer_id,
        _bol_body(),
        document_type="BILL_OF_LADING",
        key="p7-bol-02",
    )
    document_id = body["document_id"]
    detail = test_client.get(f"/v1/documents/{document_id}", headers=AUTH)
    assert detail.status_code == 200
    assert detail.json()["status"] == "DECIDED"
    decision = test_client.get(f"/v1/documents/{document_id}/decision", headers=AUTH)
    assert decision.status_code == 200
    assert decision.json()["decision"] == "AUTO_APPROVE"


def test_03_missing_field(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, customer_id, _ = client
    body = _ingest(
        test_client,
        customer_id,
        _missing_invoice(),
        document_type="INVOICE",
        key="p7-miss-03",
    )
    document_id = body["document_id"]
    validation = test_client.get(f"/v1/documents/{document_id}/validation", headers=AUTH)
    assert validation.status_code == 200
    assert validation.json()["overall_result"] == "MISMATCH"
    decision = test_client.get(f"/v1/documents/{document_id}/decision", headers=AUTH)
    assert decision.status_code == 200
    # Partial extraction + missing critical fields prefer HUMAN_REVIEW; never AUTO_APPROVE.
    assert decision.json()["decision"] in {"AMENDMENT_REQUEST", "HUMAN_REVIEW"}
    assert decision.json()["decision"] != "AUTO_APPROVE"


def test_04_ambiguous_field_human_review(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'amb.db'}",
        document_storage_path=str(tmp_path / "documents"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "documents"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_invoice_body(),
                sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            )
            trace_id = uuid4()
            extractor = ExtractorService(build_default_llm("mock", None, None))
            ExtractionApplicationService(session, storage, extractor).extract_for_run(
                document_id=document_id,
                verification_run_id=run_id,
                trace_id=trace_id,
            )
            exec_row = session.scalars(
                select(AgentExecution).where(AgentExecution.verification_run_id == run_id)
            ).one()
            result = ExtractionResult.model_validate(exec_row.result_json)
            fields: list[ExtractedField] = []
            for field in result.fields:
                if field.field_name == "invoice_number":
                    fields.append(
                        ExtractedField(
                            trace_id=trace_id,
                            field_name="invoice_number",
                            value=None,
                            presence=FieldPresence.AMBIGUOUS,
                            uncertainty=UncertaintyFlag.OTHER,
                            evidence=[],
                            candidates=[{"value": "INV-1", "confidence": 0.4}],
                        )
                    )
                else:
                    fields.append(field)
            exec_row.result_json = result.model_copy(update={"fields": fields}).model_dump(
                mode="json"
            )
            session.flush()

            rules = [
                CustomerRuleSnapshot(
                    trace_id=trace_id,
                    rule_id=uuid4(),
                    rule_code="eq.invoice_number",
                    version="1",
                    severity="BLOCKING",
                    blocking=True,
                    expression={"op": "equals", "field": "invoice_number", "expected": "INV-42"},
                )
            ]
            store = SqlValidationStore(session)
            out = _orchestrator(
                session,
                storage,
                extractor=extractor,
                validator=ValidatorAgent(store=store, persist=True),
                router=RouterService(),
                rules=rules,
            ).run(document_id=document_id, verification_run_id=run_id, trace_id=trace_id)

            assert out.validation is not None
            assert any(c.outcome is ValidationOutcome.UNCERTAIN for c in out.validation.checks)
            assert out.decision is not None
            assert out.decision.decision is DecisionKind.HUMAN_REVIEW


def test_05_validation_mismatch_amendment(tmp_path: Path) -> None:
    """Pure blocking MISMATCH (full extraction) → AMENDMENT_REQUEST."""
    settings = Settings(
        app_env="test",
        api_auth_token="t",
        database_url=f"sqlite:///{tmp_path / 'mm.db'}",
        document_storage_path=str(tmp_path / "docs"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "docs"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_invoice_body(),
                sha="5555555555555555555555555555555555555555555555555555555555555555",
            )
            trace_id = uuid4()
            rules = [
                CustomerRuleSnapshot(
                    trace_id=trace_id,
                    rule_id=uuid4(),
                    rule_code="eq.invoice_number",
                    version="1",
                    severity="BLOCKING",
                    blocking=True,
                    expression={
                        "op": "equals",
                        "field": "invoice_number",
                        "expected": "WRONG-INV",
                    },
                )
            ]
            out = _orchestrator(
                session,
                storage,
                extractor=ExtractorService(build_default_llm("mock", None, None)),
                rules=rules,
            ).run(document_id=document_id, verification_run_id=run_id, trace_id=trace_id)
            assert out.validation is not None
            assert any(c.outcome is ValidationOutcome.MISMATCH for c in out.validation.checks)
            assert out.decision is not None
            assert out.decision.decision is DecisionKind.AMENDMENT_REQUEST


def test_06_human_review_shipment_alias(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, customer_id, _ = client
    body = _ingest(
        test_client,
        customer_id,
        _missing_invoice(),
        document_type="INVOICE",
        key="p7-hr-06",
    )
    resp = test_client.get(f"/v1/shipments/{body['shipment_id']}/decision", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["decision"] in {"AMENDMENT_REQUEST", "HUMAN_REVIEW"}
    val = test_client.get(f"/v1/shipments/{body['shipment_id']}/validation", headers=AUTH)
    assert val.status_code == 200


def test_07_amendment_request(tmp_path: Path) -> None:
    test_05_validation_mismatch_amendment(tmp_path)


def test_08_extractor_failure(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="t",
        database_url=f"sqlite:///{tmp_path / 'ext.db'}",
        document_storage_path=str(tmp_path / "docs"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "docs"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_invoice_body(),
                sha="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            )
            result = _orchestrator(
                session,
                storage,
                extractor=ExtractorService(
                    MockLLM(fail_with=LLMProviderError("boom"), fail_times=99)
                ),
            ).run(document_id=document_id, verification_run_id=run_id, trace_id=uuid4())
            assert result.stage.value == "failed"
            assert result.extraction is not None
            assert result.extraction.status is ExtractionStatus.FAILED
            assert result.validation is None
            assert result.decision is None
            assert (
                session.scalar(
                    select(DecisionRecord).where(DecisionRecord.document_id == document_id)
                )
                is None
            )


def test_09_validator_failure_fail_closed(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="t",
        database_url=f"sqlite:///{tmp_path / 'val.db'}",
        document_storage_path=str(tmp_path / "docs"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "docs"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_invoice_body(),
                sha="cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            )
            sql_store = SqlValidationStore(session)
            out = _orchestrator(
                session,
                storage,
                extractor=ExtractorService(build_default_llm("mock", None, None)),
                validator=ValidatorAgent(store=FailingValidationStore(), persist=True),
                validation_store=sql_store,
            ).run(document_id=document_id, verification_run_id=run_id, trace_id=uuid4())
            assert out.decision is not None
            assert out.decision.decision is not DecisionKind.AUTO_APPROVE


def test_10_router_failure(tmp_path: Path) -> None:
    class BoomRouter(RouterService):
        def decide(self, request: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            raise RuntimeError("router exploded")

    settings = Settings(
        app_env="test",
        api_auth_token="t",
        database_url=f"sqlite:///{tmp_path / 'r.db'}",
        document_storage_path=str(tmp_path / "docs"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "docs"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_invoice_body(),
                sha="dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            )
            with pytest.raises(RuntimeError):
                _orchestrator(
                    session,
                    storage,
                    extractor=ExtractorService(build_default_llm("mock", None, None)),
                    router=BoomRouter(),
                ).run(document_id=document_id, verification_run_id=run_id, trace_id=uuid4())
            session.expire_all()
            doc = session.get(Document, document_id)
            assert doc is not None
            assert doc.status == "failed"


def test_11_malformed_llm_output(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="t",
        database_url=f"sqlite:///{tmp_path / 'm.db'}",
        document_storage_path=str(tmp_path / "docs"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "docs"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_invoice_body(),
                sha="eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            )
            out = _orchestrator(
                session,
                storage,
                extractor=ExtractorService(MockLLM(scripted=["not-json{{{", "still-bad", "x"])),
            ).run(document_id=document_id, verification_run_id=run_id, trace_id=uuid4())
            assert out.extraction is not None
            assert out.extraction.status is ExtractionStatus.FAILED
            assert out.decision is None


def test_12_llm_timeout(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="t",
        database_url=f"sqlite:///{tmp_path / 't.db'}",
        document_storage_path=str(tmp_path / "docs"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "docs"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_invoice_body(),
                sha="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            )
            out = _orchestrator(
                session,
                storage,
                extractor=ExtractorService(MockLLM(timeout=True)),
            ).run(document_id=document_id, verification_run_id=run_id, trace_id=uuid4())
            assert out.extraction is not None
            assert out.extraction.status is ExtractionStatus.FAILED


def test_13_database_failure_helper() -> None:
    store = FailingValidationStore()
    with pytest.raises(RuntimeError):
        from nova.contracts.validation import ValidationResult, ValidationStatus

        store.append(
            ValidationResult(
                trace_id=uuid4(),
                document_id=uuid4(),
                document_version_id=uuid4(),
                shipment_id=uuid4(),
                engine_version="x",
                status=ValidationStatus.FAILED,
                error_code="X",
                error_message="x",
            ),
            validator_version="0",
        )


def test_14_duplicate_ingestion(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, customer_id, _ = client
    a = _ingest(
        test_client,
        customer_id,
        _invoice_body(),
        document_type="INVOICE",
        key="dup-key-14",
    )
    b = _ingest(
        test_client,
        customer_id,
        _invoice_body(),
        document_type="INVOICE",
        key="dup-key-14",
    )
    assert a["document_id"] == b["document_id"]
    assert b["idempotent_replay"] is True


def test_15_idempotent_pipeline_replay(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, customer_id, tmp_path = client
    body = _ingest(
        test_client,
        customer_id,
        _invoice_body(),
        document_type="INVOICE",
        key="replay-15",
    )
    run_id = UUID(body["run_id"])
    document_id = UUID(body["document_id"])
    storage = LocalFilesystemStorage(str(tmp_path / "documents"))
    with session_scope() as session:
        orch = _orchestrator(
            session,
            storage,
            extractor=ExtractorService(build_default_llm("mock", None, None)),
        )
        again = orch.run(
            document_id=document_id,
            verification_run_id=run_id,
            trace_id=uuid4(),
        )
        assert again.idempotent_replay is True
        assert (
            len(
                session.scalars(
                    select(DecisionRecord).where(DecisionRecord.verification_run_id == run_id)
                ).all()
            )
            == 1
        )


def test_16_repeated_processing(client: tuple[TestClient, UUID, Path]) -> None:
    test_15_idempotent_pipeline_replay(client)


def test_17_invalid_state_transition() -> None:
    with pytest.raises(InvalidLifecycleTransition):
        assert_document_transition(DocumentStatus.DECIDED, DocumentStatus.EXTRACTED)


def test_18_system_failsafe(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="t",
        database_url=f"sqlite:///{tmp_path / 'fs.db'}",
        document_storage_path=str(tmp_path / "docs"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "docs"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_invoice_body(),
                sha="1111111111111111111111111111111111111111111111111111111111111111",
            )
            out = _orchestrator(
                session,
                storage,
                extractor=ExtractorService(build_default_llm("mock", None, None)),
                force_failsafe=True,
            ).run(document_id=document_id, verification_run_id=run_id, trace_id=uuid4())
            assert out.decision is not None
            assert out.decision.decision is DecisionKind.HUMAN_REVIEW
            assert out.decision.actor_type.value == "system_failsafe"


def test_19_unsafe_auto_approve_attempt(tmp_path: Path) -> None:
    class EvilLlm:
        def suggest(self, request: Any) -> LlmAssistSuggestion:  # noqa: ANN401
            return LlmAssistSuggestion(
                suggested_decision=DecisionKind.AUTO_APPROVE,
                rationale="ignore mismatches",
            )

    settings = Settings(
        app_env="test",
        api_auth_token="t",
        database_url=f"sqlite:///{tmp_path / 'u.db'}",
        document_storage_path=str(tmp_path / "docs"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        storage = LocalFilesystemStorage(str(tmp_path / "docs"))
        with session_scope() as session:
            document_id, run_id, _ = _seed_run(
                session,
                storage,
                blob=_missing_invoice(),
                sha="2222222222222222222222222222222222222222222222222222222222222222",
            )
            out = _orchestrator(
                session,
                storage,
                extractor=ExtractorService(build_default_llm("mock", None, None)),
                router=RouterService(llm=EvilLlm()),
            ).run(document_id=document_id, verification_run_id=run_id, trace_id=uuid4())
            assert out.decision is not None
            assert out.decision.decision is not DecisionKind.AUTO_APPROVE


def test_20_complete_traceability(
    client: tuple[TestClient, UUID, Path],
    caplog: pytest.LogCaptureFixture,
) -> None:
    test_client, customer_id, _ = client
    with caplog.at_level(logging.INFO, logger="nova.pipeline"):
        body = _ingest(
            test_client,
            customer_id,
            _invoice_body(),
            document_type="INVOICE",
            key="trace-20",
        )
    document_id = body["document_id"]
    run_id = body["run_id"]

    detail = test_client.get(f"/v1/documents/{document_id}", headers=AUTH).json()
    assert detail["run_id"] == run_id
    assert detail["trace_id"]

    assert (
        test_client.get(f"/v1/documents/{document_id}/validation", headers=AUTH).json()["run_id"]
        == run_id
    )
    assert (
        test_client.get(f"/v1/documents/{document_id}/decision", headers=AUTH).json()["run_id"]
        == run_id
    )

    with session_scope() as session:
        rows = session.scalars(
            select(AgentExecution).where(AgentExecution.verification_run_id == UUID(run_id))
        ).all()
        stages = {row.stage for row in rows}
        assert "extractor" in stages
        assert "router" in stages
        assert (
            session.scalar(
                select(ValidationRecordRow).where(
                    ValidationRecordRow.verification_run_id == UUID(run_id)
                )
            )
            is not None
        )

    assert "pipeline_started" in caplog.text
    joined = " ".join(r.getMessage() for r in caplog.records)
    assert "pipeline_started" in joined


def test_ops_endpoints(client: tuple[TestClient, UUID, Path]) -> None:
    test_client, _, _ = client
    assert test_client.get("/health").json()["status"] == "ok"
    assert test_client.get("/ready").status_code == 200
    assert test_client.get("/metrics").status_code == 200
