"""Document blob storage port and local filesystem adapter."""

from __future__ import annotations

import os
from pathlib import Path, PurePath
from typing import Protocol
from uuid import UUID

from nova.domain.errors import UnsafeFilename


class DocumentStoragePort(Protocol):
    def put(self, document_id: UUID, version_id: UUID, filename: str, blob: bytes) -> str:
        """Persist bytes and return a non-secret storage URI."""

    def delete(self, storage_uri: str) -> None:
        """Delete a previously persisted blob if it exists."""

    def is_writable(self) -> bool:
        """Return whether the backing store can accept writes."""

    def read_staged(self, source_path: str) -> tuple[str, bytes]:
        """Read a caller-selected file constrained beneath the storage root."""


def safe_filename(filename: str) -> str:
    if not filename or filename in {".", ".."}:
        raise UnsafeFilename()
    if "\x00" in filename or Path(filename).is_absolute():
        raise UnsafeFilename()
    pure = PurePath(filename)
    if len(pure.parts) != 1 or any(part in {".", ".."} for part in pure.parts):
        raise UnsafeFilename()
    sanitized = Path(filename).name
    if sanitized != filename or "/" in filename or "\\" in filename:
        raise UnsafeFilename()
    return sanitized


class LocalFilesystemStorage:
    """Atomic local storage constrained beneath one configured root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def put(self, document_id: UUID, version_id: UUID, filename: str, blob: bytes) -> str:
        name = safe_filename(filename)
        destination = (self.root / str(document_id) / str(version_id) / name).resolve()
        if not destination.is_relative_to(self.root):
            raise UnsafeFilename()
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(blob)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        return destination.as_uri()

    def delete(self, storage_uri: str) -> None:
        prefix = "file://"
        if not storage_uri.startswith(prefix):
            raise UnsafeFilename("The storage URI is unsafe.")
        destination = Path(storage_uri.removeprefix(prefix)).resolve()
        if not destination.is_relative_to(self.root):
            raise UnsafeFilename("The storage URI is unsafe.")
        destination.unlink(missing_ok=True)
        for parent in (destination.parent, destination.parent.parent):
            try:
                parent.rmdir()
            except OSError:
                break

    def is_writable(self) -> bool:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            probe = self.root / ".nova-write-probe"
            probe.write_bytes(b"")
            probe.unlink()
        except OSError:
            return False
        return True

    def read_staged(self, source_path: str) -> tuple[str, bytes]:
        if not source_path or "\x00" in source_path or Path(source_path).is_absolute():
            raise UnsafeFilename("The source path is unsafe.")
        candidate = (self.root / source_path).resolve()
        if not candidate.is_relative_to(self.root) or not candidate.is_file():
            raise UnsafeFilename("The source path is unsafe or unavailable.")
        return safe_filename(candidate.name), candidate.read_bytes()
