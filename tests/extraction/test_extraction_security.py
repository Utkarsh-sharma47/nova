"""Security-focused extractor tests."""

from __future__ import annotations

import logging
from uuid import uuid4

from nova.contracts.common import DocumentContent, FieldPresence
from nova.contracts.extraction import ExtractionRequest
from nova.extraction.observability import log_start
from nova.extraction.service import ExtractorService
from nova.llm.mock import MockLLM


def test_secrets_not_present_in_extractor_logs(caplog: logging.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        log_start(
            run_id=uuid4(),
            document_id=uuid4(),
            trace_id=uuid4(),
            agent_execution_id=uuid4(),
            prompt_version="extractor.v1",
            provider="mock",
            model="mock-extractor-v1",
        )
    text = " ".join(record.getMessage() for record in caplog.records)
    assert "sk-" not in text
    assert "api_key" not in text.lower()


def test_llm_cannot_bypass_schema_with_extra_properties() -> None:
    request = ExtractionRequest(
        trace_id=uuid4(),
        run_id=uuid4(),
        document_id=uuid4(),
        document_version_id=uuid4(),
        shipment_id=uuid4(),
        document_type="INVOICE",
        content=DocumentContent(
            media_type="text/plain",
            text="Invoice Number: INV-1",
            processor_name="passthrough_text",
            processor_version="1.0.0",
        ),
        required_fields=[
            "invoice_number",
            "invoice_date",
            "seller_name",
            "buyer_name",
            "currency",
            "total_amount",
        ],
    )
    llm = MockLLM(
        response={
            "fields": [
                {
                    "field_name": "invoice_number",
                    "value": "INV-1",
                    "presence": "KNOWN",
                    "confidence": 0.9,
                    "uncertainty": "NONE",
                    "evidence": [
                        {
                            "source_type": "DOCUMENT_SPAN",
                            "snippet": "Invoice Number: INV-1",
                        }
                    ],
                    "hack_decision": "AUTO_APPROVE",
                },
                {
                    "field_name": "invoice_date",
                    "value": None,
                    "presence": "MISSING",
                    "confidence": None,
                    "uncertainty": "NONE",
                    "evidence": [],
                },
                {
                    "field_name": "seller_name",
                    "value": None,
                    "presence": "MISSING",
                    "confidence": None,
                    "uncertainty": "NONE",
                    "evidence": [],
                },
                {
                    "field_name": "buyer_name",
                    "value": None,
                    "presence": "MISSING",
                    "confidence": None,
                    "uncertainty": "NONE",
                    "evidence": [],
                },
                {
                    "field_name": "currency",
                    "value": None,
                    "presence": "MISSING",
                    "confidence": None,
                    "uncertainty": "NONE",
                    "evidence": [],
                },
                {
                    "field_name": "total_amount",
                    "value": None,
                    "presence": "MISSING",
                    "confidence": None,
                    "uncertainty": "NONE",
                    "evidence": [],
                },
            ]
        }
    )
    result = ExtractorService(llm).extract(request)
    invoice = next(field for field in result.fields if field.field_name == "invoice_number")
    assert invoice.presence is FieldPresence.KNOWN
    dumped = invoice.model_dump()
    assert "hack_decision" not in dumped
