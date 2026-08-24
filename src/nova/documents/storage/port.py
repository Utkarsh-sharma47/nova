"""Blob storage port for document bytes."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class DocumentBlobStorePort(Protocol):
    def put(
        self,
        blob: bytes,
        *,
        document_id: UUID,
        media_type: str,
        filename: str | None = None,
    ) -> str: ...

    def get(self, storage_uri: str) -> bytes: ...

    def delete(self, storage_uri: str) -> None: ...
