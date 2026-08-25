"""Document byte storage port and local filesystem implementation."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

from nova.domain.errors import PayloadTooLargeError, StorageError, ValidationFailedError

_UNSAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_FILENAME_LEN = 200


def safe_filename(name: str | None, *, fallback: str = "document.bin") -> str:
    """Return a filesystem-safe basename (no path separators or traversal)."""
    raw = (name or "").strip() or fallback
    # Drop any directory components first.
    basenamed = Path(raw).name
    cleaned = _UNSAFE_NAME.sub("_", basenamed).strip("._")
    if not cleaned or cleaned in {".", ".."}:
        cleaned = fallback
    if len(cleaned) > _MAX_FILENAME_LEN:
        stem = Path(cleaned).stem[: _MAX_FILENAME_LEN - 20]
        suffix = Path(cleaned).suffix[:20]
        cleaned = f"{stem}{suffix}" or fallback
    return cleaned


class DocumentStoragePort(ABC):
    """Abstract storage for document bytes."""

    @abstractmethod
    def store(
        self,
        *,
        relative_path: str,
        data: bytes,
        max_bytes: int | None = None,
    ) -> str:
        """Persist bytes under a relative path. Returns a storage URI."""

    @abstractmethod
    def retrieve(self, relative_path: str) -> bytes:
        """Return stored bytes for a relative path. Raises if missing/unsafe."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Return True if the relative path already exists."""

    @abstractmethod
    def ping(self) -> bool:
        """Return True if the storage root is usable."""


class LocalFilesystemDocumentStorage(DocumentStoragePort):
    """Local disk storage with path-traversal protection and no overwrite."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def _resolve_safe(self, relative_path: str) -> Path:
        if not relative_path or relative_path.startswith(("/", "\\")):
            raise ValidationFailedError(
                "Storage path must be relative.",
                code="INVALID_STORAGE_PATH",
                details={"relative_path": relative_path},
            )
        candidate = (self._root / relative_path).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise ValidationFailedError(
                "Path traversal is not allowed.",
                code="INVALID_STORAGE_PATH",
                details={"relative_path": relative_path},
            ) from exc
        return candidate

    def store(
        self,
        *,
        relative_path: str,
        data: bytes,
        max_bytes: int | None = None,
    ) -> str:
        if max_bytes is not None and len(data) > max_bytes:
            raise PayloadTooLargeError(
                f"Uploaded document exceeds the maximum allowed size of {max_bytes} bytes.",
                details={"max_bytes": max_bytes, "actual_bytes": len(data)},
            )
        target = self._resolve_safe(relative_path)
        if target.exists():
            raise StorageError(
                "Refusing to overwrite existing stored object.",
                code="STORAGE_OVERWRITE_REFUSED",
                details={"relative_path": relative_path},
            )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as exc:
            raise StorageError(
                "Failed to write document bytes to storage.",
                details={"relative_path": relative_path},
            ) from exc
        return f"file://{target}"

    def retrieve(self, relative_path: str) -> bytes:
        target = self._resolve_safe(relative_path)
        if not target.is_file():
            raise StorageError(
                "Stored document was not found.",
                code="STORAGE_OBJECT_NOT_FOUND",
                details={"relative_path": relative_path},
            )
        try:
            return target.read_bytes()
        except OSError as exc:
            raise StorageError(
                "Failed to read document bytes from storage.",
                details={"relative_path": relative_path},
            ) from exc

    def exists(self, relative_path: str) -> bool:
        try:
            return self._resolve_safe(relative_path).exists()
        except ValidationFailedError:
            return False

    def ping(self) -> bool:
        try:
            if not self._root.exists() or not self._root.is_dir():
                return False
            probe = self._root / ".nova_write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True
        except OSError:
            return False
