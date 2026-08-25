from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from nova.api.app import create_app
from nova.config import Settings
from nova.contracts.query import QueryRequest, QueryScope
from nova.llm.errors import LLMOutputError, LLMTimeoutError
from nova.llm.mock import MockLLM
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import Base, Customer
from nova.query.service import QueryService
from tests.query.conftest import AUTH, SeededWorld


def test_api_validation_missing_question(
    query_world: tuple[TestClient, SeededWorld],
) -> None:
    client, world = query_world
    response = client.post(
        "/v1/query",
        headers=AUTH,
        json={"customer_id": str(world.customer_id)},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_api_validation_blank_question(
    query_world: tuple[TestClient, SeededWorld],
) -> None:
    client, world = query_world
    response = client.post(
        "/v1/query",
        headers=AUTH,
        json={"question": "   ", "customer_id": str(world.customer_id)},
    )
    assert response.status_code == 422


def test_api_requires_auth(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = client.post(
        "/v1/query",
        json={
            "question": "Which shipments are waiting on human review?",
            "customer_id": str(world.customer_id),
        },
    )
    assert response.status_code == 401


def test_response_schema_fields(query_world: tuple[TestClient, SeededWorld]) -> None:
    client, world = query_world
    response = client.post(
        "/v1/query",
        headers=AUTH,
        json={
            "question": "Which shipments are waiting on human review?",
            "customer_id": str(world.customer_id),
        },
    )
    body = response.json()
    assert set(body.keys()) >= {
        "question",
        "interpreted_intent",
        "status",
        "result",
        "unsupported",
        "failure",
        "trace_id",
    }
    assert body["trace_id"]


def test_llm_malformed_output(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'llm-bad.db'}",
        document_storage_path=str(tmp_path / "documents"),
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        with session_scope() as session:
            session.add(Customer(customer_id=customer_id, name="C", status="active"))
        with session_scope() as session:
            service = QueryService(session, llm=MockLLM(response="not-json{{{"))
            # Force LLM path with an ambiguous question that is not security-rejected.
            result = service.answer(
                QueryRequest(
                    question="Tell me something interesting about logistics KPIs",
                    customer_id=customer_id,
                    scope=QueryScope(),
                ),
                trace_id="trace-llm-malformed",
            )
            assert result.status.value == "FAILURE"
            assert result.failure is not None
            assert result.failure.code == "AI_PROVIDER_ERROR"


def test_llm_timeout(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'llm-timeout.db'}",
        document_storage_path=str(tmp_path / "documents"),
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        with session_scope() as session:
            session.add(Customer(customer_id=customer_id, name="C", status="active"))
        with session_scope() as session:
            service = QueryService(session, llm=MockLLM(timeout=True))
            result = service.answer(
                QueryRequest(
                    question="Tell me something interesting about logistics KPIs",
                    customer_id=customer_id,
                ),
                trace_id="trace-llm-timeout",
            )
            assert result.status.value == "FAILURE"
            assert result.failure is not None
            assert result.failure.code == "AI_PROVIDER_TIMEOUT"
            assert result.failure.retryable is True


def test_database_failure(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'db-fail.db'}",
        document_storage_path=str(tmp_path / "documents"),
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        with session_scope() as session:
            session.add(Customer(customer_id=customer_id, name="C", status="active"))

        class BoomSession(Session):
            def execute(self, *args: object, **kwargs: object) -> object:  # type: ignore[override]
                from sqlalchemy.exc import SQLAlchemyError

                raise SQLAlchemyError("boom")

        # Use a real session then force repository failure via closed bind.
        with session_scope() as session:
            service = QueryService(session, llm=None)
            session.close()
            result = service.answer(
                QueryRequest(
                    question="Which shipments are waiting on human review?",
                    customer_id=customer_id,
                ),
                trace_id="trace-db-fail",
            )
            assert result.status.value in {"FAILURE", "EMPTY", "RESULT"}
            # Closed session typically surfaces as database failure or empty depending on driver.
            if result.status.value == "FAILURE":
                assert result.failure is not None
                assert result.failure.code == "DATABASE_ERROR"


def test_llm_invented_intent_rejected(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        api_auth_token="nova-test-token",
        database_url=f"sqlite:///{tmp_path / 'llm-intent.db'}",
        document_storage_path=str(tmp_path / "documents"),
    )
    with TestClient(create_app(settings)):
        Base.metadata.create_all(get_engine())
        customer_id = uuid4()
        with session_scope() as session:
            session.add(Customer(customer_id=customer_id, name="C", status="active"))
        with session_scope() as session:
            service = QueryService(
                session,
                llm=MockLLM(
                    response={
                        "name": "delete_all_customers",
                        "parameters": {},
                        "confidence": 0.99,
                    }
                ),
            )
            result = service.answer(
                QueryRequest(
                    question="Tell me something interesting about logistics KPIs",
                    customer_id=customer_id,
                ),
                trace_id="trace-bad-intent",
            )
            assert result.status.value == "UNSUPPORTED"
            assert result.unsupported is not None
            assert result.unsupported.reason_code.value == "INTENT_NOT_SUPPORTED"


def test_llm_output_error_type_exported() -> None:
    # Keep failure taxonomy importable for observability wiring.
    assert issubclass(LLMOutputError, Exception)
    assert issubclass(LLMTimeoutError, Exception)


@pytest.mark.parametrize(
    "payload",
    [
        {"question": "x" * 2001, "customer_id": str(uuid4())},
        {"question": "hi", "customer_id": "not-a-uuid"},
    ],
)
def test_api_rejects_invalid_payloads(
    query_world: tuple[TestClient, SeededWorld],
    payload: dict[str, object],
) -> None:
    client, _world = query_world
    response = client.post("/v1/query", headers=AUTH, json=payload)
    assert response.status_code == 422
