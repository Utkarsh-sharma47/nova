"""Passthrough text adapter for fixtures and deterministic tests."""

from __future__ import annotations

from uuid import UUID

from nova.contracts.common import DocumentContent
from nova.documents.errors import DOC_CORRUPT, DOC_UNREADABLE, DocumentProcessingError

ADAPTER_NAME = "passthrough_text"
ADAPTER_VERSION = "1.0.0"


class PassthroughTextAdapter:
    @property
    def name(self) -> str:
        return ADAPTER_NAME

    @property
    def version(self) -> str:
        return ADAPTER_VERSION

    def supports(self, media_type: str) -> bool:
        return media_type.split(";")[0].strip().lower() == "text/plain"

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
            text = blob.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentProcessingError(DOC_CORRUPT, "Text document is not valid UTF-8") from exc
        return DocumentContent(
            media_type="text/plain",
            text=text,
            page_texts=[text],
            layout={"page_count": 1, "adapter": ADAPTER_NAME},
            processor_name=self.name,
            processor_version=self.version,
            warnings=[],
        )
