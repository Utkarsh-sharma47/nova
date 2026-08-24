"""Validator Agent — deterministic rules + bounded optional LLM judgment."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError

from nova.agents.validator.deterministic import ENGINE_VERSION, evaluate_deterministic_rule
from nova.contracts.common import ModelMetadata, StageError, UsageMetrics
from nova.contracts.validation import (
    CustomerRuleSnapshot,
    ValidationCheck,
    ValidationOutcome,
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
)
from nova.llm.errors import (
    LLMError,
    LLMMalformedOutputError,
    LLMProviderError,
    LLMTimeoutError,
    RetryExhaustedError,
)
from nova.llm.port import LLMMessage, LLMPort, LLMRequest
from nova.validation_store import ValidationStorePort

logger = logging.getLogger(__name__)

VALIDATOR_VERSION = "0.1.0"
PROMPT_VERSION = "validator.judgment.v1"
MAX_LLM_RETRIES = 2


class ValidatorAgent:
    """Evaluate extracted fields against customer rules.

    Safety invariants:
    1. Deterministic MISMATCH/MATCH cannot be overridden by LLM.
    2. Missing/uncertain evidence cannot become verified MATCH via LLM.
    3. LLM failure → UNCERTAIN (never silent MATCH).
    4. No routing decisions (AUTO_APPROVE / etc.).
    5. Persistence is append-only; DB failure is recorded, not converted to MATCH.
    """

    def __init__(
        self,
        *,
        llm: LLMPort | None = None,
        store: ValidationStorePort | None = None,
        max_llm_retries: int = MAX_LLM_RETRIES,
        persist: bool = True,
    ) -> None:
        self._llm = llm
        self._store = store
        self._max_llm_retries = max_llm_retries
        self._persist = persist

    def validate(self, request: ValidationRequest) -> ValidationResult:
        started = time.perf_counter()
        execution_id = uuid4()

        if request.extraction_status and request.extraction_status.upper() == "FAILED":
            return self._finalize(
                self._failed_result(
                    request,
                    execution_id=execution_id,
                    error_code="INVALID_EXTRACTION",
                    error_message="Cannot validate FAILED extraction",
                    errors=[
                        StageError(
                            code="INVALID_EXTRACTION",
                            message="extraction_status=FAILED",
                            retryable=False,
                        )
                    ],
                ),
                started=started,
            )

        fields_snapshot = [f.model_copy(deep=True) for f in request.extracted_fields]
        checks: list[ValidationCheck] = []
        model_meta: ModelMetadata | None = None
        usage = UsageMetrics(attempt=1)

        try:
            for rule in request.rules:
                if rule.requires_judgment:
                    check, meta, u = self._judgment_check(request, rule, fields_snapshot)
                    checks.append(check)
                    if meta is not None:
                        model_meta = meta
                    if u is not None:
                        usage = self._merge_usage(usage, u)
                else:
                    checks.append(
                        evaluate_deterministic_rule(
                            rule,
                            fields_snapshot,
                            trace_id=request.trace_id,
                            run_id=request.run_id,
                        )
                    )
        except Exception as exc:  # noqa: BLE001
            logger.exception("validator_engine_error")
            return self._finalize(
                self._failed_result(
                    request,
                    execution_id=execution_id,
                    error_code="ENGINE_ERROR",
                    error_message=type(exc).__name__,
                    errors=[
                        StageError(
                            code="ENGINE_ERROR",
                            message="Validator engine error",
                            retryable=False,
                        )
                    ],
                    checks=checks,
                    model_metadata=model_meta,
                ),
                started=started,
            )

        result = ValidationResult(
            contract_version=request.contract_version,
            run_id=request.run_id,
            trace_id=request.trace_id,
            request_id=request.request_id,
            agent_execution_id=execution_id,
            document_id=request.document_id,
            document_version_id=request.document_version_id,
            shipment_id=request.shipment_id,
            customer_id=request.customer_id,
            extraction_result_id=request.extraction_result_id,
            status=ValidationStatus.COMPLETED,
            ruleset_id=request.ruleset_id,
            ruleset_version=request.ruleset_version,
            checks=checks,
            match_count=sum(1 for c in checks if c.outcome is ValidationOutcome.MATCH),
            mismatch_count=sum(1 for c in checks if c.outcome is ValidationOutcome.MISMATCH),
            uncertain_count=sum(1 for c in checks if c.outcome is ValidationOutcome.UNCERTAIN),
            engine_version=ENGINE_VERSION,
            model_metadata=model_meta,
            usage=usage,
            created_at=datetime.now(UTC),
        )
        return self._finalize(result, started=started)

    def _judgment_check(
        self,
        request: ValidationRequest,
        rule: CustomerRuleSnapshot,
        fields: list[Any],
    ) -> tuple[ValidationCheck, ModelMetadata | None, UsageMetrics | None]:
        expr = rule.expression or {}
        baseline = evaluate_deterministic_rule(
            rule.model_copy(update={"requires_judgment": False}),
            fields,
            trace_id=request.trace_id,
            run_id=request.run_id,
        )
        if baseline.outcome is ValidationOutcome.MISMATCH:
            return (
                baseline.model_copy(
                    update={
                        "details": {
                            **(baseline.details or {}),
                            "llm_override_blocked": True,
                            "safety": "DETERMINISTIC_MISMATCH_LOCKED",
                        }
                    }
                ),
                None,
                None,
            )
        if baseline.outcome is ValidationOutcome.MATCH and expr.get("op") not in {
            None,
            "",
            "judgment",
            "custom",
        }:
            # Crisp MATCH already resolved — do not let LLM flip it.
            return baseline, None, None

        if self._llm is None:
            return (
                ValidationCheck(
                    trace_id=request.trace_id,
                    run_id=request.run_id,
                    rule_id=rule.rule_id,
                    rule_code=rule.rule_code,
                    field_name=expr.get("field") if isinstance(expr.get("field"), str) else None,
                    outcome=ValidationOutcome.UNCERTAIN,
                    reason="LLM_UNAVAILABLE",
                    deterministic=False,
                    severity=rule.severity,
                    details={"validation_code": "LLM_UNAVAILABLE"},
                ),
                None,
                None,
            )

        total_usage = UsageMetrics(attempt=1, input_tokens=0, output_tokens=0, latency_ms=0)
        meta: ModelMetadata | None = None
        last_error: str | None = None

        for attempt in range(1, self._max_llm_retries + 2):
            try:
                response = self._llm.complete(
                    LLMRequest(
                        messages=[
                            LLMMessage(
                                role="system",
                                content=(
                                    "Return JSON only: "
                                    '{"outcome":"MATCH|MISMATCH|UNCERTAIN",'
                                    '"reason":"...","confidence":0-1}. '
                                    "Never invent evidence. Prefer UNCERTAIN when unsure."
                                ),
                            ),
                            LLMMessage(
                                role="user",
                                content=json.dumps(
                                    {
                                        "rule_code": rule.rule_code,
                                        "expression": rule.expression,
                                        "fields": [
                                            {
                                                "field_name": f.field_name,
                                                "value": f.value,
                                                "presence": f.presence.value,
                                                "confidence": f.confidence,
                                            }
                                            for f in fields
                                        ],
                                    },
                                    default=str,
                                ),
                            ),
                        ],
                        response_format="json",
                        timeout_ms=min(request.timeout_ms, 30_000),
                        metadata={"prompt_version": PROMPT_VERSION, "attempt": attempt},
                    )
                )
                total_usage = UsageMetrics(
                    attempt=attempt,
                    input_tokens=(total_usage.input_tokens or 0) + (response.input_tokens or 0),
                    output_tokens=(total_usage.output_tokens or 0) + (response.output_tokens or 0),
                    latency_ms=(total_usage.latency_ms or 0) + (response.latency_ms or 0),
                )
                meta = ModelMetadata(
                    provider=response.provider,
                    model=response.model,
                    prompt_id="validator.judgment",
                    prompt_version=PROMPT_VERSION,
                    agent_version=VALIDATOR_VERSION,
                    temperature=0.0,
                    invoked_at=datetime.now(UTC),
                )
                proposal = self._parse_judgment(response.content)
                outcome = ValidationOutcome(proposal["outcome"])
                reason = str(proposal.get("reason") or "LLM_JUDGMENT")
                confidence = proposal.get("confidence")

                if (
                    baseline.outcome is ValidationOutcome.UNCERTAIN
                    and outcome is ValidationOutcome.MATCH
                ):
                    outcome = ValidationOutcome.UNCERTAIN
                    reason = "LLM_MATCH_BLOCKED_ON_UNCERTAIN_BASELINE"
                if outcome is ValidationOutcome.MATCH and baseline.reason in {
                    "MISSING_EVIDENCE",
                    "FIELD_MISSING",
                    "FIELD_UNKNOWN",
                    "FIELD_AMBIGUOUS",
                    "CONFLICTING_EVIDENCE",
                    "LOW_CONFIDENCE",
                }:
                    outcome = ValidationOutcome.UNCERTAIN
                    reason = f"LLM_MATCH_BLOCKED_{baseline.reason}"

                # Reject invented evidence claims
                notes = str(proposal.get("evidence_notes") or "")
                if "invented_evidence" in notes.casefold():
                    outcome = ValidationOutcome.UNCERTAIN
                    reason = "LLM_INVENTED_EVIDENCE_REJECTED"

                return (
                    ValidationCheck(
                        trace_id=request.trace_id,
                        run_id=request.run_id,
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        field_name=(
                            expr.get("field") if isinstance(expr.get("field"), str) else None
                        ),
                        outcome=outcome,
                        reason=reason,
                        confidence=confidence if isinstance(confidence, int | float) else None,
                        deterministic=False,
                        severity=rule.severity,
                        evidence=list(baseline.evidence),
                        details={
                            "validation_code": reason,
                            "llm_raw_outcome": proposal.get("outcome"),
                            "attempt": attempt,
                        },
                    ),
                    meta,
                    total_usage,
                )
            except (LLMTimeoutError, LLMProviderError, LLMMalformedOutputError, LLMError) as exc:
                last_error = getattr(exc, "code", type(exc).__name__)
                if attempt > self._max_llm_retries or not getattr(exc, "retryable", False):
                    break
            except (ValidationError, ValueError, KeyError, json.JSONDecodeError, TypeError):
                last_error = "LLM_MALFORMED_OUTPUT"
                if attempt > self._max_llm_retries:
                    break

        return (
            ValidationCheck(
                trace_id=request.trace_id,
                run_id=request.run_id,
                rule_id=rule.rule_id,
                rule_code=rule.rule_code,
                field_name=expr.get("field") if isinstance(expr.get("field"), str) else None,
                outcome=ValidationOutcome.UNCERTAIN,
                reason="LLM_FAILURE",
                deterministic=False,
                severity=rule.severity,
                details={
                    "validation_code": last_error or RetryExhaustedError.code,
                    "retries": self._max_llm_retries,
                },
            ),
            meta,
            total_usage,
        )

    def _parse_judgment(self, content: Any) -> dict[str, Any]:
        if isinstance(content, dict):
            data = content
        else:
            try:
                data = json.loads(str(content))
            except json.JSONDecodeError as exc:
                raise LLMMalformedOutputError("non-JSON judgment") from exc
        if not isinstance(data, dict):
            raise LLMMalformedOutputError("judgment not an object")
        if any(k in data for k in ("decision", "AUTO_APPROVE", "routing")):
            raise LLMMalformedOutputError("LLM attempted routing decision")
        outcome = data.get("outcome")
        if outcome not in {o.value for o in ValidationOutcome}:
            raise LLMMalformedOutputError(f"illegal outcome: {outcome!r}")
        return data

    def _failed_result(
        self,
        request: ValidationRequest,
        *,
        execution_id: UUID,
        error_code: str,
        error_message: str,
        errors: list[StageError],
        checks: list[ValidationCheck] | None = None,
        model_metadata: ModelMetadata | None = None,
    ) -> ValidationResult:
        checks = checks or []
        return ValidationResult(
            contract_version=request.contract_version,
            run_id=request.run_id,
            trace_id=request.trace_id,
            request_id=request.request_id,
            agent_execution_id=execution_id,
            document_id=request.document_id,
            document_version_id=request.document_version_id,
            shipment_id=request.shipment_id,
            customer_id=request.customer_id,
            extraction_result_id=request.extraction_result_id,
            status=ValidationStatus.FAILED,
            ruleset_id=request.ruleset_id,
            ruleset_version=request.ruleset_version,
            checks=checks,
            match_count=sum(1 for c in checks if c.outcome is ValidationOutcome.MATCH),
            mismatch_count=sum(1 for c in checks if c.outcome is ValidationOutcome.MISMATCH),
            uncertain_count=sum(1 for c in checks if c.outcome is ValidationOutcome.UNCERTAIN),
            engine_version=ENGINE_VERSION,
            errors=errors,
            model_metadata=model_metadata,
            error_code=error_code,
            error_message=error_message,
            created_at=datetime.now(UTC),
        )

    def _finalize(self, result: ValidationResult, *, started: float) -> ValidationResult:
        latency_ms = int((time.perf_counter() - started) * 1000)
        if result.usage is None:
            result = result.model_copy(update={"usage": UsageMetrics(latency_ms=latency_ms)})
        else:
            result = result.model_copy(
                update={
                    "usage": result.usage.model_copy(
                        update={"latency_ms": result.usage.latency_ms or latency_ms}
                    )
                }
            )

        logger.info(
            "validator_completed",
            extra={
                "extra_fields": {
                    "event": "validator_completed",
                    "stage": "validator",
                    "status": result.status.value,
                    "match_count": result.match_count,
                    "mismatch_count": result.mismatch_count,
                    "uncertain_count": result.uncertain_count,
                    "duration_ms": result.usage.latency_ms if result.usage else latency_ms,
                    "error_code": result.error_code,
                }
            },
        )

        if self._persist and self._store is not None:
            try:
                self._store.append(result, validator_version=VALIDATOR_VERSION)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "validator_persist_failed",
                    extra={
                        "extra_fields": {
                            "event": "validator_persist_failed",
                            "error_type": type(exc).__name__,
                        }
                    },
                )
                return result.model_copy(
                    update={
                        "status": ValidationStatus.FAILED,
                        "error_code": "DATABASE_FAILURE",
                        "error_message": "Failed to persist validation result",
                        "errors": list(result.errors)
                        + [
                            StageError(
                                code="DATABASE_FAILURE",
                                message="Failed to persist validation result",
                                retryable=True,
                            )
                        ],
                    }
                )
        return result

    @staticmethod
    def _merge_usage(a: UsageMetrics, b: UsageMetrics) -> UsageMetrics:
        return UsageMetrics(
            attempt=max(a.attempt or 1, b.attempt or 1),
            input_tokens=(a.input_tokens or 0) + (b.input_tokens or 0),
            output_tokens=(a.output_tokens or 0) + (b.output_tokens or 0),
            latency_ms=(a.latency_ms or 0) + (b.latency_ms or 0),
            estimated_cost_usd=(a.estimated_cost_usd or 0) + (b.estimated_cost_usd or 0)
            if a.estimated_cost_usd is not None or b.estimated_cost_usd is not None
            else None,
        )
