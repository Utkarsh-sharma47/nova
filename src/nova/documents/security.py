"""Security helpers for filenames and storage paths."""

from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

from nova.documents.errors import (
    DOC_INVALID_FILENAME,
    DOC_PATH_TRAVERSAL,
    DocumentProcessingError,
)
from nova.documents.limits import DEFAULT_LIMITS, DocumentLimits

_UNSAFE_FILENAME_CHARS = re.compile(r"[^\w.\- ]+", re.UNICODE)
_RESERVED_WINDOWS = frozenset(
    {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)


def sanitize_filename(
    filename: str | None,
    *,
    limits: DocumentLimits = DEFAULT_LIMITS,
) -> str | None:
    if filename is None:
        return None
    if "\x00" in filename:
        raise DocumentProcessingError(DOC_INVALID_FILENAME, "Filename contains a null byte")
    stripped = filename.strip()
    if not stripped:
        raise DocumentProcessingError(DOC_INVALID_FILENAME, "Filename is empty")
    posix_name = PurePosixPath(stripped.replace("\\", "/")).name
    win_name = PureWindowsPath(stripped).name
    basename = posix_name if len(posix_name) <= len(win_name) else win_name
    basename = os.path.basename(basename)
    if not basename or basename in {".", ".."}:
        raise DocumentProcessingError(
            DOC_PATH_TRAVERSAL, "Filename resolves to a path traversal or empty name"
        )
    if "/" in basename or "\\" in basename:
        raise DocumentProcessingError(
            DOC_PATH_TRAVERSAL, "Filename must not contain path separators after sanitization"
        )
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", basename).strip(" .")
    if not cleaned:
        raise DocumentProcessingError(
            DOC_INVALID_FILENAME, "Filename has no safe characters remaining"
        )
    stem, dot, _ext = cleaned.rpartition(".")
    check = (stem if dot else cleaned).upper()
    if check in _RESERVED_WINDOWS:
        cleaned = f"_{cleaned}"
    if len(cleaned) > limits.max_filename_length:
        raise DocumentProcessingError(
            DOC_INVALID_FILENAME,
            f"Filename exceeds max length of {limits.max_filename_length}",
            details={"max_filename_length": limits.max_filename_length},
        )
    return cleaned


def assert_path_within_root(path: Path, root: Path) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise DocumentProcessingError(
            DOC_PATH_TRAVERSAL, "Resolved path escapes storage root"
        ) from exc
    return resolved
