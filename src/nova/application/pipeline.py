"""End-to-end Part 1 verification pipeline orchestration.

Coordinates: document processing → extraction → validation → routing → persistence.
Does not duplicate agent logic; invokes ExtractorService, ValidatorAgent, RouterService.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from nova.agents.validator.agent import ValidatorAgent
from nova.application.extraction import ExtractionApplicationService
from nova.application.rules import (
    DEFAULT_RULESET_ID,
    DEFAULT_RULESET_VERSION,
    default_routing_policy,
    default_rules_for_document_type,
)
from nova.application.validation_persistence import SqlValidationStore
from nova.contracts.extraction import ExtractionResult, ExtractionStatus
from nova.contracts.routing import DecisionKind, DecisionResult, RoutingRequest
from nova.contracts.validation import (
    CustomerRuleSnapshot,
    ValidationRequest,
    ValidationResult,
)
from nova.domain.errors import InvalidLifecycleTransition
from nova.domain.lifecycle import (
    DocumentStatus,
    PipelineStage,
    VerificationRunStatus,
    assert_document_transition,
    assert_run_transition,
)
from nova.extraction.service import ExtractorService
from nova.infrastructure.storage import DocumentStoragePort
from nova.persistence.models import AgentExecution, Document, VerificationRun, utc_now
from nova.persistence.repositories import NovaRepository
from nova.router.persistence import DecisionRepository
from nova.router.service import RouterService

logger = logging.getLogger("nova.pipeline")

_TYPE_TO_WIRE = {
    "commercial_invoice": "INVOICE",
    "bill_of_lading": "BILL_OF_LADING",
    "packing_list": "OTHER",
    "other": "OTHER",
}

_FAILABLE_DOC_STATUSES = frozenset(
    {
        DocumentStatus.CONTENT_AVAILABLE,
        DocumentStatus.IN_PIPELINE,
        DocumentStatus.EXTRACTED,
        DocumentStatus.VALIDATED,
    }
)


@dataclass
class StageTiming:
    document_processing_ms: int = 0
    extraction_ms: int = 0
    validation_ms: int = 0
    routing_ms: int = 0
    total_ms: int = 0


@dataclass
class PipelineResult:
    document_id: UUID
    shipment_id: UUID
    run_id: UUID
    trace_id: UUID
    stage: PipelineStage
    document_status: DocumentStatus
    run_status: VerificationRunStatus
    extraction: ExtractionResult | None = None
    validation: ValidationResult | None = None
    decision: DecisionResult | None = None
    failure_reason: str | None = None
    timings: StageTiming = field(default_factory=StageTiming)
    idempotent_replay: bool = False


class PipelineOrchestrator:
    """Application-level coordinator for one verification run."""

    def __init__(
        self,
        session: Session,
        storage: DocumentStoragePort,
        *,
        extractor: ExtractorService,
        validator: ValidatorAgent | None = None,
        router: RouterService | None = None,
        validation_store: SqlValidationStore | None = None,
        decision_repository: DecisionRepository | None = None,
        rules: list[CustomerRuleSnapshot] | None = None,
        force_failsafe: bool = False,
        skip_if_decided: bool = True,
        auto_commit: bool = True,
    ) -> None:
        self.session = session
        self.storage = storage
        self.repository = NovaRepository(session)
        self.extraction_app = ExtractionApplicationService(session, storage, extractor)
        self.validation_store = validation_store or SqlValidationStore(session)
        self.validator = validator or ValidatorAgent(
            store=self.validation_store,
            persist=True,
        )
        self.router = router or RouterService()
        self.decisions = decision_repository or DecisionRepository(session)
        self._rules_override = rules
        self.force_failsafe = force_failsafe
        self.skip_if_decided = skip_if_decided
        self.auto_commit = auto_commit

    def run(
        self,
        *,
        document_id: UUID,
        verification_run_id: UUID,
        trace_id: UUID,
    ) -> PipelineResult:
        started = time.perf_counter()
        timings = StageTiming()
        self._emit(
            "pipeline_started",
            trace_id=str(trace_id),
            run_id=str(verification_run_id),
            document_id=str(document_id),
            stage=PipelineStage.INGESTED.value,
        )

        document = self.repository.document(document_id)
        if document is None:
            raise LookupError(f"document not found: {document_id}")
        run = self.session.get(VerificationRun, verification_run_id)
        if run is None:
            raise LookupError(f"verification run not found: {verification_run_id}")

        existing_decision = self.decisions.find_by_run(verification_run_id)
        if self.skip_if_decided and existing_decision is not None:
            stored_validation = self.validation_store.find_by_run(verification_run_id)
            extraction_exec = self.repository.extractor_execution(verification_run_id)
            extraction = (
                ExtractionResult.model_validate(extraction_exec.result_json)
                if extraction_exec and extraction_exec.result_json
                else None
            )
            timings.total_ms = int((time.perf_counter() - started) * 1000)
            return PipelineResult(
                document_id=document_id,
                shipment_id=document.shipment_id,
                run_id=verification_run_id,
                trace_id=trace_id,
                stage=PipelineStage.COMPLETED,
                document_status=DocumentStatus(document.status),
                run_status=VerificationRunStatus(run.status),
                extraction=extraction,
                validation=stored_validation.result if stored_validation else None,
                idempotent_replay=True,
                timings=timings,
            )

        try:
            t0 = time.perf_counter()
            extraction = self.extraction_app.extract_for_run(
                document_id=document_id,
                verification_run_id=verification_run_id,
                trace_id=trace_id,
            )
            timings.extraction_ms = int((time.perf_counter() - t0) * 1000)
            self._checkpoint()
            self._emit(
                "document_processed",
                trace_id=str(trace_id),
                run_id=str(verification_run_id),
                document_id=str(document_id),
                stage=PipelineStage.DOCUMENT_PROCESSING.value,
                duration_ms=timings.extraction_ms,
            )
            self._emit(
                "extraction_completed",
                trace_id=str(trace_id),
                run_id=str(verification_run_id),
                document_id=str(document_id),
                stage=PipelineStage.EXTRACTION.value,
                status=extraction.status.value,
                duration_ms=timings.extraction_ms,
            )

            # Refresh after extraction mutations
            self.session.refresh(document)
            self.session.refresh(run)

            if extraction.status is ExtractionStatus.FAILED:
                timings.total_ms = int((time.perf_counter() - started) * 1000)
                self._emit(
                    "pipeline_failed",
                    trace_id=str(trace_id),
                    run_id=str(verification_run_id),
                    document_id=str(document_id),
                    stage=PipelineStage.EXTRACTION.value,
                    failure_reason=extraction.error_code or "EXTRACTION_FAILED",
                )
                self._checkpoint()
                return PipelineResult(
                    document_id=document_id,
                    shipment_id=document.shipment_id,
                    run_id=verification_run_id,
                    trace_id=trace_id,
                    stage=PipelineStage.FAILED,
                    document_status=DocumentStatus.FAILED,
                    run_status=VerificationRunStatus.FAILED,
                    extraction=extraction,
                    failure_reason=extraction.error_code or "EXTRACTION_FAILED",
                    timings=timings,
                )

            self._ensure_run_running(run)
            self._set_shipment_status(document, "validating")

            t1 = time.perf_counter()
            validation = self._validate(
                document=document,
                run=run,
                extraction=extraction,
                trace_id=trace_id,
            )
            timings.validation_ms = int((time.perf_counter() - t1) * 1000)
            self._checkpoint()
            self._emit(
                "validation_completed",
                trace_id=str(trace_id),
                run_id=str(verification_run_id),
                document_id=str(document_id),
                stage=PipelineStage.VALIDATION.value,
                status=validation.status.value,
                duration_ms=timings.validation_ms,
            )

            if DocumentStatus(document.status) is DocumentStatus.EXTRACTED:
                assert_document_transition(DocumentStatus.EXTRACTED, DocumentStatus.VALIDATED)
                document.status = DocumentStatus.VALIDATED.value
                document.updated_at = utc_now()

            stored = self.validation_store.find_by_run(verification_run_id)
            validation_id = (
                stored.validation_result_id
                if stored is not None
                else (validation.agent_execution_id or uuid4())
            )

            self._set_shipment_status(document, "routing")
            t2 = time.perf_counter()
            decision = self._route(
                document=document,
                run=run,
                extraction=extraction,
                validation=validation,
                validation_result_id=validation_id,
                trace_id=trace_id,
            )
            timings.routing_ms = int((time.perf_counter() - t2) * 1000)
            self.decisions.persist(decision)
            self._record_router_execution(document, run, decision, trace_id)

            if DocumentStatus(document.status) is DocumentStatus.VALIDATED:
                assert_document_transition(DocumentStatus.VALIDATED, DocumentStatus.DECIDED)
                document.status = DocumentStatus.DECIDED.value
                document.updated_at = utc_now()

            assert_run_transition(
                VerificationRunStatus(run.status),
                VerificationRunStatus.SUCCEEDED,
            )
            run.status = VerificationRunStatus.SUCCEEDED.value
            run.completed_at = utc_now()
            self._set_shipment_status(document, "decided")
            self._checkpoint()

            timings.total_ms = int((time.perf_counter() - started) * 1000)
            self._emit(
                "decision_completed",
                trace_id=str(trace_id),
                run_id=str(verification_run_id),
                document_id=str(document_id),
                stage=PipelineStage.ROUTING.value,
                status=decision.decision.value,
                duration_ms=timings.routing_ms,
                total_ms=timings.total_ms,
            )
            return PipelineResult(
                document_id=document_id,
                shipment_id=document.shipment_id,
                run_id=verification_run_id,
                trace_id=trace_id,
                stage=PipelineStage.COMPLETED,
                document_status=DocumentStatus.DECIDED,
                run_status=VerificationRunStatus.SUCCEEDED,
                extraction=extraction,
                validation=validation,
                decision=decision,
                timings=timings,
            )
        except InvalidLifecycleTransition:
            self._rollback_if_owning_transaction()
            timings.total_ms = int((time.perf_counter() - started) * 1000)
            self._emit(
                "pipeline_failed",
                trace_id=str(trace_id),
                run_id=str(verification_run_id),
                document_id=str(document_id),
                stage=PipelineStage.FAILED.value,
                failure_reason="INVALID_STATE_TRANSITION",
            )
            raise
        except Exception as exc:
            # Preserve prior stage rows when possible. When auto_commit=True we own the
            # transaction (API path): roll back uncommitted work, then mark failed and
            # commit. When auto_commit=False an outer begin() owns the session — do not
            # rollback (that closes the outer transaction); mark failed in-place.
            self._rollback_if_owning_transaction()
            try:
                document = self.repository.document(document_id)
                run = self.session.get(VerificationRun, verification_run_id)
                if document is not None and run is not None:
                    self._mark_failed(document, run, code=type(exc).__name__)
                    self._checkpoint()
            except Exception:  # noqa: BLE001
                self._rollback_if_owning_transaction()
                logger.exception(
                    "pipeline_mark_failed_failed",
                    extra={"event": "pipeline_mark_failed_failed"},
                )
            timings.total_ms = int((time.perf_counter() - started) * 1000)
            self._emit(
                "pipeline_failed",
                trace_id=str(trace_id),
                run_id=str(verification_run_id),
                document_id=str(document_id),
                stage=PipelineStage.FAILED.value,
                failure_reason=type(exc).__name__,
            )
            raise

    def _checkpoint(self) -> None:
        """Flush stage work; commit when owning the session (API path)."""
        self.session.flush()
        if self.auto_commit:
            self.session.commit()

    def _rollback_if_owning_transaction(self) -> None:
        """Roll back only when this orchestrator owns commits (auto_commit=True)."""
        if self.auto_commit:
            self.session.rollback()

    def _validate(
        self,
        *,
        document: Document,
        run: VerificationRun,
        extraction: ExtractionResult,
        trace_id: UUID,
    ) -> ValidationResult:
        existing = self.validation_store.find_by_run(run.verification_run_id)
        if existing is not None:
            return existing.result

        wire_type = _TYPE_TO_WIRE.get(document.document_type, "OTHER")
        rules = self._rules_override or default_rules_for_document_type(
            document_type=wire_type,
            trace_id=trace_id,
            customer_id=document.shipment.customer_id if document.shipment else None,
        )
        version = next(
            (
                v
                for v in document.versions
                if v.document_version_id == document.current_version_id
            ),
            None,
        )
        assert version is not None
        request = ValidationRequest(
            trace_id=trace_id,
            run_id=run.verification_run_id,
            document_id=document.document_id,
            document_version_id=version.document_version_id,
            shipment_id=document.shipment_id,
            customer_id=document.shipment.customer_id if document.shipment else None,
            extraction_result_id=extraction.agent_execution_id,
            ruleset_id=DEFAULT_RULESET_ID,
            ruleset_version=DEFAULT_RULESET_VERSION,
            rules=rules,
            extracted_fields=list(extraction.fields),
            extraction_status=extraction.status.value,
            timeout_ms=30_000,
        )
        return self.validator.validate(request)

    def _route(
        self,
        *,
        document: Document,
        run: VerificationRun,
        extraction: ExtractionResult,
        validation: ValidationResult,
        validation_result_id: UUID,
        trace_id: UUID,
    ) -> DecisionResult:
        wire_type = _TYPE_TO_WIRE.get(document.document_type, "OTHER")
        version_id = document.current_version_id
        assert version_id is not None
        policy = default_routing_policy(document_type=wire_type, trace_id=trace_id)
        blocking_uncertain = any(
            c.blocking and c.outcome.value == "UNCERTAIN" for c in validation.checks
        )
        request = RoutingRequest(
            trace_id=trace_id,
            run_id=run.verification_run_id,
            document_id=document.document_id,
            document_version_id=version_id,
            shipment_id=document.shipment_id,
            customer_id=document.shipment.customer_id if document.shipment else None,
            verification_run_id=run.verification_run_id,
            validation_result_id=validation_result_id,
            extraction=extraction,
            validation=validation,
            policy=policy,
            blocking_uncertainty_present=blocking_uncertain,
            timeout_ms=15_000,
        )
        return self.router.decide(request, force_failsafe=self.force_failsafe)

    def _record_router_execution(
        self,
        document: Document,
        run: VerificationRun,
        decision: DecisionResult,
        trace_id: UUID,
    ) -> None:
        version_id = document.current_version_id
        assert version_id is not None
        execution = AgentExecution(
            agent_execution_id=uuid4(),
            verification_run_id=run.verification_run_id,
            document_id=document.document_id,
            document_version_id=version_id,
            stage="router",
            status="succeeded",
            attempt_group=1,
            agent_version=decision.agent_version,
            trace_id=str(trace_id),
            result_json={
                "decision": decision.decision.value,
                "reason_codes": decision.reason_codes,
                "actor_type": decision.actor_type.value,
            },
            started_at=utc_now(),
            completed_at=utc_now(),
        )
        self.repository.add(execution)
        self.repository.flush()

    def _ensure_run_running(self, run: VerificationRun) -> None:
        current = VerificationRunStatus(run.status)
        if current is VerificationRunStatus.QUEUED:
            assert_run_transition(current, VerificationRunStatus.RUNNING)
            run.status = VerificationRunStatus.RUNNING.value
            run.started_at = utc_now()
        elif current is VerificationRunStatus.SUCCEEDED:
            raise InvalidLifecycleTransition(
                details={
                    "entity": "verification_run",
                    "from": current.value,
                    "to": VerificationRunStatus.RUNNING.value,
                }
            )

    def _mark_failed(self, document: Document, run: VerificationRun, *, code: str) -> None:
        now = utc_now()
        current_doc = DocumentStatus(document.status)
        if current_doc in _FAILABLE_DOC_STATUSES:
            assert_document_transition(current_doc, DocumentStatus.FAILED)
            document.status = DocumentStatus.FAILED.value
            document.updated_at = now

        current_run = VerificationRunStatus(run.status)
        if current_run is VerificationRunStatus.QUEUED:
            assert_run_transition(current_run, VerificationRunStatus.RUNNING)
            run.status = VerificationRunStatus.RUNNING.value
            run.started_at = now
            current_run = VerificationRunStatus.RUNNING
        if current_run is VerificationRunStatus.RUNNING:
            assert_run_transition(current_run, VerificationRunStatus.FAILED)
            run.status = VerificationRunStatus.FAILED.value
            run.error_code = code
            run.completed_at = now

    def _set_shipment_status(self, document: Document, status: str) -> None:
        shipment = document.shipment
        if shipment is not None:
            shipment.status = status
            shipment.updated_at = utc_now()

    def _emit(self, event: str, **fields: Any) -> None:
        safe = {k: v for k, v in fields.items() if k not in {"content", "blob", "api_key"}}
        logger.info(event, extra={"event": event, "extra_fields": safe})


__all__ = [
    "DecisionKind",
    "PipelineOrchestrator",
    "PipelineResult",
    "StageTiming",
]
