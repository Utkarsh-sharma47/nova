"""Large-file rejection and latency smoke tests."""

from __future__ import annotations

import time
from uuid import uuid4

from nova.documents.limits import DocumentLimits
from nova.documents.models import ProcessingStatus
from nova.documents.service import DocumentProcessingService, process_document

from .fixtures import make_digital_pdf, make_text_invoice


def test_large_file_rejected() -> None:
    limits = DocumentLimits(max_bytes=1024)
    service = DocumentProcessingService(limits=limits)
    blob = b"A" * 2048
    result = process_document(
        blob,
        document_id=uuid4(),
        original_filename="big.txt",
        service=service,
    )
    assert result.status is ProcessingStatus.FAILED
    assert result.error_code == "DOC_PAYLOAD_TOO_LARGE"


def test_size_vs_latency_smoke() -> None:
    service = DocumentProcessingService()
    samples: list[tuple[int, float]] = []
    for pages in (1, 3, 5):
        blob = make_digital_pdf(pages=pages)
        started = time.perf_counter()
        result = process_document(
            blob,
            document_id=uuid4(),
            original_filename="bol.pdf",
            service=service,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        assert result.status in {ProcessingStatus.SUCCEEDED, ProcessingStatus.PARTIAL}
        samples.append((len(blob), elapsed_ms))
        assert elapsed_ms < 5_000  # soft ceiling; not an optimization target

    # Larger payloads should not explode latency by orders of magnitude in this smoke range.
    assert samples[0][1] < 5_000
    assert samples[-1][1] < 5_000


def test_text_processing_fast_path() -> None:
    started = time.perf_counter()
    result = process_document(
        make_text_invoice(),
        document_id=uuid4(),
        original_filename="invoice.txt",
    )
    assert result.status is ProcessingStatus.SUCCEEDED
    assert (time.perf_counter() - started) * 1000 < 1_000
