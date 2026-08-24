"""Router / Decision Agent service.

Policy-first routing: deterministic safety constraints outrank any LLM suggestion.
AUTO_APPROVE is emitted only when no safety constraint fires.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from uuid import UUID

from nova.contracts.common import ModelMetadata, StageError, UsageMetrics
from nova.contracts.routing import (
    DecisionActorType,
    DecisionKind,
    DecisionResult,
    LlmRoutingSuggestion,
    RoutingRequest,
)
from nova.router.codes import (
    RC_ALL_BLOCKING_MATCH,
    RC_AMENDMENT_FROM_MISMATCH,
    RC_GRAY_ZONE_LLM_ASSIST,
    RC_HIGH_CONFIDENCE,
    RC_HUMAN_REVIEW_DEFAULT,
    RC_IDEMPOTENT_REPLAY,
    ROUTER_AGENT_VERSION,
    ROUTER_POLICY_ENGINE_VERSION,
    SC_FABRICATED_EVIDENCE,
    SC_LLM_FAILURE,
    SC_MALFORMED_OUTPUT,
    SC_PROMPT_INJECTION_IGNORED,
    SC_SYSTEM_FAILSAFE,
    SC_TIMEOUT,
    SC_UNSAFE_LLM_OVERRIDE,
)
from nova.router.constraints import SafetyAssessment, SafetyHit, evaluate_safety_constraints
from nova.router.llm import NullRouterLlm, RouterLlmPort, sanitize_llm_suggestion

logger = logging.getLogger("nova.router")



def _fingerprint(request: RoutingRequest) -> str:
    payload = {
        "document_id": str(request.document_id),
        "document_version_id": str(request.document_version_id),
        "shipment_id": str(request.shipment_id),
        "verification_run_id": str(request.verification_run_id),
        "validation_result_id": str(request.validation_result_id),
        "policy_id": request.policy.policy_id,
        "policy_version": request.policy.policy_version,
        "extraction_status": request.extraction.status.value,
        "validation_status": request.validation.status.value,
        "checks": [
            {
                "check_id": c.check_id,
                "rule_id": str(c.rule_id),
                "outcome": c.outcome.value,
                "blocking": c.blocking,
            }
            for c in request.validation.checks
        ],
        "fields": [
            {
                "name": f.field_name,
                "presence": f.presence.value,
                "confidence": f.confidence,
                "uncertainty": f.uncertainty.value,
                "value": f.value,
            }
            for f in request.extraction.fields
        ],
        "blocking_uncertainty_present": request.blocking_uncertainty_present,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _ids_to_str(ids: list[UUID]) -> list[str]:
    return [str(i) for i in ids]


class RouterService:
    """Deterministic Router with optional advisory LLM assist."""

    def __init__(
        self,
        *,
        llm: RouterLlmPort | None = None,
        decision_cache: dict[str, DecisionKind] | None = None,
    ) -> None:
        self._llm: RouterLlmPort = llm or NullRouterLlm()
        self._decision_cache: dict[str, DecisionKind] = (
            decision_cache if decision_cache is not None else {}
        )

    def decide(
        self,
        request: RoutingRequest,
        *,
        timed_out: bool = False,
        force_failsafe: bool = False,
        engine_error: str | None = None,
    ) -> DecisionResult:
        started = time.perf_counter()
        fingerprint = _fingerprint(request)
        logger.info(
            "decision start",
            extra={
                "event": "decision.start",
                "extra_fields": {
                    "stage": "router",
                    "run_id": str(request.run_id or request.verification_run_id),
                    "trace_id": str(request.trace_id),
                },
            },
        )
        errors: list[StageError] = []
        safety_codes: list[str] = []
        reasons: list[str] = []
        reason_codes: list[str] = []
        triggering: list[str] = []
        evidence_refs: list[str] = []
        llm_rationale: str | None = None
        llm_overridden = False
        unsafe_llm_attempt = False
        actor = DecisionActorType.ROUTER
        model_metadata = None
        usage: UsageMetrics | None = None

        if request.correlation and request.correlation.get("prompt_injection_detected"):
            safety_codes.append(SC_PROMPT_INJECTION_IGNORED)
            reasons.append("Prompt-injection-like content ignored for disposition")

        if force_failsafe or engine_error:
            return self._fail_closed(
                request=request,
                fingerprint=fingerprint,
                started=started,
                code=SC_SYSTEM_FAILSAFE,
                message=engine_error or "System failsafe activated",
                safety_codes=safety_codes,
                reasons=reasons,
                reason_codes=reason_codes,
                retryable=False,
            )

        if timed_out:
            return self._fail_closed(
                request=request,
                fingerprint=fingerprint,
                started=started,
                code=SC_TIMEOUT,
                message="Router timeout exceeded",
                safety_codes=safety_codes,
                reasons=reasons,
                reason_codes=reason_codes,
                retryable=True,
            )

        assessment = evaluate_safety_constraints(
            extraction=request.extraction,
            validation=request.validation,
            policy=request.policy,
            blocking_uncertainty_present=request.blocking_uncertainty_present,
        )
        safety_codes.extend(assessment.codes)
        reasons.extend(assessment.reasons)
        triggering.extend(_ids_to_str(assessment.triggering_check_ids))

        embedded = request.llm_suggestion
        if embedded is not None:
            applied = self._apply_embedded_suggestion(embedded, assessment)
            assessment = applied.assessment
            safety_codes.extend(applied.safety_codes)
            reasons.extend(applied.reasons)
            reason_codes.extend(applied.reason_codes)
            errors.extend(applied.errors)
            llm_rationale = applied.llm_rationale
            llm_overridden = applied.llm_overridden
            unsafe_llm_attempt = applied.unsafe_llm_attempt

        auto_eligible = not assessment.blocks_auto_approve

        if embedded is None and not isinstance(self._llm, NullRouterLlm):
            suggestion = self._llm.suggest(request)
            model_metadata = suggestion.model_metadata
            usage = suggestion.usage
            if suggestion.failed:
                safety_codes.append(SC_LLM_FAILURE)
                reasons.append(suggestion.error_message or "LLM assist unavailable")
                reason_codes.append(SC_LLM_FAILURE)
                assessment.hits.append(
                    SafetyHit(
                        code=SC_LLM_FAILURE,
                        reason=suggestion.error_message or "LLM assist unavailable",
                        preferred_decision=DecisionKind.HUMAN_REVIEW,
                    )
                )
                auto_eligible = False
            elif suggestion.malformed:
                safety_codes.append(SC_MALFORMED_OUTPUT)
                reasons.append(suggestion.error_message or "Malformed LLM decision")
                reason_codes.append(SC_MALFORMED_OUTPUT)
                assessment.hits.append(
                    SafetyHit(
                        code=SC_MALFORMED_OUTPUT,
                        reason=suggestion.error_message or "Malformed LLM decision",
                        preferred_decision=DecisionKind.HUMAN_REVIEW,
                    )
                )
                auto_eligible = False
            else:
                if (
                    suggestion.suggested_decision == DecisionKind.AUTO_APPROVE
                    and not auto_eligible
                ):
                    unsafe_llm_attempt = True
                    llm_overridden = True
                    safety_codes.append(SC_UNSAFE_LLM_OVERRIDE)
                    reason_codes.append(SC_UNSAFE_LLM_OVERRIDE)
                    reasons.append("LLM AUTO_APPROVE rejected by safety constraints")
                sanitized = sanitize_llm_suggestion(
                    suggestion, auto_approve_eligible=auto_eligible
                )
                llm_rationale = sanitized.rationale
                if (
                    not auto_eligible
                    and sanitized.suggested_decision
                    in {DecisionKind.HUMAN_REVIEW, DecisionKind.AMENDMENT_REQUEST}
                    and not sanitized.failed
                    and not sanitized.malformed
                ):
                    reason_codes.append(RC_GRAY_ZONE_LLM_ASSIST)

        if fingerprint in self._decision_cache:
            reason_codes.append(RC_IDEMPOTENT_REPLAY)
            reasons.append("Repeated identical input fingerprint; deterministic replay")

        decision = self._resolve_decision(
            assessment=assessment,
            auto_eligible=auto_eligible,
            embedded=embedded,
            reason_codes=reason_codes,
        )

        if decision == DecisionKind.AUTO_APPROVE and assessment.blocks_auto_approve:
            decision = assessment.preferred_decision()
            llm_overridden = True
            unsafe_llm_attempt = True
            if SC_UNSAFE_LLM_OVERRIDE not in safety_codes:
                safety_codes.append(SC_UNSAFE_LLM_OVERRIDE)
            reasons.append("Final safety gate blocked AUTO_APPROVE")

        if decision == DecisionKind.AUTO_APPROVE:
            reason_codes.extend([RC_ALL_BLOCKING_MATCH, RC_HIGH_CONFIDENCE])
            reasons.append("All blocking checks MATCH with sufficient confidence")
            for field in request.extraction.fields:
                for ev in field.evidence:
                    if ev.evidence_id:
                        evidence_refs.append(ev.evidence_id)
                    elif ev.snippet:
                        evidence_refs.append(ev.snippet[:64])
            if request.policy.require_evidence_for_auto_approve and not evidence_refs:
                decision = DecisionKind.HUMAN_REVIEW
                safety_codes.append("SC_MISSING_EVIDENCE")
                reasons.append("AUTO_APPROVE blocked: no evidence refs")

        confidence = self._decision_confidence(request, decision, auto_eligible)
        self._decision_cache[fingerprint] = decision

        return self._build(
            request=request,
            decision=decision,
            reasons=reasons,
            reason_codes=list(dict.fromkeys(reason_codes)),
            triggering=list(dict.fromkeys(triggering)),
            evidence_refs=list(dict.fromkeys(evidence_refs)),
            safety_codes=list(dict.fromkeys(safety_codes)),
            actor=actor,
            fingerprint=fingerprint,
            llm_rationale=llm_rationale,
            llm_overridden=llm_overridden,
            unsafe_llm_attempt=unsafe_llm_attempt,
            model_metadata=model_metadata,
            usage=usage,
            errors=errors,
            confidence=confidence,
            started=started,
        )

    def _fail_closed(
        self,
        *,
        request: RoutingRequest,
        fingerprint: str,
        started: float,
        code: str,
        message: str,
        safety_codes: list[str],
        reasons: list[str],
        reason_codes: list[str],
        retryable: bool,
    ) -> DecisionResult:
        safety_codes = [*safety_codes, code]
        reason_codes = [*reason_codes, code]
        reasons = [*reasons, message]
        return self._build(
            request=request,
            decision=DecisionKind.HUMAN_REVIEW,
            reasons=reasons,
            reason_codes=reason_codes,
            triggering=[],
            evidence_refs=[],
            safety_codes=safety_codes,
            actor=DecisionActorType.SYSTEM_FAILSAFE,
            fingerprint=fingerprint,
            llm_rationale=None,
            llm_overridden=False,
            unsafe_llm_attempt=False,
            model_metadata=None,
            usage=None,
            errors=[StageError(code=code, message=message, retryable=retryable)],
            confidence=None,
            started=started,
        )

    class _EmbeddedApply:
        __slots__ = (
            "assessment",
            "safety_codes",
            "reasons",
            "reason_codes",
            "errors",
            "llm_rationale",
            "llm_overridden",
            "unsafe_llm_attempt",
        )

        def __init__(
            self,
            assessment: SafetyAssessment,
            safety_codes: list[str],
            reasons: list[str],
            reason_codes: list[str],
            errors: list[StageError],
            llm_rationale: str | None,
            llm_overridden: bool,
            unsafe_llm_attempt: bool,
        ) -> None:
            self.assessment = assessment
            self.safety_codes = safety_codes
            self.reasons = reasons
            self.reason_codes = reason_codes
            self.errors = errors
            self.llm_rationale = llm_rationale
            self.llm_overridden = llm_overridden
            self.unsafe_llm_attempt = unsafe_llm_attempt

    def _apply_embedded_suggestion(
        self,
        embedded: LlmRoutingSuggestion,
        assessment: SafetyAssessment,
    ) -> RouterService._EmbeddedApply:
        safety_codes: list[str] = []
        reasons: list[str] = []
        reason_codes: list[str] = []
        errors: list[StageError] = []
        llm_rationale = embedded.rationale
        llm_overridden = False
        unsafe_llm_attempt = False

        if not embedded.available:
            safety_codes.append(SC_LLM_FAILURE)
            reason_codes.append(SC_LLM_FAILURE)
            reasons.append("LLM unavailable for routing assist")
            assessment.hits.append(
                SafetyHit(
                    code=SC_LLM_FAILURE,
                    reason="LLM unavailable",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                )
            )
            return self._EmbeddedApply(
                assessment,
                safety_codes,
                reasons,
                reason_codes,
                errors,
                llm_rationale,
                llm_overridden,
                unsafe_llm_attempt,
            )

        if embedded.malformed or (
            embedded.decision is None and embedded.raw_payload is not None
        ):
            safety_codes.append(SC_MALFORMED_OUTPUT)
            reason_codes.append(SC_MALFORMED_OUTPUT)
            reasons.append("Malformed LLM decision payload")
            assessment.hits.append(
                SafetyHit(
                    code=SC_MALFORMED_OUTPUT,
                    reason="Malformed LLM decision",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                )
            )
            errors.append(
                StageError(
                    code=SC_MALFORMED_OUTPUT,
                    message="Malformed LLM decision payload",
                    retryable=True,
                )
            )
            return self._EmbeddedApply(
                assessment,
                safety_codes,
                reasons,
                reason_codes,
                errors,
                llm_rationale,
                llm_overridden,
                unsafe_llm_attempt,
            )

        if embedded.fabricated_evidence:
            safety_codes.append(SC_FABRICATED_EVIDENCE)
            reason_codes.append(SC_FABRICATED_EVIDENCE)
            reasons.append("LLM provided fabricated evidence references")
            assessment.hits.append(
                SafetyHit(
                    code=SC_FABRICATED_EVIDENCE,
                    reason="Fabricated evidence",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                )
            )
            unsafe_llm_attempt = True
            llm_overridden = True

        if embedded.decision == DecisionKind.AUTO_APPROVE and assessment.blocks_auto_approve:
            unsafe_llm_attempt = True
            llm_overridden = True
            safety_codes.append(SC_UNSAFE_LLM_OVERRIDE)
            reason_codes.append(SC_UNSAFE_LLM_OVERRIDE)
            reasons.append("LLM AUTO_APPROVE rejected by safety constraints")

        if (
            embedded.decision == DecisionKind.AUTO_APPROVE
            and not embedded.triggering_check_ids
            and not assessment.blocks_auto_approve
        ):
            # Eligible path still requires evidence/triggering checks for approve.
            unsafe_llm_attempt = True
            llm_overridden = True
            safety_codes.append(SC_UNSAFE_LLM_OVERRIDE)
            reasons.append("LLM AUTO_APPROVE without triggering_check_ids rejected")
            assessment.hits.append(
                SafetyHit(
                    code=SC_UNSAFE_LLM_OVERRIDE,
                    reason="AUTO_APPROVE without triggering checks",
                    preferred_decision=DecisionKind.HUMAN_REVIEW,
                )
            )

        return self._EmbeddedApply(
            assessment,
            safety_codes,
            reasons,
            reason_codes,
            errors,
            llm_rationale,
            llm_overridden,
            unsafe_llm_attempt,
        )

    def _resolve_decision(
        self,
        *,
        assessment: SafetyAssessment,
        auto_eligible: bool,
        embedded: LlmRoutingSuggestion | None,
        reason_codes: list[str],
    ) -> DecisionKind:
        if auto_eligible:
            return DecisionKind.AUTO_APPROVE

        preferred = assessment.preferred_decision()

        if (
            embedded is not None
            and embedded.available
            and not embedded.malformed
            and embedded.decision
            in {DecisionKind.HUMAN_REVIEW, DecisionKind.AMENDMENT_REQUEST}
        ):
            if (
                embedded.decision == DecisionKind.AMENDMENT_REQUEST
                and preferred == DecisionKind.AMENDMENT_REQUEST
            ):
                reason_codes.append(RC_AMENDMENT_FROM_MISMATCH)
                return DecisionKind.AMENDMENT_REQUEST
            if embedded.decision == DecisionKind.HUMAN_REVIEW:
                reason_codes.append(RC_HUMAN_REVIEW_DEFAULT)
                return DecisionKind.HUMAN_REVIEW

        if preferred == DecisionKind.AMENDMENT_REQUEST:
            reason_codes.append(RC_AMENDMENT_FROM_MISMATCH)
            return DecisionKind.AMENDMENT_REQUEST

        reason_codes.append(RC_HUMAN_REVIEW_DEFAULT)
        return DecisionKind.HUMAN_REVIEW

    def _decision_confidence(
        self,
        request: RoutingRequest,
        decision: DecisionKind,
        auto_eligible: bool,
    ) -> float | None:
        if decision == DecisionKind.AUTO_APPROVE and auto_eligible:
            confs = [f.confidence for f in request.extraction.fields if f.confidence is not None]
            if not confs:
                return request.policy.min_decision_confidence
            return min(confs)
        return None

    def _build(
        self,
        *,
        request: RoutingRequest,
        decision: DecisionKind,
        reasons: list[str],
        reason_codes: list[str],
        triggering: list[str],
        evidence_refs: list[str],
        safety_codes: list[str],
        actor: DecisionActorType,
        fingerprint: str,
        llm_rationale: str | None,
        llm_overridden: bool,
        unsafe_llm_attempt: bool,
        model_metadata: ModelMetadata | None,
        usage: UsageMetrics | None,
        errors: list[StageError],
        confidence: float | None,
        started: float,
    ) -> DecisionResult:
        latency_ms = int((time.perf_counter() - started) * 1000)
        if usage is None:
            usage = UsageMetrics(latency_ms=latency_ms)
        elif usage.latency_ms is None:
            usage = usage.model_copy(update={"latency_ms": latency_ms})

        safety_for_result = [] if decision == DecisionKind.AUTO_APPROVE else safety_codes

        result = DecisionResult(
            trace_id=request.trace_id,
            run_id=request.run_id,
            document_id=request.document_id,
            document_version_id=request.document_version_id,
            shipment_id=request.shipment_id,
            verification_run_id=request.verification_run_id,
            validation_result_id=request.validation_result_id,
            decision=decision,
            reasons=reasons,
            reason_codes=reason_codes,
            triggering_check_ids=triggering,
            evidence_refs=evidence_refs,
            policy_id=request.policy.policy_id,
            policy_version=request.policy.policy_version,
            routing_rule_version=ROUTER_POLICY_ENGINE_VERSION,
            agent_version=ROUTER_AGENT_VERSION,
            confidence=confidence,
            safety_constraints_applied=safety_for_result,
            requires_human_attention=decision != DecisionKind.AUTO_APPROVE,
            actor_type=actor,
            input_fingerprint=fingerprint,
            model_metadata=model_metadata,
            usage=usage,
            llm_rationale=llm_rationale,
            llm_overridden=llm_overridden,
            unsafe_llm_attempt=unsafe_llm_attempt,
            completed_at=datetime.now(UTC),
            errors=errors,
        )
        logger.info(
            "decision completion",
            extra={
                "event": "decision.complete",
                "extra_fields": {
                    "stage": "router",
                    "run_id": str(result.run_id or result.verification_run_id),
                    "trace_id": str(result.trace_id),
                    "decision": result.decision.value,
                    "reason_code": result.reason_codes[0] if result.reason_codes else None,
                    "duration_ms": latency_ms,
                    "actor_type": result.actor_type.value,
                },
            },
        )
        return result
