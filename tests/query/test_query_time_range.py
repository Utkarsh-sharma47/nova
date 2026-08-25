"""Query time-window filtering for flagged-this-week style questions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from nova.contracts.query import QueryRequest, QueryScope
from nova.query.classifier import classify_deterministic
from nova.query.executors import _list_shipments_by_decision


def test_classifier_detects_flagged_this_week() -> None:
    outcome = classify_deterministic(
        QueryRequest(
            question="how many shipments were flagged this week?",
            customer_id=uuid4(),
            scope=QueryScope(),
        )
    )
    assert outcome.intent is not None
    assert outcome.intent.parameters["decision"] == "HUMAN_REVIEW"
    assert outcome.intent.parameters["time_range"]["preset"] == "this_week"


def test_executor_applies_time_range(monkeypatch: object) -> None:
    captured: dict[str, object] = {}

    class FakeRepo:
        def shipments_by_decision(self, *args: object, **kwargs: object) -> list[object]:
            captured.update(kwargs)
            return []

    status, payload = _list_shipments_by_decision(
        {"decision": "HUMAN_REVIEW", "time_range": {"preset": "this_week"}},
        customer_id=uuid4(),
        repository=FakeRepo(),  # type: ignore[arg-type]
        max_results=20,
    )
    assert status.value == "EMPTY"
    assert "time window" in payload.answer_summary
    assert captured.get("decided_after") is not None
    assert isinstance(captured["decided_after"], datetime)
    assert captured["decided_after"] > datetime.now(UTC) - timedelta(days=8)  # type: ignore[operator]
