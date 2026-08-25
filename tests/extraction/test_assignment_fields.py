"""Assignment field catalog + anti-fabrication coverage for GoComet 2A."""

from __future__ import annotations

import base64
import json
from uuid import uuid4

from nova.contracts.common import DocumentContent, DocumentImage, FieldPresence
from nova.contracts.extraction import ExtractionRequest, ExtractionStatus
from nova.extraction.fields import ASSIGNMENT_FIELDS, required_fields_for
from nova.extraction.heuristic import heuristic_extractor_response
from nova.extraction.service import ExtractorService
from nova.llm.mock import MockLLM
from nova.llm.port import LLMMessage, LLMRequest


def test_assignment_fields_present_for_invoice_and_bol() -> None:
    invoice = required_fields_for("INVOICE")
    bol = required_fields_for("BILL_OF_LADING")
    for name in ASSIGNMENT_FIELDS:
        assert name in invoice
        assert name in bol


def test_heuristic_extracts_assignment_fields_without_invention() -> None:
    text = (
        "Invoice Number: INV-1\n"
        "Consignee: Harbor Goods BV\n"
        "HS Code: 8471.30\n"
        "Port of Loading: Singapore\n"
        "Port of Discharge: Rotterdam\n"
        "Incoterms: FOB\n"
        "Description of Goods: Widgets\n"
        "Gross Weight: 100 KG\n"
    )
    request = LLMRequest(
        messages=[
            LLMMessage(role="system", content="x"),
            LLMMessage(
                role="user",
                content=json.dumps(
                    {
                        "document_type_hint": "INVOICE",
                        "required_fields": list(ASSIGNMENT_FIELDS),
                        "document": {"text": text},
                    }
                ),
            ),
        ]
    )
    payload = heuristic_extractor_response(request)
    by_name = {item["field_name"]: item for item in payload["fields"]}
    assert by_name["invoice_number"]["presence"] == "KNOWN"
    assert by_name["hs_code"]["value"] == "8471.30"
    assert by_name["incoterms"]["value"] == "FOB"
    assert by_name["description_of_goods"]["value"] == "Widgets"
    assert by_name["gross_weight"]["value"] == "100 KG"
    assert by_name["consignee_name"]["evidence"]


def test_heuristic_leaves_missing_assignment_fields_missing() -> None:
    request = LLMRequest(
        messages=[
            LLMMessage(
                role="user",
                content=json.dumps(
                    {
                        "document_type_hint": "INVOICE",
                        "required_fields": list(ASSIGNMENT_FIELDS),
                        "document": {"text": "Invoice Number: INV-ONLY\n"},
                    }
                ),
            )
        ]
    )
    payload = heuristic_extractor_response(request)
    by_name = {item["field_name"]: item for item in payload["fields"]}
    assert by_name["invoice_number"]["presence"] == "KNOWN"
    assert by_name["hs_code"]["presence"] == "MISSING"
    assert by_name["hs_code"]["value"] is None


def test_image_only_document_does_not_fabricate_with_mock() -> None:
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    content = DocumentContent(
        media_type="image/png",
        text=None,
        images=[
            DocumentImage(
                media_type="image/png",
                data_base64=base64.b64encode(png).decode("ascii"),
            )
        ],
        processor_name="raster_image",
        processor_version="1.0.0",
        warnings=["no_local_ocr_vision_llm_required"],
    )
    service = ExtractorService(MockLLM(factory=heuristic_extractor_response))
    result = service.extract(
        ExtractionRequest(
            trace_id=uuid4(),
            run_id=uuid4(),
            document_id=uuid4(),
            document_version_id=uuid4(),
            shipment_id=uuid4(),
            document_type="INVOICE",
            content=content,
            required_fields=list(ASSIGNMENT_FIELDS),
        )
    )
    assert result.status is ExtractionStatus.PARTIAL
    assert all(field.presence is FieldPresence.MISSING for field in result.fields)
    assert all(field.value is None for field in result.fields)
