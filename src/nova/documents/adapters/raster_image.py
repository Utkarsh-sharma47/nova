"""Raster image adapter — preserves bytes for vision LLMs; no local OCR."""

from __future__ import annotations

import base64
from uuid import UUID

from nova.contracts.common import DocumentContent, DocumentImage
from nova.documents.errors import DOC_CORRUPT, DOC_UNREADABLE, DocumentProcessingError

ADAPTER_NAME = "raster_image"
ADAPTER_VERSION = "1.0.0"

_SUPPORTED = frozenset({"image/png", "image/jpeg"})


class RasterImageAdapter:
    """Accept PNG/JPEG for vision extraction. Does not invent text via OCR."""

    @property
    def name(self) -> str:
        return ADAPTER_NAME

    @property
    def version(self) -> str:
        return ADAPTER_VERSION

    def supports(self, media_type: str) -> bool:
        return media_type.split(";")[0].strip().lower() in _SUPPORTED

    def process(
        self,
        blob: bytes,
        *,
        media_type: str,
        document_id: UUID | None = None,
        trace_id: UUID | None = None,
    ) -> DocumentContent:
        del document_id, trace_id
        normalized = media_type.split(";")[0].strip().lower()
        if normalized == "image/jpg":
            normalized = "image/jpeg"
        if not self.supports(normalized):
            raise DocumentProcessingError(
                DOC_UNREADABLE,
                f"{ADAPTER_NAME} cannot process media type {media_type}",
            )
        if not blob:
            raise DocumentProcessingError(DOC_CORRUPT, "Image blob is empty")
        if normalized == "image/png" and not blob.startswith(b"\x89PNG\r\n\x1a\n"):
            raise DocumentProcessingError(DOC_CORRUPT, "PNG magic bytes missing")
        if normalized == "image/jpeg" and not blob.startswith(b"\xff\xd8\xff"):
            raise DocumentProcessingError(DOC_CORRUPT, "JPEG magic bytes missing")

        encoded = base64.b64encode(blob).decode("ascii")
        return DocumentContent(
            media_type=normalized,
            text=None,
            page_texts=None,
            images=[DocumentImage(media_type=normalized, data_base64=encoded)],
            layout={"page_count": 1, "adapter": ADAPTER_NAME, "vision_required": True},
            processor_name=self.name,
            processor_version=self.version,
            warnings=["no_local_ocr_vision_llm_required"],
        )
