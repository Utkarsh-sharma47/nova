"""Configurable limits for document intake and processing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentLimits:
    """Hard limits applied before and during document processing."""

    max_bytes: int = 10 * 1024 * 1024  # 10 MiB
    max_pages: int = 100
    max_filename_length: int = 255
    max_pdf_objects: int = 50_000


DEFAULT_LIMITS = DocumentLimits()

SUPPORTED_MEDIA_TYPES: frozenset[str] = frozenset({"application/pdf", "text/plain"})
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".txt"})
EXTENSION_TO_MEDIA_TYPE: dict[str, str] = {".pdf": "application/pdf", ".txt": "text/plain"}
PROCESSOR_PACKAGE_VERSION = "1.0.0"
