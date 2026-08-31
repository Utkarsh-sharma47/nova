"""Natural-language phrasing regressions for the query agent.

These cases were all observed failing (UNSUPPORTED, or silently answered as a
different question) against the running stack. Each asserts the mapped intent and
its parameters, and where a count is produced it is checked against independently
computed database state.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from nova.api.app import create_app
from nova.config import Settings
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import Base, Customer
from nova.query.repository import reference_matches
from tests.query.conftest import AUTH
from tests.query.seed import SEED_DOCUMENTS, seed_query_dataset


@pytest.fixture
def phrasing_world(tmp_path: Path) -> Iterator[tuple[TestClient, UUID]]:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'query-phrasing.db'}",
        document_storage_path=str(tmp_path / "documents"),
        llm_provider="mock",
    )
    with TestClient(create_app(settings)) as client:
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        with session_scope() as session:
            session.add(
                Customer(customer_id=customer_id, name="Phrasing Customer", status="active")
            )
            session.flush()
            seed_query_dataset(session, customer_id)
        yield client, customer_id


def _ask(client: TestClient, customer_id: UUID, question: str) -> dict[str, Any]:
    response = client.post(
        "/v1/query",
        headers=AUTH,
        json={"question": question, "customer_id": str(customer_id)},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize(
    ("question", "intent", "expected_params"),
    [
        # Superlative agreement phrasing.
        (
            "Show me the strongest agreement documents.",
            "list_documents_by_agreement",
            {"agreement": "STRONG_AGREEMENT"},
        ),
        (
            "Show me the weakest agreement documents.",
            "list_documents_by_agreement",
            {"agreement": "WEAK_AGREEMENT"},
        ),
        # Bare adjective, no "agreement" noun.
        (
            "show weak documents",
            "list_documents_by_agreement",
            {"agreement": "WEAK_AGREEMENT"},
        ),
        # Disposition named without a subject noun.
        ("how many were flagged?", "count_documents_by_decision", {"decision": "HUMAN_REVIEW"}),
        ("how many need review?", "count_documents_by_decision", {"decision": "HUMAN_REVIEW"}),
        (
            "How many documents require amendment?",
            "count_documents_by_decision",
            {"decision": "AMENDMENT_REQUEST"},
        ),
        # "approved" without the "auto" prefix, scoped to shipments.
        (
            "how many shipments were approved?",
            "list_shipments_by_decision",
            {"decision": "AUTO_APPROVE"},
        ),
        # Failure phrasing that never says "why" or "mismatch".
        (
            "what went wrong with INV-MESSY-2001?",
            "explain_document_review",
            {"document_ref": "INV-MESSY-2001"},
        ),
        (
            "which fields failed in INV-MESSY-2001?",
            "get_document_mismatched_fields",
            {"document_ref": "INV-MESSY-2001"},
        ),
        # Validation results addressed by invoice number rather than UUID.
        (
            "Show me the validation results for INV-MESSY-2001.",
            "get_document_validation",
            {"document_ref": "INV-MESSY-2001"},
        ),
    ],
)
def test_phrasing_maps_to_expected_intent(
    phrasing_world: tuple[TestClient, UUID],
    question: str,
    intent: str,
    expected_params: dict[str, Any],
) -> None:
    client, customer_id = phrasing_world
    body = _ask(client, customer_id, question)
    assert body["status"] in {"RESULT", "EMPTY"}, body
    assert body["interpreted_intent"] is not None, body
    assert body["interpreted_intent"]["name"] == intent, body["interpreted_intent"]
    params = body["interpreted_intent"]["parameters"]
    for key, value in expected_params.items():
        assert params.get(key) == value, params


def test_mismatched_fields_by_reference_matches_seeded_state(
    phrasing_world: tuple[TestClient, UUID],
) -> None:
    """A human reference must resolve, and the fields must come from the database."""
    client, customer_id = phrasing_world
    seeded = next(doc for doc in SEED_DOCUMENTS if doc.invoice_number == "INV-MESSY-2001")
    body = _ask(client, customer_id, "What fields mismatched in the messy invoice?")

    assert body["status"] == "RESULT", body
    params = body["interpreted_intent"]["parameters"]
    assert params["document_ref"] == "messy"
    summary = body["result"]["answer_summary"]
    assert "INV-MESSY-2001" in summary
    for field_name in seeded.mismatch_fields:
        assert field_name in summary, summary


def test_ambiguous_reference_is_reported_not_silently_resolved(
    phrasing_world: tuple[TestClient, UUID],
) -> None:
    """Two INV-CLEAN-* documents exist; picking one arbitrarily would be wrong."""
    client, customer_id = phrasing_world
    body = _ask(client, customer_id, "What fields mismatched in the clean invoice?")

    assert body["status"] == "UNSUPPORTED", body
    assert body["unsupported"]["reason_code"] == "AMBIGUOUS_INTENT"
    suggestions = " ".join(body["unsupported"]["suggestions"])
    assert "INV-CLEAN-1001" in suggestions
    assert "INV-CLEAN-1002" in suggestions
    assert body["result"] is None


def test_fields_failed_without_a_reference_asks_instead_of_guessing(
    phrasing_world: tuple[TestClient, UUID],
) -> None:
    client, customer_id = phrasing_world
    body = _ask(client, customer_id, "which fields failed?")

    assert body["status"] == "UNSUPPORTED", body
    assert body["unsupported"]["reason_code"] == "MISSING_SCOPE_ID"
    assert body["result"] is None


@pytest.mark.parametrize(
    ("invoice_number", "reference", "expected"),
    [
        ("INV-REJECT-9001", "reject", True),
        ("INV-REJECT-9001", "rejected", True),  # inflected form must still resolve
        ("INV-MESSY-2001", "messy", True),
        ("INV-CLEAN-1001", "clean", True),
        ("INV-REJECT-9001", "inv-reject-9001", True),
        ("INV-REJECT-9001", "messy", False),
        ("INV-CLEAN-1001", "1002", False),
        # A token shorter than 4 characters must not match everything.
        ("INV-CLEAN-1001", "invoice", False),
    ],
)
def test_reference_matches_handles_inflection_without_over_matching(
    invoice_number: str,
    reference: str,
    expected: bool,
) -> None:
    assert reference_matches(invoice_number, reference) is expected
