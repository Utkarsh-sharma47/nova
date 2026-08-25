"""Optional LLM assist for Router gray-zone ranking.

LLM suggestions are advisory. They may only choose between HUMAN_REVIEW and
AMENDMENT_REQUEST when AUTO_APPROVE is already forbidden. They can never
authorize AUTO_APPROVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from nova.contracts.common import ModelMetadata, UsageMetrics
from nova.contracts.routing import DecisionKind, RoutingRequest


@dataclass(frozen=True)
class LlmAssistSuggestion:
    suggested_decision: DecisionKind
    rationale: str | None = None
    model_metadata: ModelMetadata | None = None
    usage: UsageMetrics | None = None
    malformed: bool = False
    failed: bool = False
    error_message: str | None = None


class RouterLlmPort(Protocol):
    def suggest(self, request: RoutingRequest) -> LlmAssistSuggestion:
        """Return an advisory disposition suggestion."""


class NullRouterLlm:
    """Default: no LLM assist."""

    def suggest(self, request: RoutingRequest) -> LlmAssistSuggestion:
        _ = request
        return LlmAssistSuggestion(
            suggested_decision=DecisionKind.HUMAN_REVIEW,
            rationale=None,
        )


def sanitize_llm_suggestion(
    suggestion: LlmAssistSuggestion,
    *,
    auto_approve_eligible: bool,
) -> LlmAssistSuggestion:
    """Force fail-closed semantics on LLM output.

    AUTO_APPROVE from the LLM is stripped unless deterministic eligibility
    already holds — and even then the deterministic engine remains authoritative.
    """
    if suggestion.failed or suggestion.malformed:
        return suggestion
    if suggestion.suggested_decision == DecisionKind.AUTO_APPROVE:
        if not auto_approve_eligible:
            return LlmAssistSuggestion(
                suggested_decision=DecisionKind.HUMAN_REVIEW,
                rationale=suggestion.rationale,
                model_metadata=suggestion.model_metadata,
                usage=suggestion.usage,
                malformed=False,
                failed=False,
                error_message="LLM AUTO_APPROVE ignored; safety constraints forbid it",
            )
        # Eligible path: still do not let LLM be the authority — drop to no-op.
        return LlmAssistSuggestion(
            suggested_decision=DecisionKind.AUTO_APPROVE,
            rationale=suggestion.rationale,
            model_metadata=suggestion.model_metadata,
            usage=suggestion.usage,
        )
    if suggestion.suggested_decision not in {
        DecisionKind.HUMAN_REVIEW,
        DecisionKind.AMENDMENT_REQUEST,
        DecisionKind.AUTO_APPROVE,
    }:
        return LlmAssistSuggestion(
            suggested_decision=DecisionKind.HUMAN_REVIEW,
            rationale=suggestion.rationale,
            model_metadata=suggestion.model_metadata,
            usage=suggestion.usage,
            malformed=True,
            error_message="LLM returned illegal decision enum",
        )
    return suggestion
