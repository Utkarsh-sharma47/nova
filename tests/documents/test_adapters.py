"""Unit tests for document processor adapters."""

from __future__ import annotations

from uuid import uuid4

from nova.documents.adapters.digital_pdf import DigitalPdfAdapter
from nova.documents.adapters.passthrough_text import PassthroughTextAdapter
from nova.documents.models import ProcessingStatus
from nova.documents.port import DocumentProcessorPort
from nova.documents.service import DocumentProcessingService, process_document

from .fixtures import make_digital_pdf, make_text_invoice


def test_adapters_satisfy_port() -> None:
    pdf = DigitalPdfAdapter()
    text = PassthroughTextAdapter()
    assert isinstance(pdf, DocumentProcessorPort)
    assert isinstance(text, DocumentProcessorPort)


def test_passthrough_text_extracts() -> None:
    adapter = PassthroughTextAdapter()
    content = adapter.process(make_text_invoice(), media_type="text/plain")
    assert content.text is not None
    assert "INV-1001" in content.text
    assert content.processor_name == "passthrough_text"


def test_digital_pdf_extracts_text() -> None:
    adapter = DigitalPdfAdapter()
    blob = make_digital_pdf(text="BILL OF LADING BL-NOVA-0001")
    content = adapter.process(blob, media_type="application/pdf")
    assert content.layout is not None
    assert content.layout["page_count"] == 1
    assert content.text is not None
    assert "BL-NOVA-0001" in content.text


def test_service_processes_supported_types() -> None:
    service = DocumentProcessingService()
    text_result = process_document(
        make_text_invoice(),
        document_id=uuid4(),
        original_filename="invoice.txt",
        document_type="INVOICE",
        service=service,
    )
    assert text_result.status is ProcessingStatus.SUCCEEDED
    assert text_result.content is not None

    pdf_result = process_document(
        make_digital_pdf(),
        document_id=uuid4(),
        original_filename="bol.pdf",
        document_type="BILL_OF_LADING",
        service=service,
    )
    assert pdf_result.status in {ProcessingStatus.SUCCEEDED, ProcessingStatus.PARTIAL}
    assert pdf_result.content is not None
    assert pdf_result.duration_ms is not None
