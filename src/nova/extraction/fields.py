"""Part 1 extraction field catalog (GoComet assignment + Nova extras).

Do not invent fields beyond this catalog. Callers may pass a subset via
`required_fields`; unknown field names are rejected.
"""

from __future__ import annotations

from typing import Final

# Exact GoComet assignment MUST fields (Deliverable 2A).
ASSIGNMENT_FIELDS: Final[tuple[str, ...]] = (
    "consignee_name",
    "hs_code",
    "port_of_loading",
    "port_of_discharge",
    "incoterms",
    "description_of_goods",
    "gross_weight",
    "invoice_number",
)

# Additional Nova Part 1 fields kept for operational demo richness.
_INVOICE_EXTRA: Final[tuple[str, ...]] = (
    "invoice_date",
    "seller_name",
    "buyer_name",
    "currency",
    "total_amount",
)

_BOL_EXTRA: Final[tuple[str, ...]] = (
    "bl_number",
    "vessel_name",
    "shipper_name",
    "container_number",
)


def _unique(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for group in groups:
        for name in group:
            seen.setdefault(name, None)
    return tuple(seen)


# Invoice extraction always includes the eight assignment fields.
INVOICE_FIELDS: Final[tuple[str, ...]] = _unique(ASSIGNMENT_FIELDS, _INVOICE_EXTRA)

# BoL extraction always includes the eight assignment fields (missing stay MISSING).
BILL_OF_LADING_FIELDS: Final[tuple[str, ...]] = _unique(ASSIGNMENT_FIELDS, _BOL_EXTRA)

PART1_FIELDS_BY_DOCUMENT_TYPE: Final[dict[str, tuple[str, ...]]] = {
    "INVOICE": INVOICE_FIELDS,
    "commercial_invoice": INVOICE_FIELDS,
    "BILL_OF_LADING": BILL_OF_LADING_FIELDS,
    "bill_of_lading": BILL_OF_LADING_FIELDS,
}

_ALL_KNOWN_FIELDS: Final[frozenset[str]] = frozenset(
    {*INVOICE_FIELDS, *BILL_OF_LADING_FIELDS}
)


def required_fields_for(document_type: str | None) -> list[str]:
    if document_type is None:
        return list(INVOICE_FIELDS)
    fields = PART1_FIELDS_BY_DOCUMENT_TYPE.get(document_type)
    if fields is None:
        return list(INVOICE_FIELDS)
    return list(fields)


def assert_supported_fields(field_names: list[str]) -> None:
    unknown = [name for name in field_names if name not in _ALL_KNOWN_FIELDS]
    if unknown:
        raise ValueError(f"unsupported extraction fields: {unknown}")


def is_supported_field(field_name: str) -> bool:
    return field_name in _ALL_KNOWN_FIELDS
