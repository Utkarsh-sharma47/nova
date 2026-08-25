"""Observability tests — logs must not include document contents."""

from __future__ import annotations

import logging
from uuid import uuid4

import pytest

from nova.documents.service import process_document
from nova.observability.metrics import DOCUMENT_PROCESSING, DOCUMENT_PROCESSING_FAILURES

from .fixtures import make_text_invoice


def test_processing_logs_ids_not_body(caplog: pytest.LogCaptureFixture) -> None:
    secret = "SECRET_SHIPMENT_VALUE_SHOULD_NOT_APPEAR"
    blob = make_text_invoice(body="INVOICE\n" + secret + "\n")
    with caplog.at_level(logging.INFO, logger="nova.documents"):
        result = process_document(
            blob,
            document_id=uuid4(),
            original_filename="invoice.txt",
            trace_id=uuid4(),
        )
    assert result.status.value == "SUCCEEDED"
    combined = " ".join(r.getMessage() for r in caplog.records)
    assert secret not in combined
    assert any("document_processing" in r.getMessage() for r in caplog.records)


def test_processing_increments_prometheus_counters() -> None:
    ok_counter = DOCUMENT_PROCESSING.labels(stage="document_processing", status="SUCCEEDED")
    fail_counter = DOCUMENT_PROCESSING_FAILURES.labels(
        stage="document_processing", error_code="DOC_CORRUPT"
    )
    before_ok = ok_counter._value.get()
    before_fail = fail_counter._value.get()

    ok = process_document(
        make_text_invoice(),
        document_id=uuid4(),
        original_filename="invoice.txt",
    )
    assert ok.status.value == "SUCCEEDED"

    failed = process_document(
        b"%PDF-not-really",
        document_id=uuid4(),
        declared_media_type="application/pdf",
        original_filename="bad.pdf",
    )
    assert failed.status.value == "FAILED"
    assert failed.error_code == "DOC_CORRUPT"

    assert ok_counter._value.get() == before_ok + 1
    assert fail_counter._value.get() == before_fail + 1
