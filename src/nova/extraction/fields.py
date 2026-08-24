"""Part 1 supported extraction field catalog.

Do not invent fields outside this set. Evaluation fixtures use the same names.
"""

from __future__ import annotations

PART1_FIELDS: frozenset[str] = frozenset(
    {
        "invoice_number",
        "bl_number",
        "shipper_name",
        "consignee_name",
        "vessel_name",
        "port_of_loading",
        "port_of_discharge",
        "cargo_description",
        "gross_weight",
        "issue_date",
    }
)

# Human-readable labels commonly found in synthetic fixtures.
FIELD_LABELS: dict[str, tuple[str, ...]] = {
    "invoice_number": ("Invoice Number", "Invoice No", "Invoice #"),
    "bl_number": ("B/L Number", "Bill of Lading Number", "BL Number"),
    "shipper_name": ("Shipper Name", "Shipper", "Exporter"),
    "consignee_name": ("Consignee Name", "Consignee"),
    "vessel_name": ("Vessel Name", "Vessel"),
    "port_of_loading": ("Port of Loading", "POL"),
    "port_of_discharge": ("Port of Discharge", "POD"),
    "cargo_description": ("Cargo Description", "Description of Goods", "Goods"),
    "gross_weight": ("Gross Weight", "Weight"),
    "issue_date": ("Issue Date", "Date of Issue", "Invoice Date"),
}


def is_supported_field(name: str) -> bool:
    return name in PART1_FIELDS


def assert_supported_fields(names: list[str]) -> None:
    unsupported = [name for name in names if not is_supported_field(name)]
    if unsupported:
        raise ValueError(f"Unsupported extraction fields: {', '.join(unsupported)}")
