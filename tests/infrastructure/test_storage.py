"""Local filesystem storage security tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from nova.domain.errors import PayloadTooLargeError, StorageError, ValidationFailedError
from nova.infrastructure.storage import LocalFilesystemDocumentStorage, safe_filename


def test_safe_filename_strips_path_components() -> None:
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("invoice.pdf") == "invoice.pdf"
    assert ".." not in safe_filename("a/../b")


def test_safe_filename_rejects_empty() -> None:
    assert safe_filename("...") == "document.bin"
    assert safe_filename(None) == "document.bin"


def test_store_and_reject_overwrite(tmp_path: Path) -> None:
    storage = LocalFilesystemDocumentStorage(tmp_path)
    uri = storage.store(relative_path="a/b.txt", data=b"hello")
    assert uri.startswith("file://")
    assert (tmp_path / "a" / "b.txt").read_bytes() == b"hello"
    with pytest.raises(StorageError) as exc:
        storage.store(relative_path="a/b.txt", data=b"other")
    assert exc.value.code == "STORAGE_OVERWRITE_REFUSED"


def test_path_traversal_rejected(tmp_path: Path) -> None:
    storage = LocalFilesystemDocumentStorage(tmp_path)
    with pytest.raises(ValidationFailedError):
        storage.store(relative_path="../escape.txt", data=b"x")


def test_absolute_path_rejected(tmp_path: Path) -> None:
    storage = LocalFilesystemDocumentStorage(tmp_path)
    with pytest.raises(ValidationFailedError):
        storage.store(relative_path="/tmp/evil.txt", data=b"x")


def test_size_limit(tmp_path: Path) -> None:
    storage = LocalFilesystemDocumentStorage(tmp_path)
    with pytest.raises(PayloadTooLargeError):
        storage.store(relative_path="big.bin", data=b"12345", max_bytes=3)


def test_ping(tmp_path: Path) -> None:
    storage = LocalFilesystemDocumentStorage(tmp_path)
    assert storage.ping() is True
