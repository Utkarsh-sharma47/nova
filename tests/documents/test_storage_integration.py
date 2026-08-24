"""Storage + processor integration tests."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from nova.documents.errors import DOC_PATH_TRAVERSAL, DocumentProcessingError
from nova.documents.models import DocumentProcessingRequest, ProcessingStatus
from nova.documents.service import DocumentProcessingService, process_document
from nova.documents.storage import LocalBlobStore

from .fixtures import make_digital_pdf, make_text_invoice


def test_store_then_process(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path / "blobs")
    document_id = uuid4()
    blob = make_text_invoice()
    uri = store.put(
        blob,
        document_id=document_id,
        media_type="text/plain",
        filename="../../evil/invoice.txt",
    )
    loaded = store.get(uri)
    assert loaded == blob
    result = process_document(
        loaded,
        document_id=document_id,
        original_filename="invoice.txt",
        service=DocumentProcessingService(),
    )
    assert result.status is ProcessingStatus.SUCCEEDED
    assert result.content is not None
    assert "INV-1001" in (result.content.text or "")


def test_store_pdf_round_trip(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path / "blobs")
    document_id = uuid4()
    blob = make_digital_pdf()
    uri = store.put(
        blob, document_id=document_id, media_type="application/pdf", filename="bol.pdf"
    )
    result = DocumentProcessingService().process(
        DocumentProcessingRequest(
            document_id=document_id,
            blob=store.get(uri),
            original_filename="bol.pdf",
            storage_uri=uri,
            document_type="BILL_OF_LADING",
        )
    )
    assert result.source.storage_uri == uri
    assert result.status in {ProcessingStatus.SUCCEEDED, ProcessingStatus.PARTIAL}


def test_storage_rejects_traversal_uri(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path / "blobs")
    with pytest.raises(DocumentProcessingError) as exc:
        store.get("nova-local://../etc/passwd")
    assert exc.value.error_code == DOC_PATH_TRAVERSAL
