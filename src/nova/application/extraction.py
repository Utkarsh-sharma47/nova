"""Application orchestration for extraction after document storage."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from nova.contracts.common import DocumentContent, FieldPresence
from nova.contracts.extraction import ExtractionRequest, ExtractionResult, ExtractionStatus
from nova.documents import DocumentProcessingRequest, DocumentProcessingService, ProcessingStatus
from nova.domain.lifecycle import (
    DocumentStatus,
    VerificationRunStatus,
    assert_document_transition,
    assert_run_transition,
)
from nova.extraction.fields import required_fields_for
from nova.extraction.prompts import PROMPT_ID, PROMPT_VERSION
from nova.extraction.service import AGENT_VERSION, ExtractorService
from nova.infrastructure.storage import DocumentStoragePort
from nova.llm.port import LLMPort
from nova.persistence.models import (
    AgentExecution,
    Document,
    DocumentVersion,
    ExtractedFieldRow,
    ModelCallMetadata,
    VerificationRun,
    utc_now,
)
from nova.persistence.repositories import NovaRepository

logger = logging.getLogger("nova.application.extraction")

_TYPE_TO_WIRE = {
    "commercial_invoice": "INVOICE",
    "bill_of_lading": "BILL_OF_LADING",
    "packing_list": "OTHER",
    "other": "OTHER",
}


class ExtractionApplicationService:
    """Load stored document → ExtractorService → append-only persistence + lifecycle."""

    def __init__(
        self,
        session: Session,
        storage: DocumentStoragePort,
        extractor: ExtractorService,
        *,
        processor: DocumentProcessingService | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.extractor = extractor
        self.processor = processor or DocumentProcessingService()
        self.repository = NovaRepository(session)

    def extract_for_run(
        self,
        *,
        document_id: UUID,
        verification_run_id: UUID,
        trace_id: UUID,
    ) -> ExtractionResult:
        existing = self.repository.extractor_execution(verification_run_id)
        if existing is not None and existing.result_json is not None:
            return ExtractionResult.model_validate(existing.result_json)

        document = self.repository.document(document_id)
        if document is None:
            raise LookupError(f"document not found: {document_id}")
        run = self.session.get(VerificationRun, verification_run_id)
        if run is None:
            raise LookupError(f"verification run not found: {verification_run_id}")

        version = _current_version(document)
        if version is None:
            raise LookupError("document has no current version")

        content = self._load_content(document, version, trace_id)
        wire_type = _TYPE_TO_WIRE.get(document.document_type, "OTHER")
        required = required_fields_for(wire_type)

        self._transition_start(document, run)
        agent_execution_id = uuid4()
        execution = AgentExecution(
            agent_execution_id=agent_execution_id,
            verification_run_id=verification_run_id,
            document_id=document_id,
            document_version_id=version.document_version_id,
            stage="extractor",
            status="running",
            attempt_group=1,
            agent_version=AGENT_VERSION,
            prompt_id=PROMPT_ID,
            prompt_version=PROMPT_VERSION,
            trace_id=str(trace_id),
            started_at=utc_now(),
        )
        self.repository.add(execution)
        self.repository.flush()

        request = ExtractionRequest(
            trace_id=trace_id,
            run_id=verification_run_id,
            agent_execution_id=agent_execution_id,
            document_id=document_id,
            document_version_id=version.document_version_id,
            shipment_id=document.shipment_id,
            customer_id=document.shipment.customer_id if document.shipment else None,
            document_type=wire_type,
            content=content,
            required_fields=required,
            timeout_ms=60_000,
        )
        result = self.extractor.extract(request)
        self._persist_result(execution, run, document, version, result)
        self.repository.flush()
        return result

    def _load_content(
        self,
        document: Document,
        version: DocumentVersion,
        trace_id: UUID,
    ) -> DocumentContent:
        blob = self._read_blob(version.storage_uri)
        processing = self.processor.process(
            DocumentProcessingRequest(
                document_id=document.document_id,
                blob=blob,
                document_type=_TYPE_TO_WIRE.get(document.document_type),
                declared_media_type=version.media_type,
                original_filename=version.original_filename,
                storage_uri=version.storage_uri,
                trace_id=trace_id,
            )
        )
        if processing.status is ProcessingStatus.FAILED or processing.content is None:
            return DocumentContent(
                media_type=version.media_type,
                text=None,
                processor_name=version.processor_name or "unknown",
                processor_version=version.processor_version or "0",
                warnings=[processing.error_code or "DOC_UNREADABLE"],
            )
        return processing.content

    def _read_blob(self, storage_uri: str) -> bytes:
        if storage_uri.startswith("file://"):
            path = Path(storage_uri.removeprefix("file://"))
            return path.read_bytes()
        raise ValueError("unsupported storage URI scheme")

    def _transition_start(self, document: Document, run: VerificationRun) -> None:
        current_doc = DocumentStatus(document.status)
        assert_document_transition(current_doc, DocumentStatus.IN_PIPELINE)
        document.status = DocumentStatus.IN_PIPELINE.value
        document.updated_at = utc_now()

        current_run = VerificationRunStatus(run.status)
        if current_run is VerificationRunStatus.QUEUED:
            assert_run_transition(current_run, VerificationRunStatus.RUNNING)
            run.status = VerificationRunStatus.RUNNING.value
            run.started_at = utc_now()
        shipment = document.shipment
        if shipment is not None and shipment.status == "open":
            shipment.status = "extracting"
            shipment.updated_at = utc_now()
        self.repository.flush()

    def _persist_result(
        self,
        execution: AgentExecution,
        run: VerificationRun,
        document: Document,
        version: DocumentVersion,
        result: ExtractionResult,
    ) -> None:
        now = utc_now()
        status_map = {
            ExtractionStatus.SUCCEEDED: "succeeded",
            ExtractionStatus.PARTIAL: "partial",
            ExtractionStatus.FAILED: "failed",
            ExtractionStatus.COMPLETED: "succeeded",
        }
        execution.status = status_map[result.status]
        execution.provider = result.model_metadata.provider if result.model_metadata else None
        execution.model_name = result.model_metadata.model if result.model_metadata else None
        execution.prompt_version = (
            result.model_metadata.prompt_version if result.model_metadata else PROMPT_VERSION
        )
        execution.attempt_count = (
            result.usage.attempt if result.usage and result.usage.attempt else 1
        )
        execution.error_code = result.error_code
        execution.error_message = result.error_message
        execution.result_json = result.model_dump(mode="json")
        execution.completed_at = now
        if result.usage and result.usage.latency_ms is not None:
            execution.duration_ms = result.usage.latency_ms

        model_call_id: UUID | None = None
        if result.model_metadata is not None:
            model_call = ModelCallMetadata(
                verification_run_id=run.verification_run_id,
                agent_execution_id=execution.agent_execution_id,
                stage="extractor",
                provider=result.model_metadata.provider or "unknown",
                model_name=result.model_metadata.model or "unknown",
                prompt_version=result.model_metadata.prompt_version or PROMPT_VERSION,
                response_schema_version=result.contract_version,
                temperature=result.model_metadata.temperature,
                token_input=result.usage.input_tokens if result.usage else None,
                token_output=result.usage.output_tokens if result.usage else None,
                cost_usd=result.usage.estimated_cost_usd if result.usage else None,
                latency_ms=result.usage.latency_ms if result.usage else None,
                attempt=result.usage.attempt if result.usage else None,
            )
            self.repository.add(model_call)
            self.repository.flush()
            model_call_id = model_call.model_call_id

        for field in result.fields:
            is_missing = field.presence == FieldPresence.MISSING
            row = ExtractedFieldRow(
                verification_run_id=run.verification_run_id,
                document_version_id=version.document_version_id,
                agent_execution_id=execution.agent_execution_id,
                model_call_id=model_call_id,
                field_key=field.field_name,
                value_json=field.value,
                value_type=field.value_type,
                presence=field.presence.value,
                confidence=field.confidence,
                evidence_json=[item.model_dump(mode="json") for item in field.evidence],
                is_missing=is_missing,
                absence_reason=(
                    field.presence.value if field.presence != FieldPresence.KNOWN else None
                ),
                uncertainty_json={
                    "flag": field.uncertainty.value,
                    "codes": [code.value for code in field.uncertainty_codes],
                },
                extractor_notes="; ".join(field.warnings) if field.warnings else None,
            )
            self.repository.add(row)

        if result.status is ExtractionStatus.FAILED:
            assert_document_transition(
                DocumentStatus(document.status),
                DocumentStatus.FAILED,
            )
            document.status = DocumentStatus.FAILED.value
            assert_run_transition(VerificationRunStatus(run.status), VerificationRunStatus.FAILED)
            run.status = VerificationRunStatus.FAILED.value
            run.error_code = result.error_code
            run.error_message = result.error_message
            run.completed_at = now
        else:
            assert_document_transition(
                DocumentStatus(document.status),
                DocumentStatus.EXTRACTED,
            )
            document.status = DocumentStatus.EXTRACTED.value
            # Keep verification run RUNNING so validator/router can continue the same run.
            if VerificationRunStatus(run.status) is VerificationRunStatus.QUEUED:
                assert_run_transition(
                    VerificationRunStatus.QUEUED,
                    VerificationRunStatus.RUNNING,
                )
                run.status = VerificationRunStatus.RUNNING.value
                run.started_at = now
        document.updated_at = now
        self.repository.flush()


def _current_version(document: Document) -> DocumentVersion | None:
    for version in document.versions:
        if version.document_version_id == document.current_version_id:
            return version
    return None


def build_default_llm(provider: str, model: str | None, api_key: str | None) -> LLMPort:
    """Factory: tests/local default to MockLLM. Live providers are adapters only."""
    normalized = provider.lower().strip()
    if normalized in {"mock", "test", "none", ""}:
        from nova.extraction.heuristic import heuristic_extractor_response
        from nova.llm.mock import MockLLM

        return MockLLM(
            factory=heuristic_extractor_response,
            model=model or "mock-extractor-v1",
        )
    if normalized in {"openai", "openai_compatible", "openai-compatible"}:
        if not api_key or not api_key.strip():
            logger.warning(
                "openai_provider_missing_api_key_falling_back_to_mock",
                extra={
                    "event": "llm.provider_fallback",
                    "extra_fields": {"provider": provider, "reason": "missing_api_key"},
                },
            )
            from nova.extraction.heuristic import heuristic_extractor_response
            from nova.llm.mock import MockLLM

            return MockLLM(
                factory=heuristic_extractor_response,
                model=model or "mock-extractor-v1",
            )
        from nova.llm.openai_compatible import OpenAICompatibleLLM

        return OpenAICompatibleLLM(api_key=api_key, model=model, provider_name="openai")

    logger.warning(
        "unsupported_llm_provider_falling_back_to_mock",
        extra={
            "event": "llm.provider_fallback",
            "extra_fields": {"provider": provider},
        },
    )
    from nova.extraction.heuristic import heuristic_extractor_response
    from nova.llm.mock import MockLLM

    return MockLLM(factory=heuristic_extractor_response, model=model or "mock-extractor-v1")
