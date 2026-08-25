"""MIME sniffing from magic bytes — do not trust extensions alone."""

from __future__ import annotations

from nova.documents.errors import DOC_CORRUPT, DOC_EMPTY, DocumentProcessingError


def detect_media_type(blob: bytes) -> str:
    if not blob:
        raise DocumentProcessingError(DOC_EMPTY, "Document blob is empty")
    if blob.startswith(b"%PDF"):
        return "application/pdf"
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if blob.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if b"\x00" in blob[:8192]:
        raise DocumentProcessingError(
            DOC_CORRUPT, "Binary content does not match a supported media type"
        )
    try:
        blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentProcessingError(
            DOC_CORRUPT,
            "Content is not valid UTF-8 text and is not a recognized binary type",
        ) from exc
    return "text/plain"


def is_pdf_header_intact(blob: bytes) -> bool:
    if not blob.startswith(b"%PDF"):
        return False
    tail = blob[-1024:] if len(blob) > 1024 else blob
    return b"%%EOF" in tail
