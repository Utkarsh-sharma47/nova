"""Digital PDF adapter — text extraction for clean digital PDFs (no OCR).

Technology: pypdf
License: BSD-3-Clause
Limitations: extracts embedded text only; scanned/image-only pages yield empty
             text and a warning. Does not perform OCR.
Accuracy: suitable for digitally generated trade PDFs; OCR path deferred.
Deployment: pure-Python dependency; no system packages required.
"""

from __future__ import annotations

from io import BytesIO
from uuid import UUID

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from nova.contracts.common import DocumentContent
from nova.documents.errors import (
    DOC_CORRUPT,
    DOC_TOO_MANY_PAGES,
    DOC_UNREADABLE,
    DocumentProcessingError,
)
from nova.documents.limits import DEFAULT_LIMITS, DocumentLimits

ADAPTER_NAME = "digital_pdf"
ADAPTER_VERSION = "1.0.0"


class DigitalPdfAdapter:
    """DocumentProcessorPort implementation for digital (text-bearing) PDFs."""

    def __init__(self, limits: DocumentLimits = DEFAULT_LIMITS) -> None:
        self._limits = limits

    @property
    def name(self) -> str:
        return ADAPTER_NAME

    @property
    def version(self) -> str:
        return ADAPTER_VERSION

    def supports(self, media_type: str) -> bool:
        return media_type.split(";")[0].strip().lower() == "application/pdf"

    def process(
        self,
        blob: bytes,
        *,
        media_type: str,
        document_id: UUID | None = None,
        trace_id: UUID | None = None,
    ) -> DocumentContent:
        del document_id, trace_id
        if not self.supports(media_type):
            raise DocumentProcessingError(
                DOC_UNREADABLE,
                f"{ADAPTER_NAME} cannot process media type {media_type}",
            )
        try:
            reader = PdfReader(BytesIO(blob), strict=False)
        except PdfReadError as exc:
            raise DocumentProcessingError(DOC_CORRUPT, "PDF could not be parsed") from exc
        except Exception as exc:
            raise DocumentProcessingError(
                DOC_CORRUPT, "PDF parsing failed unexpectedly"
            ) from exc

        try:
            obj_count = len(reader.xref) if reader.xref is not None else 0
        except Exception:
            obj_count = 0
        if obj_count > self._limits.max_pdf_objects:
            raise DocumentProcessingError(
                DOC_CORRUPT,
                "PDF exceeds maximum object count (possible decompression bomb)",
                details={
                    "object_count": obj_count,
                    "max_pdf_objects": self._limits.max_pdf_objects,
                },
            )
        if reader.is_encrypted:
            raise DocumentProcessingError(DOC_UNREADABLE, "Encrypted PDFs are not supported")

        page_count = len(reader.pages)
        if page_count > self._limits.max_pages:
            raise DocumentProcessingError(
                DOC_TOO_MANY_PAGES,
                f"PDF exceeds maximum of {self._limits.max_pages} pages",
                details={"page_count": page_count, "max_pages": self._limits.max_pages},
            )

        warnings: list[str] = []
        page_texts: list[str] = []
        for index, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
                warnings.append(f"page_{index + 1}_text_extraction_failed")
            page_texts.append(text)

        combined = "\n\n".join(page_texts).strip()
        empty_pages = sum(1 for t in page_texts if not t.strip())
        if page_count > 0 and empty_pages == page_count:
            warnings.append("no_extractable_text_ocr_not_configured")
        elif empty_pages > 0:
            warnings.append(f"empty_pages:{empty_pages}")

        return DocumentContent(
            media_type="application/pdf",
            text=combined or None,
            page_texts=page_texts,
            layout={
                "page_count": page_count,
                "empty_page_count": empty_pages,
                "adapter": ADAPTER_NAME,
            },
            processor_name=self.name,
            processor_version=self.version,
            warnings=warnings,
        )
