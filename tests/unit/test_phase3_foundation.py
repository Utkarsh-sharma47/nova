from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from nova.config import Settings
from nova.documents import DigitalPdfAdapter, DocumentLimits, validate_document
from nova.documents.errors import (
    DOC_CORRUPT,
    DOC_PAYLOAD_TOO_LARGE,
    DOC_UNSUPPORTED_EXTENSION,
    DocumentProcessingError,
)
from nova.domain.errors import InvalidLifecycleTransition, UnsafeFilename
from nova.domain.lifecycle import (
    DocumentStatus,
    VerificationRunStatus,
    assert_document_transition,
    assert_run_transition,
)
from nova.infrastructure.storage import LocalFilesystemStorage, safe_filename


def test_config_parses_environment_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ALLOWED_MIME_TYPES", "application/pdf,text/plain")
    settings = Settings()
    assert settings.app_env == "test"
    assert settings.allowed_mime_types == ("application/pdf", "text/plain")


def test_non_test_runtime_requires_auth_token() -> None:
    with pytest.raises(ValueError, match="API_AUTH_TOKEN"):
        Settings(app_env="production", api_auth_token=None).validate_runtime()


def test_non_test_runtime_rejects_placeholder_auth_token() -> None:
    with pytest.raises(ValueError, match="placeholder"):
        Settings(app_env="production", api_auth_token="change-me").validate_runtime()


def test_lifecycle_allows_forward_transitions_and_rejects_terminal() -> None:
    assert_document_transition(
        DocumentStatus.REGISTERED,
        DocumentStatus.CONTENT_AVAILABLE,
    )
    assert_run_transition(VerificationRunStatus.QUEUED, VerificationRunStatus.RUNNING)
    with pytest.raises(InvalidLifecycleTransition):
        assert_document_transition(
            DocumentStatus.WITHDRAWN,
            DocumentStatus.CONTENT_AVAILABLE,
        )


@pytest.mark.parametrize("name", ["../secret.pdf", "/etc/passwd", r"..\secret.pdf", "..", ""])
def test_storage_rejects_path_traversal(name: str) -> None:
    with pytest.raises(UnsafeFilename):
        safe_filename(name)


def test_storage_writes_below_root(tmp_path: Path) -> None:
    storage = LocalFilesystemStorage(tmp_path)
    uri = storage.put(uuid4(), uuid4(), "safe.txt", b"hello")
    stored_path = Path(uri.removeprefix("file://"))
    assert stored_path.read_bytes() == b"hello"
    storage.delete(uri)
    assert not stored_path.exists()

    staged = tmp_path / "staged.txt"
    staged.write_bytes(b"staged")
    assert storage.read_staged("staged.txt") == ("staged.txt", b"staged")
    with pytest.raises(UnsafeFilename):
        storage.read_staged("../outside.txt")


def test_validation_rejects_oversized_and_unsupported() -> None:
    with pytest.raises(DocumentProcessingError) as oversized:
        validate_document(
            b"too large",
            original_filename="x.txt",
            declared_media_type="text/plain",
            limits=DocumentLimits(max_bytes=2),
        )
    assert oversized.value.error_code == DOC_PAYLOAD_TOO_LARGE
    with pytest.raises(DocumentProcessingError) as unsupported:
        validate_document(
            b"\x89PNG\r\n",
            original_filename="x.png",
            declared_media_type="image/png",
        )
    assert unsupported.value.error_code == DOC_UNSUPPORTED_EXTENSION


def test_pdf_processor_rejects_corrupt_pdf() -> None:
    with pytest.raises(DocumentProcessingError) as corrupt:
        DigitalPdfAdapter().process(b"%PDF-not-valid", media_type="application/pdf")
    assert corrupt.value.error_code == DOC_CORRUPT
