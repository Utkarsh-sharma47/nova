"""Regression: customer expected-value rules must drive fail-closed decisions.

Exercises the real API → ingestion → pipeline → persistence path (not a
test-only decision shortcut).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from nova.agents.validator.agent import ValidatorAgent
from nova.api.app import create_app
from nova.application.extraction import build_default_llm
from nova.application.pipeline import PipelineOrchestrator
from nova.application.rules import (
    CUSTOMER_EXPECTED_FIELDS_KEY,
    customer_metadata_with_expected_fields,
    demo_control_group_expected_fields,
)
from nova.config import Settings
from nova.contracts.extraction import ExtractionStatus
from nova.contracts.routing import DecisionKind
from nova.extraction.service import ExtractorService
from nova.infrastructure.storage import LocalFilesystemStorage
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import (
    Base,
    Customer,
    Document,
    DocumentVersion,
    Shipment,
    VerificationRun,
)
from nova.validation_store import FailingValidationStore

AUTH = {"X-API-Key": "nova-test-token"}
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "demo"


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'decision.db'}",
        document_storage_path=str(tmp_path / "documents"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)) as test_client:
        Base.metadata.create_all(get_engine())
        yield test_client


def _create_demo_customer(test_client: TestClient) -> UUID:
    response = test_client.post(
        "/v1/customers",
        headers=AUTH,
        json={"name": "Control Group Demo"},
    )
    assert response.status_code == 201, response.text
    customer_id = UUID(response.json()["customer_id"])
    with session_scope() as session:
        customer = session.get(Customer, customer_id)
        assert customer is not None
        expected = customer.metadata_json.get(CUSTOMER_EXPECTED_FIELDS_KEY)
        assert isinstance(expected, dict)
        assert expected["consignee_name"] == "Harbor Goods BV"
        assert expected["port_of_loading"] == "Singapore"
    return customer_id


def _upload(
    test_client: TestClient,
    *,
    customer_id: UUID,
    path: Path,
    key: str,
) -> dict:
    response = test_client.post(
        "/v1/documents",
        headers={**AUTH, "Idempotency-Key": key},
        data={"customer_id": str(customer_id), "document_type": "INVOICE"},
        files={"file": (path.name, path.read_bytes(), "text/plain")},
    )
    assert response.status_code == 202, response.text
    return response.json()


def _equals_results(validation: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for check in validation.get("checks", []):
        field = check.get("field_name")
        code = str(check.get("rule_code") or "")
        if field and code.startswith("equals."):
            out[str(field)] = str(check.get("result"))
    return out


def test_clean_invoice_auto_approve(client: TestClient) -> None:
    customer_id = _create_demo_customer(client)
    body = _upload(
        client,
        customer_id=customer_id,
        path=FIXTURES / "synthetic_invoice_clean.txt",
        key="decision-clean-001",
    )
    document_id = body["document_id"]

    detail = client.get(f"/v1/documents/{document_id}", headers=AUTH)
    assert detail.status_code == 200
    assert detail.json()["status"] == "DECIDED"
    assert detail.json()["agreement"] == "STRONG_AGREEMENT"
    assert detail.json()["document_confidence"] is not None
    assert detail.json()["document_confidence"] >= 0.85

    validation = client.get(f"/v1/documents/{document_id}/validation", headers=AUTH).json()
    assert validation["overall_result"] == "MATCH"

    decision = client.get(f"/v1/documents/{document_id}/decision", headers=AUTH).json()
    assert decision["decision"] == "AUTO_APPROVE"


def test_rejected_invoice_not_auto_approve(client: TestClient) -> None:
    customer_id = _create_demo_customer(client)
    body = _upload(
        client,
        customer_id=customer_id,
        path=FIXTURES / "synthetic_invoice_rejected.txt",
        key="decision-reject-001",
    )
    document_id = body["document_id"]

    validation = client.get(f"/v1/documents/{document_id}/validation", headers=AUTH).json()
    assert validation["overall_result"] == "MISMATCH"
    by_field = _equals_results(validation)
    for field in (
        "consignee_name",
        "port_of_loading",
        "port_of_discharge",
        "hs_code",
        "incoterms",
        "gross_weight",
    ):
        assert by_field.get(field) == "MISMATCH", (field, by_field)

    # Persist expected/actual for at least one mismatch check.
    mismatch = next(
        c
        for c in validation["checks"]
        if c.get("rule_code") == "equals.consignee_name"
    )
    assert mismatch["result"] == "MISMATCH"
    assert mismatch["expected"] == "Harbor Goods BV"
    assert "Wrong Harbor" in str(mismatch["actual"])

    decision = client.get(f"/v1/documents/{document_id}/decision", headers=AUTH).json()
    assert decision["decision"] != "AUTO_APPROVE"
    assert decision["decision"] in {"HUMAN_REVIEW", "AMENDMENT_REQUEST"}
    assert decision.get("rationale")

    detail = client.get(f"/v1/documents/{document_id}", headers=AUTH).json()
    assert detail["agreement"] == "WEAK_AGREEMENT"
    assert detail["agreement"] != decision["decision"]


def test_uncertain_missing_fields_not_auto_approve(client: TestClient) -> None:
    customer_id = _create_demo_customer(client)
    missing = (
        b"Invoice Number: INV-CLEAN-2001\n"
        b"Seller: Acme Logistics Pte Ltd\n"
        b"Note: required control fields intentionally omitted.\n"
    )
    response = client.post(
        "/v1/documents",
        headers={**AUTH, "Idempotency-Key": "decision-uncertain-001"},
        data={"customer_id": str(customer_id), "document_type": "INVOICE"},
        files={"file": ("missing.txt", missing, "text/plain")},
    )
    assert response.status_code == 202, response.text
    document_id = response.json()["document_id"]
    validation = client.get(f"/v1/documents/{document_id}/validation", headers=AUTH).json()
    assert validation["overall_result"] in {"MISMATCH", "UNCERTAIN"}
    decision = client.get(f"/v1/documents/{document_id}/decision", headers=AUTH).json()
    assert decision["decision"] != "AUTO_APPROVE"


def test_no_customer_expected_values_not_auto_approve(client: TestClient) -> None:
    customer_id = uuid4()
    with session_scope() as session:
        session.add(
            Customer(
                customer_id=customer_id,
                name="No Expected Values",
                status="active",
                metadata_json={},
            )
        )

    body = _upload(
        client,
        customer_id=customer_id,
        path=FIXTURES / "synthetic_invoice_clean.txt",
        key="decision-no-rules-001",
    )
    validation = client.get(
        f"/v1/documents/{body['document_id']}/validation", headers=AUTH
    ).json()
    assert any(
        c.get("rule_code") == "customer.expected_values_missing"
        for c in validation.get("checks", [])
    )
    decision = client.get(
        f"/v1/documents/{body['document_id']}/decision", headers=AUTH
    ).json()
    assert decision["decision"] != "AUTO_APPROVE"


def test_validation_failure_not_auto_approve(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'fail.db'}",
        document_storage_path=str(tmp_path / "documents"),
        llm_provider="mock",
    )
    storage = LocalFilesystemStorage(str(tmp_path / "documents"))
    blob = (FIXTURES / "synthetic_invoice_clean.txt").read_bytes()
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        with session_scope() as session:
            customer_id = uuid4()
            session.add(
                Customer(
                    customer_id=customer_id,
                    name="Fail Store",
                    status="active",
                    metadata_json=customer_metadata_with_expected_fields(
                        demo_control_group_expected_fields()
                    ),
                )
            )
            shipment = Shipment(customer_id=customer_id, status="open")
            session.add(shipment)
            session.flush()
            document_id = uuid4()
            version_id = uuid4()
            run_id = uuid4()
            uri = storage.put(document_id, version_id, "clean.txt", blob)
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
                    content_sha256="a" * 64,
                    media_type="text/plain",
                    byte_size=len(blob),
                    original_filename="clean.txt",
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

            result = PipelineOrchestrator(
                session,
                storage,
                extractor=ExtractorService(build_default_llm("mock", None, None)),
                validator=ValidatorAgent(store=FailingValidationStore(), persist=True),
                auto_commit=False,
            ).run(
                document_id=document_id,
                verification_run_id=run_id,
                trace_id=uuid4(),
            )
            assert result.extraction is not None
            assert result.extraction.status is ExtractionStatus.SUCCEEDED
            assert result.decision is not None
            assert result.decision.decision is not DecisionKind.AUTO_APPROVE
            assert result.decision.decision is DecisionKind.HUMAN_REVIEW
