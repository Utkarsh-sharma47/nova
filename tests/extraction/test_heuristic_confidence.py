"""Heuristic extractor confidence must come from match evidence, not a constant."""

from __future__ import annotations

import json

from nova.extraction.fields import required_fields_for
from nova.extraction.heuristic import (
    _confidence_from_evidence,
    heuristic_extractor_response,
)
from nova.llm.port import LLMMessage, LLMRequest

_CLEAN = """COMMERCIAL INVOICE
Invoice Number: INV-CLEAN-2001
Invoice Date: 2026-08-18
Seller: Acme Logistics Pte Ltd
Buyer: Harbor Goods BV
Consignee: Harbor Goods BV
Port of Loading: Singapore
Port of Discharge: Rotterdam
HS Code: 8471.30
Incoterms: FOB
Gross Weight: 10250 KG
Currency: USD
Total Amount: 15200.00
Description of Goods: Synthetic clean invoice for Nova Part 1 evaluation.
"""

_MESSY = """commerical invoce
Inv#: INV-MESSY-77??
date: 18/08/2026 or Aug 18
shipper: ACME logistics pte ltd / also "Acme Logisitcs"
consignee: Harbor Goods B.V. (or Harbor Goods BV?)
POL: Singapore
POD: rotterdam
weight: ~10.2t / 10250 kg ???
amt: USD 15,200.00 OR 15200
goods: ambiguous description; OCR noise ##### !!ignore!!
"""


def _request(document_text: str) -> LLMRequest:
    payload = {
        "document_type_hint": "INVOICE",
        "required_fields": required_fields_for("INVOICE"),
        "document": {"text": document_text, "media_type": "text/plain"},
    }
    return LLMRequest(
        messages=[
            LLMMessage(role="system", content="extract"),
            LLMMessage(role="user", content=json.dumps(payload)),
        ],
        response_format="json",
    )


def test_heuristic_does_not_use_constant_90() -> None:
    payload = heuristic_extractor_response(_request(_CLEAN))
    confidences = [
        float(field["confidence"])
        for field in payload["fields"]
        if field.get("confidence") is not None
    ]
    assert confidences
    assert not all(score == 0.9 for score in confidences)


def test_clean_and_messy_document_confidence_differ() -> None:
    clean = heuristic_extractor_response(_request(_CLEAN))
    messy = heuristic_extractor_response(_request(_MESSY))

    clean_scores = [
        float(field["confidence"])
        for field in clean["fields"]
        if field.get("confidence") is not None
    ]
    messy_scores = [
        float(field["confidence"])
        for field in messy["fields"]
        if field.get("confidence") is not None
    ]
    assert clean_scores
    assert messy_scores
    clean_avg = sum(clean_scores) / len(clean_scores)
    messy_avg = sum(messy_scores) / len(messy_scores)
    assert clean_avg > messy_avg
    assert clean_avg != 0.9


def test_evidence_based_alias_specificity_changes_confidence() -> None:
    preferred = _confidence_from_evidence(
        field_name="invoice_number",
        alias="invoice number",
        value="INV-1",
    )
    weak = _confidence_from_evidence(
        field_name="invoice_number",
        alias="inv#",
        value="INV-MESSY-77??",
    )
    assert preferred > weak
    assert preferred != 0.9
    assert weak != 0.9
