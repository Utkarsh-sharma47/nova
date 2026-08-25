"""Contract tests for document processing result models."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from nova.contracts import DocumentContent, ErrorResponse, ErrorType
from nova.documents.errors import DOC_CORRUPT, DocumentProcessingError
from nova.documents.models import (
    DocumentProcessingResult,
    DocumentSourceMetadata,
    ProcessingStatus,
)
from nova.documents.port import DocumentProcessorPort
from nova.documents.service import process_document

from .fixtures import make_corrupt_pdf, make_text_invoice


def test_processing_result_round_trip() -> None:
    result = DocumentProcessingResult(
        document_id=uuid4(),
        document_type="INVOICE",
        status=ProcessingStatus.SUCCEEDED,
        content=DocumentContent(
            media_type="text/plain",
            text="hello",
            processor_name="passthrough_text",
            processor_version="1.0.0",
        ),
        source=DocumentSourceMetadata(
            detected_media_type="text/plain",
            byte_size=5,
            content_sha256="a" * 64,
        ),
        processor_version="1.0.0",
    )
    assert result.model_dump()["status"] == "SUCCEEDED"


def test_processing_result_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        DocumentProcessingResult(
            document_id=uuid4(),
            status=ProcessingStatus.FAILED,
            source=DocumentSourceMetadata(
                detected_media_type="text/plain",
                byte_size=0,
                content_sha256="0" * 64,
            ),
            processor_version="1.0.0",
            unexpected=True,  # type: ignore[call-arg]
        )


def test_error_maps_to_contract() -> None:
    err = DocumentProcessingError(DOC_CORRUPT, "bad pdf", details={"reason": "eof"})
    response: ErrorResponse = err.to_error_response()
    assert response.error_type is ErrorType.DOCUMENT_PROCESSING
    assert response.error_code == DOC_CORRUPT
    assert response.retryable is False


def test_failed_processing_has_no_extraction_fields() -> None:
    result = process_document(
        make_corrupt_pdf(),
        document_id=uuid4(),
        original_filename="bad.pdf",
    )
    assert result.status is ProcessingStatus.FAILED
    assert result.content is None
    dumped = result.model_dump()
    assert "fields" not in dumped
    assert "extracted" not in dumped


def test_port_runtime_checkable() -> None:
    from nova.documents import DigitalPdfAdapter, PassthroughTextAdapter

    assert isinstance(DigitalPdfAdapter(), DocumentProcessorPort)
    assert isinstance(PassthroughTextAdapter(), DocumentProcessorPort)
    assert callable(process_document)


def test_success_content_is_document_content_contract() -> None:
    result = process_document(
        make_text_invoice(),
        document_id=uuid4(),
        original_filename="invoice.txt",
    )
    assert result.content is not None
    DocumentContent.model_validate(result.content.model_dump())
