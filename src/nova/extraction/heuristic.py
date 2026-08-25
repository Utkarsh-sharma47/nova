"""Heuristic MockLLM factory for local/CI without API keys.

Parses simple ``Field: value`` lines from the document text embedded in the
prompt user message. Never invents values absent from the text.
"""

from __future__ import annotations

import json
import re
from typing import Any

from nova.extraction.fields import is_supported_field
from nova.llm.port import LLMRequest

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "invoice_number": ("invoice number", "invoice #", "invoice no", "inv no"),
    "invoice_date": ("invoice date", "date"),
    "seller_name": ("seller", "seller name", "from"),
    "buyer_name": ("buyer", "buyer name", "bill to"),
    "currency": ("currency", "ccy"),
    "total_amount": ("total amount", "total", "amount due"),
    "bl_number": ("bl number", "b/l number", "bill of lading", "bol"),
    "vessel_name": ("vessel", "vessel name", "ship"),
    "shipper_name": ("shipper", "shipper name"),
    "consignee_name": ("consignee", "consignee name"),
    "port_of_loading": ("port of loading", "pol", "load port"),
    "port_of_discharge": ("port of discharge", "pod", "discharge port"),
    "container_number": ("container", "container number", "container no"),
}


def heuristic_extractor_response(request: LLMRequest) -> dict[str, Any]:
    user = next((msg.content for msg in request.messages if msg.role == "user"), "")
    required = _extract_required_fields(user)
    document_text = _extract_document_text(user)
    fields: list[dict[str, Any]] = []
    for name in required:
        if not is_supported_field(name):
            continue
        match = _find_value(name, document_text)
        if match is None:
            fields.append(
                {
                    "field_name": name,
                    "value": None,
                    "value_type": "string",
                    "presence": "MISSING",
                    "confidence": None,
                    "uncertainty": "NONE",
                    "evidence": [],
                    "warnings": [],
                }
            )
            continue
        value, snippet = match
        fields.append(
            {
                "field_name": name,
                "value": value,
                "value_type": "string",
                "presence": "KNOWN",
                "confidence": 0.9,
                "uncertainty": "NONE",
                "evidence": [
                    {
                        "evidence_id": f"h-{name}",
                        "source_type": "DOCUMENT_SPAN",
                        "snippet": snippet,
                        "page": 1,
                    }
                ],
                "warnings": [],
            }
        )
    return {"fields": fields}


def _extract_required_fields(user: str) -> list[str]:
    payload = _extract_user_payload(user)
    if payload is None:
        return []
    fields = payload.get("required_fields")
    if not isinstance(fields, list):
        return []
    return [str(item) for item in fields]


def _extract_document_text(user: str) -> str:
    payload = _extract_user_payload(user)
    if payload is None:
        return ""
    document = payload.get("document") or {}
    text = document.get("text")
    return text if isinstance(text, str) else ""


def _extract_user_payload(user: str) -> dict[str, Any] | None:
    """Locate the document JSON object (not the inline schema example braces)."""
    marker = user.find('"document_type_hint"')
    if marker < 0:
        marker = user.find('"required_fields"')
    if marker < 0:
        return None
    start = user.rfind("{", 0, marker)
    if start < 0:
        return None
    try:
        payload = json.loads(user[start:])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _find_value(field_name: str, text: str) -> tuple[str, str] | None:
    aliases = _FIELD_ALIASES.get(field_name, (field_name.replace("_", " "),))
    for alias in aliases:
        pattern = re.compile(
            rf"(?im)^\s*{re.escape(alias)}\s*[:\-]\s*(.+?)\s*$",
        )
        found = pattern.search(text)
        if found:
            value = found.group(1).strip()
            if value:
                snippet = found.group(0).strip()
                return value, snippet
    return None
