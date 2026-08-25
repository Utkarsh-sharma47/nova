"""Default Part 1 customer rules and routing policy for the pipeline."""

from __future__ import annotations

from uuid import UUID, uuid4

from nova.contracts.routing import RoutingPolicySnapshot
from nova.contracts.validation import CustomerRuleSnapshot
from nova.extraction.fields import required_fields_for

DEFAULT_RULESET_ID = "part1-default-ruleset"
DEFAULT_RULESET_VERSION = "1.0.0"
DEFAULT_POLICY_ID = "part1-routing-policy"
DEFAULT_POLICY_VERSION = "1.0.0"


def default_rules_for_document_type(
    *,
    document_type: str,
    trace_id: UUID,
    customer_id: UUID | None = None,
) -> list[CustomerRuleSnapshot]:
    """Blocking presence rules for each required Part 1 field."""
    fields = required_fields_for(document_type)
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
