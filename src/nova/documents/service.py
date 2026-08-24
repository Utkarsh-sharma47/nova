"""Document processing service — validate, select adapter, produce result."""

from __future__ import annotations

import time
from uuid import UUID

from nova.documents import observability as obs
from nova.documents.adapters.registry import ProcessorRegistry, default_registry
from nova.documents.errors import DOC_INTERNAL, DocumentProcessingError
from nova.documents.limits import DEFAULT_LIMITS, PROCESSOR_PACKAGE_VERSION, DocumentLimits
from nova.documents.models import (
    DocumentProcessingRequest,
    DocumentProcessingResult,
    DocumentSourceMetadata,
    ProcessingStatus,
)
from nova.documents.validation import validate_document


class DocumentProcessingService:
    """Orchestrates intake validation + DocumentProcessorPort adapters."""

    def __init__(
        self,
        registry: ProcessorRegistry | None = None,
        limits: DocumentLimits = DEFAULT_LIMITS,
        processor_version: str = PROCESSOR_PACKAGE_VERSION,
    ) -> None:
        self._limits = limits
        self._registry = registry or default_registry(limits=limits)
        self._processor_version = processor_version

    @property
    def processor_version(self) -> str:
        return self._processor_version

    def process(self, request: DocumentProcessingRequest) -> DocumentProcessingResult:
        started = time.perf_counter()
        document_id = request.document_id
        trace_id = request.trace_id

        try:
            validated = validate_document(
                request.blob,
                declared_media_type=request.declared_media_type,
                original_filename=request.original_filename,
                limits=self._limits,
            )
        except DocumentProcessingError as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            obs.log_processing_failure(
                document_id=document_id,
                trace_id=trace_id,
                processor_version=self._processor_version,
                error_code=exc.error_code,
                duration_ms=duration_ms,
            )
            return self._failed_result(
                request,
                error=exc,
                duration_ms=duration_ms,
                detected_media_type=request.declared_media_type or "application/octet-stream",
                byte_size=len(request.blob),
                content_sha256="0" * 64,
            )

        obs.log_processing_start(
            document_id=document_id,
            trace_id=trace_id,
            processor_version=self._processor_version,
            byte_size=validated.byte_size,
            media_type=validated.detected_media_type,
        )

        source = DocumentSourceMetadata(
            original_filename=validated.original_filename,
            sanitized_filename=validated.sanitized_filename,
            declared_media_type=validated.declared_media_type,
            detected_media_type=validated.detected_media_type,
            byte_size=validated.byte_size,
            content_sha256=validated.content_sha256,
            storage_uri=request.storage_uri,
        )

        try:
            adapter = self._registry.get(validated.detected_media_type)
            content = adapter.process(
                validated.blob,
                media_type=validated.detected_media_type,
                document_id=document_id,
                trace_id=trace_id,
            )
        except DocumentProcessingError as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            obs.log_processing_failure(
                document_id=document_id,
                trace_id=trace_id,
                processor_version=self._processor_version,
                error_code=exc.error_code,
                duration_ms=duration_ms,
            )
            return DocumentProcessingResult(
                document_id=document_id,
                document_type=request.document_type,
                status=ProcessingStatus.FAILED,
                content=None,
                source=source,
                warnings=[],
                error_code=exc.error_code,
                error_message=exc.message,
                processor_version=self._processor_version,
                duration_ms=duration_ms,
                trace_id=trace_id,
                request_id=request.request_id,
            )
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            obs.log_processing_failure(
                document_id=document_id,
                trace_id=trace_id,
                processor_version=self._processor_version,
                error_code=DOC_INTERNAL,
                duration_ms=duration_ms,
            )
            return DocumentProcessingResult(
                document_id=document_id,
                document_type=request.document_type,
                status=ProcessingStatus.FAILED,
                content=None,
                source=source,
                warnings=[],
                error_code=DOC_INTERNAL,
                error_message="Unexpected document processing failure",
                processor_version=self._processor_version,
                duration_ms=duration_ms,
                trace_id=trace_id,
                request_id=request.request_id,
            )

        duration_ms = (time.perf_counter() - started) * 1000
        page_count = None
        if content.layout and isinstance(content.layout.get("page_count"), int):
            page_count = content.layout["page_count"]
        source = source.model_copy(update={"page_count": page_count})

        warnings = list(content.warnings)
        status = ProcessingStatus.SUCCEEDED
        if warnings and (content.text is None or not content.text.strip()):
            status = ProcessingStatus.PARTIAL

        obs.log_processing_complete(
            document_id=document_id,
            trace_id=trace_id,
            processor_version=self._processor_version,
            status=status.value,
            duration_ms=duration_ms,
            media_type=validated.detected_media_type,
            page_count=page_count,
        )

        return DocumentProcessingResult(
            document_id=document_id,
            document_type=request.document_type,
            status=status,
            content=content,
            source=source,
            warnings=warnings,
            processor_version=self._processor_version,
            duration_ms=duration_ms,
            trace_id=trace_id,
            request_id=request.request_id,
        )

    def _failed_result(
        self,
        request: DocumentProcessingRequest,
        *,
        error: DocumentProcessingError,
        duration_ms: float,
        detected_media_type: str,
        byte_size: int,
        content_sha256: str,
    ) -> DocumentProcessingResult:
        return DocumentProcessingResult(
            document_id=request.document_id,
            document_type=request.document_type,
            status=ProcessingStatus.FAILED,
            content=None,
            source=DocumentSourceMetadata(
                original_filename=request.original_filename,
                sanitized_filename=None,
                declared_media_type=request.declared_media_type,
                detected_media_type=detected_media_type,
                byte_size=byte_size,
                content_sha256=content_sha256,
                storage_uri=request.storage_uri,
            ),
            warnings=[],
            error_code=error.error_code,
            error_message=error.message,
            processor_version=self._processor_version,
            duration_ms=duration_ms,
            trace_id=request.trace_id,
            request_id=request.request_id,
        )


def process_document(
    blob: bytes,
    *,
    document_id: UUID,
    document_type: str | None = None,
    declared_media_type: str | None = None,
    original_filename: str | None = None,
    trace_id: UUID | None = None,
    service: DocumentProcessingService | None = None,
) -> DocumentProcessingResult:
    svc = service or DocumentProcessingService()
    return svc.process(
        DocumentProcessingRequest(
            document_id=document_id,
            blob=blob,
            document_type=document_type,
            declared_media_type=declared_media_type,
            original_filename=original_filename,
            trace_id=trace_id,
        )
    )
