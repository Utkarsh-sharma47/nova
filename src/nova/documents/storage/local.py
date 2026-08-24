"""Local filesystem blob store for development and integration tests."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

from nova.documents.errors import DOC_INTERNAL, DOC_PATH_TRAVERSAL, DocumentProcessingError
from nova.documents.security import assert_path_within_root, sanitize_filename


class LocalBlobStore:
    SCHEME = "nova-local"

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def put(
        self,
        blob: bytes,
        *,
        document_id: UUID,
        media_type: str,
        filename: str | None = None,
    ) -> str:
        safe_name = sanitize_filename(filename) if filename else None
        object_id = uuid4()
        doc_dir = assert_path_within_root(self._root / str(document_id), self._root)
        doc_dir.mkdir(parents=True, exist_ok=True)
        bin_path = assert_path_within_root(doc_dir / f"{object_id}.bin", self._root)
        meta_path = assert_path_within_root(doc_dir / f"{object_id}.meta.json", self._root)
        bin_path.write_bytes(blob)
        meta_path.write_text(
            json.dumps(
                {
                    "document_id": str(document_id),
                    "object_id": str(object_id),
                    "media_type": media_type,
                    "filename": safe_name,
                    "byte_size": len(blob),
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return f"{self.SCHEME}://{document_id}/{object_id}"

    def get(self, storage_uri: str) -> bytes:
        path = self._resolve_bin(storage_uri)
        if not path.is_file():
            raise DocumentProcessingError(
                DOC_INTERNAL,
                "Stored document blob not found",
                details={"storage_uri": storage_uri},
            )
        return path.read_bytes()

    def delete(self, storage_uri: str) -> None:
        bin_path = self._resolve_bin(storage_uri)
        meta_path = bin_path.with_suffix(".meta.json")
        if bin_path.is_file():
            bin_path.unlink()
        if meta_path.is_file():
            meta_path.unlink()

    def _resolve_bin(self, storage_uri: str) -> Path:
        prefix = f"{self.SCHEME}://"
        if not storage_uri.startswith(prefix):
            raise DocumentProcessingError(DOC_PATH_TRAVERSAL, "Unsupported storage URI scheme")
        remainder = storage_uri[len(prefix) :]
        parts = remainder.split("/")
        if len(parts) != 2 or ".." in parts or not parts[0] or not parts[1]:
            raise DocumentProcessingError(DOC_PATH_TRAVERSAL, "Malformed storage URI")
        document_id, object_id = parts
        candidate = self._root / document_id / f"{object_id}.bin"
        return assert_path_within_root(candidate, self._root)
