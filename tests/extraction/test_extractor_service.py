"""Extractor service unit smoke tests (MockLLM)."""

from __future__ import annotations

import json
from uuid import uuid4

from nova.contracts.common import DocumentContent, FieldPresence
from nova.contracts.extraction import ExtractionRequest, ExtractionStatus
from nova.extraction.service import ExtractorService
from nova.llm.mock import MockLLM


def _request(text: str, fields: list[str] | None = None) -> ExtractionRequest:
    run_id = uuid4()
    return ExtractionRequest(
        trace_id=run_id,
        run_id=run_id,
        document_id=uuid4(),
        document_version_id=uuid4(),
        shipment_id=uuid4(),
        customer_id=uuid4(),
        document_type="COMMERCIAL_INVOICE",
        content=DocumentContent(
            media_type="text/plain",
            text=text,
            processor_name="test",
            processor_version="1.0.0",
        ),
        required_fields=fields or ["invoice_number", "shipper_name", "consignee_name"],
    )


def test_extract_known_fields() -> None:
    payload = {
        "fields": [
            {
                "field_name": "invoice_number",
                "value": "INV-1",
                "presence": "KNOWN",
                "confidence": 0.9,
                "uncertainty": "NONE",
                "evidence": [{"source_type": "DOCUMENT_SPAN", "snippet": "INV-1"}],
            },
            {
                "field_name": "shipper_name",
                "value": "Acme",
                "presence": "KNOWN",
                "confidence": 0.9,
                "uncertainty": "NONE",
                "evidence": [{"source_type": "DOCUMENT_SPAN", "snippet": "Acme"}],
            },
            {
                "field_name": "consignee_name",
                "value": "Globex",
                "presence": "KNOWN",
                "confidence": 0.9,
                "uncertainty": "NONE",
                "evidence": [{"source_type": "DOCUMENT_SPAN", "snippet": "Globex"}],
            },
        ]
    }
    llm = MockLLM(responses=[json.dumps(payload)])
    result = ExtractorService(llm).extract(
        _request("Invoice Number: INV-1\nShipper Name: Acme\nConsignee Name: Globex\n")
    )
    assert result.status in {ExtractionStatus.SUCCEEDED, ExtractionStatus.PARTIAL}
    by_name = {f.field_name: f for f in result.fields}
    assert by_name["invoice_number"].presence == FieldPresence.KNOWN
    assert by_name["invoice_number"].value == "INV-1"


def test_anti_fabrication_downgrades_ungrounded_known() -> None:
    payload = {
        "fields": [
            {
                "field_name": "invoice_number",
                "value": "INV-1",
                "presence": "KNOWN",
                "confidence": 0.9,
                "uncertainty": "NONE",
                "evidence": [{"source_type": "DOCUMENT_SPAN", "snippet": "INV-1"}],
            },
            {
                "field_name": "shipper_name",
                "value": "Acme",
                "presence": "KNOWN",
                "confidence": 0.9,
                "uncertainty": "NONE",
                "evidence": [{"source_type": "DOCUMENT_SPAN", "snippet": "Acme"}],
            },
            {
                "field_name": "consignee_name",
                "value": "Fabricated Party",
                "presence": "KNOWN",
                "confidence": 0.99,
                "uncertainty": "NONE",
                "evidence": [
                    {"source_type": "DOCUMENT_SPAN", "snippet": "Fabricated Party"}
                ],
            },
        ]
    }
    llm = MockLLM(responses=[json.dumps(payload)])
    result = ExtractorService(llm).extract(
        _request("Invoice Number: INV-1\nShipper Name: Acme\n")
    )
    by_name = {f.field_name: f for f in result.fields}
    assert by_name["consignee_name"].presence == FieldPresence.UNKNOWN
    assert by_name["consignee_name"].value is None


def test_empty_document_fails() -> None:
    llm = MockLLM(responses=[])
    result = ExtractorService(llm).extract(_request(""))
    assert result.status == ExtractionStatus.FAILED
    assert result.error_code == "DOCUMENT_UNREADABLE"
