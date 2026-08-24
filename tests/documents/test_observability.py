"""Observability tests — logs must not include document contents."""

from __future__ import annotations

import logging
from uuid import uuid4

import pytest

from nova.documents.service import process_document

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
