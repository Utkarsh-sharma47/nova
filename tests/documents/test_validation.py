"""Unit tests for document intake validation and security."""

from __future__ import annotations

import pytest

from nova.documents.errors import (
    DOC_CORRUPT,
    DOC_EMPTY,
    DOC_INVALID_FILENAME,
    DOC_MIME_MISMATCH,
    DOC_PATH_TRAVERSAL,
    DOC_PAYLOAD_TOO_LARGE,
    DOC_UNSUPPORTED_EXTENSION,
    DocumentProcessingError,
)
from nova.documents.limits import DocumentLimits
from nova.documents.security import sanitize_filename
from nova.documents.validation import validate_document

from .fixtures import (
    make_binary_garbage,
    make_corrupt_pdf,
    make_digital_pdf,
    make_pdf_without_eof,
    make_text_invoice,
)


def test_validate_text_and_pdf() -> None:
    text = validate_document(make_text_invoice(), original_filename="invoice.txt")
    assert text.detected_media_type == "text/plain"
    pdf = validate_document(make_digital_pdf(), original_filename="bol.pdf")
    assert pdf.detected_media_type == "application/pdf"
    assert len(pdf.content_sha256) == 64


def test_reject_empty_and_oversized() -> None:
    with pytest.raises(DocumentProcessingError) as empty:
        validate_document(b"")
    assert empty.value.error_code == DOC_EMPTY

    limits = DocumentLimits(max_bytes=64)
    with pytest.raises(DocumentProcessingError) as huge:
        validate_document(b"x" * 128, limits=limits)
    assert huge.value.error_code == DOC_PAYLOAD_TOO_LARGE


def test_reject_unsupported_and_mismatch() -> None:
    with pytest.raises(DocumentProcessingError) as ext:
        validate_document(make_text_invoice(), original_filename="invoice.docx")
    assert ext.value.error_code == DOC_UNSUPPORTED_EXTENSION

    with pytest.raises(DocumentProcessingError):
        validate_document(make_binary_garbage())

    with pytest.raises(DocumentProcessingError) as mismatch:
        validate_document(
            make_text_invoice(),
            original_filename="fake.pdf",
            declared_media_type="application/pdf",
        )
    assert mismatch.value.error_code == DOC_MIME_MISMATCH


def test_reject_corrupt_pdf() -> None:
    with pytest.raises(DocumentProcessingError) as missing_eof:
        validate_document(make_pdf_without_eof(), original_filename="bad.pdf")
    assert missing_eof.value.error_code == DOC_CORRUPT

    with pytest.raises(DocumentProcessingError) as truncated:
        validate_document(make_corrupt_pdf(), original_filename="bad.pdf")
    assert truncated.value.error_code == DOC_CORRUPT


def test_filename_security() -> None:
    assert sanitize_filename("normal-invoice.pdf") == "normal-invoice.pdf"
    assert sanitize_filename(r"..\..\etc\passwd") == "passwd"
    assert sanitize_filename("../../etc/passwd") == "passwd"
    with pytest.raises(DocumentProcessingError) as null_err:
        sanitize_filename("evil\x00.pdf")
    assert null_err.value.error_code == DOC_INVALID_FILENAME
    with pytest.raises(DocumentProcessingError) as trav:
        sanitize_filename("..")
    assert trav.value.error_code == DOC_PATH_TRAVERSAL
