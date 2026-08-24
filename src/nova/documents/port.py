"""DocumentProcessorPort — stable abstraction for bytes → DocumentContent."""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from nova.contracts.common import DocumentContent


@runtime_checkable
class DocumentProcessorPort(Protocol):
    """Pluggable document processor (ADR-0006)."""

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def supports(self, media_type: str) -> bool: ...

    def process(
        self,
        blob: bytes,
        *,
        media_type: str,
        document_id: UUID | None = None,
        trace_id: UUID | None = None,
    ) -> DocumentContent: ...
