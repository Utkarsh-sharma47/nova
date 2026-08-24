"""Document intake validation: extension, MIME, size, and integrity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath

from nova.documents.errors import (
    DOC_CORRUPT,
    DOC_EMPTY,
    DOC_MIME_MISMATCH,
    DOC_PAYLOAD_TOO_LARGE,
    DOC_UNSUPPORTED_EXTENSION,
    DOC_UNSUPPORTED_MEDIA_TYPE,
    DocumentProcessingError,
)
from nova.documents.limits import (
    DEFAULT_LIMITS,
    EXTENSION_TO_MEDIA_TYPE,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_MEDIA_TYPES,
    DocumentLimits,
)
from nova.documents.security import sanitize_filename
from nova.documents.sniffing import detect_media_type, is_pdf_header_intact


@dataclass(frozen=True, slots=True)
class ValidatedDocument:
    blob: bytes
    detected_media_type: str
    declared_media_type: str | None
    original_filename: str | None
    sanitized_filename: str | None
    byte_size: int
    content_sha256: str
    extension: str | None


def _extension_of(filename: str | None) -> str | None:
    if not filename:
        return None
    suffix = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    return suffix or None


def validate_document(
    blob: bytes,
    *,
    declared_media_type: str | None = None,
    original_filename: str | None = None,
    limits: DocumentLimits = DEFAULT_LIMITS,
) -> ValidatedDocument:
    if not blob:
        raise DocumentProcessingError(DOC_EMPTY, "Document blob is empty")
    byte_size = len(blob)
    if byte_size > limits.max_bytes:
        raise DocumentProcessingError(
            DOC_PAYLOAD_TOO_LARGE,
            f"Document exceeds max size of {limits.max_bytes} bytes",
            details={"byte_size": byte_size, "max_bytes": limits.max_bytes},
        )
    sanitized = sanitize_filename(original_filename, limits=limits)
    extension = _extension_of(sanitized)
    if extension is not None and extension not in SUPPORTED_EXTENSIONS:
        raise DocumentProcessingError(
            DOC_UNSUPPORTED_EXTENSION,
            f"Unsupported file extension: {extension}",
            details={"extension": extension},
        )
    detected = detect_media_type(blob)
    if detected not in SUPPORTED_MEDIA_TYPES:
        raise DocumentProcessingError(
            DOC_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported media type: {detected}",
            details={"detected_media_type": detected},
        )
    if declared_media_type:
        declared = declared_media_type.split(";")[0].strip().lower()
        if declared and declared not in SUPPORTED_MEDIA_TYPES:
            raise DocumentProcessingError(
                DOC_UNSUPPORTED_MEDIA_TYPE,
                f"Declared media type is not supported: {declared}",
                details={"declared_media_type": declared},
            )
        if declared and declared != detected:
            raise DocumentProcessingError(
                DOC_MIME_MISMATCH,
                "Declared media type does not match detected content type",
                details={"declared_media_type": declared, "detected_media_type": detected},
            )
    if extension is not None:
        expected = EXTENSION_TO_MEDIA_TYPE.get(extension)
        if expected is not None and expected != detected:
            raise DocumentProcessingError(
                DOC_MIME_MISMATCH,
                "File extension does not match detected content type",
                details={
                    "extension": extension,
                    "detected_media_type": detected,
                    "expected_media_type": expected,
                },
            )
    if detected == "application/pdf" and not is_pdf_header_intact(blob):
        raise DocumentProcessingError(
            DOC_CORRUPT,
            "PDF failed basic integrity checks (missing header or EOF marker)",
        )
    digest = hashlib.sha256(blob).hexdigest()
    return ValidatedDocument(
        blob=blob,
        detected_media_type=detected,
        declared_media_type=declared_media_type,
        original_filename=original_filename,
        sanitized_filename=sanitized,
        byte_size=byte_size,
        content_sha256=digest,
        extension=extension,
    )
