"""Customer expected-value rules and routing policy for the Part 1 pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

from nova.contracts.routing import RoutingPolicySnapshot
from nova.contracts.validation import CustomerRuleSnapshot
from nova.extraction.fields import required_fields_for

DEFAULT_RULESET_ID = "part1-default-ruleset"
DEFAULT_RULESET_VERSION = "1.0.0"
DEFAULT_POLICY_ID = "part1-routing-policy"
DEFAULT_POLICY_VERSION = "1.0.0"

# Stored on customers.metadata under this key.
CUSTOMER_EXPECTED_FIELDS_KEY = "expected_fields"

# Demo control-group expectations (aligned with fixtures/demo/synthetic_invoice_clean.txt).
# These are customer policy values — not rejection heuristics for a specific bad invoice.
DEMO_CONTROL_GROUP_EXPECTED_FIELDS: dict[str, str] = {
    "consignee_name": "Harbor Goods BV",
    "hs_code": "8471.30",
    "port_of_loading": "Singapore",
    "port_of_discharge": "Rotterdam",
    "incoterms": "FOB",
    "gross_weight": "10250 KG",
    "description_of_goods": "Synthetic clean invoice for Nova Part 1 evaluation.",
    "invoice_number": "INV-CLEAN-2001",
    "invoice_date": "2026-08-18",
    "seller_name": "Acme Logistics Pte Ltd",
    "buyer_name": "Harbor Goods BV",
    "currency": "USD",
    "total_amount": "15200.00",
}


def demo_control_group_expected_fields() -> dict[str, str]:
    """Return a copy of the Part 1 demo control-group expected field map."""
    return dict(DEMO_CONTROL_GROUP_EXPECTED_FIELDS)


def expected_fields_from_metadata(metadata: Mapping[str, Any] | None) -> dict[str, str]:
    """Extract normalized expected field values from customer metadata."""
    if not metadata:
        return {}
    raw = metadata.get(CUSTOMER_EXPECTED_FIELDS_KEY)
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in raw.items():
        if value is None:
            continue
        name = str(key).strip()
        text = str(value).strip()
        if name and text:
            out[name] = text
    return out


def customer_metadata_with_expected_fields(
    expected_fields: Mapping[str, str],
    *,
    base: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build customer metadata JSON including expected_fields."""
    metadata = dict(base or {})
    metadata[CUSTOMER_EXPECTED_FIELDS_KEY] = {
        str(k).strip(): str(v).strip()
        for k, v in expected_fields.items()
        if str(k).strip() and str(v).strip()
    }
    return metadata


def default_rules_for_document_type(
    *,
    document_type: str,
    trace_id: UUID,
    customer_id: UUID | None = None,
    expected_fields: Mapping[str, str] | None = None,
) -> list[CustomerRuleSnapshot]:
    """Build presence + value-equality rules for required Part 1 fields.

    - Every required field gets a blocking presence rule.
    - Fields with a customer expected value also get a blocking equals rule.
    - If no expected values are configured, a blocking fail-closed rule is added so
      AUTO_APPROVE cannot proceed on presence-only MATCH.
    """
    fields = required_fields_for(document_type)
    expected = {
        str(k).strip(): str(v).strip()
        for k, v in (expected_fields or {}).items()
        if str(k).strip() and str(v).strip()
    }
    rules: list[CustomerRuleSnapshot] = []

    for name in fields:
        rules.append(
            CustomerRuleSnapshot(
                trace_id=trace_id,
                customer_id=customer_id,
                rule_id=uuid4(),
                rule_code=f"required.{name}",
                version=DEFAULT_RULESET_VERSION,
                severity="BLOCKING",
                blocking=True,
                requires_judgment=False,
                expression={"op": "required", "field": name},
            )
        )
        if name in expected:
            rules.append(
                CustomerRuleSnapshot(
                    trace_id=trace_id,
                    customer_id=customer_id,
                    rule_id=uuid4(),
                    rule_code=f"equals.{name}",
                    version=DEFAULT_RULESET_VERSION,
                    severity="BLOCKING",
                    blocking=True,
                    requires_judgment=False,
                    expression={
                        "op": "equals",
                        "field": name,
                        "expected": expected[name],
                    },
                )
            )

    if not expected:
        # Fail closed: presence-only rules must not authorize AUTO_APPROVE.
        rules.append(
            CustomerRuleSnapshot(
                trace_id=trace_id,
                customer_id=customer_id,
                rule_id=uuid4(),
                rule_code="customer.expected_values_missing",
                version=DEFAULT_RULESET_VERSION,
                severity="BLOCKING",
                blocking=True,
                requires_judgment=False,
                expression={"op": "judgment", "field": "customer_expected_values"},
            )
        )

    return rules


def default_routing_policy(
    *,
    document_type: str,
    trace_id: UUID | None = None,
) -> RoutingPolicySnapshot:
    return RoutingPolicySnapshot(
        trace_id=trace_id or uuid4(),
        policy_id=DEFAULT_POLICY_ID,
        policy_version=DEFAULT_POLICY_VERSION,
        high_confidence_threshold=0.85,
        low_confidence_threshold=0.60,
        allow_auto_approve_on_unknown=False,
        critical_fields=required_fields_for(document_type),
        require_evidence_for_auto_approve=True,
        min_decision_confidence=0.85,
    )
