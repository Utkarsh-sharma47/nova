#!/usr/bin/env python3
"""Lightweight document-processing benchmark (informational)."""

from __future__ import annotations

import resource
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from nova.documents.service import DocumentProcessingService, process_document  # noqa: E402
from tests.documents.fixtures import make_digital_pdf, make_text_invoice  # noqa: E402


def _rss_kb() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def main() -> None:
    service = DocumentProcessingService()
    print("nova document processing benchmark")
    print(f"processor_version={service.processor_version}")
    print(f"rss_kb_start={_rss_kb()}")

    workloads: list[tuple[str, bytes]] = [
        ("text_invoice", make_text_invoice()),
        ("pdf_1page", make_digital_pdf(pages=1)),
        ("pdf_3page", make_digital_pdf(pages=3)),
        ("pdf_5page", make_digital_pdf(pages=5)),
    ]

    print("name,bytes,status,duration_ms,rss_kb")
    for name, blob in workloads:
        started = time.perf_counter()
        result = process_document(
            blob,
            document_id=uuid4(),
            original_filename="bench.pdf" if name.startswith("pdf") else "bench.txt",
            service=service,
        )
        duration_ms = (time.perf_counter() - started) * 1000
        print(
            f"{name},{len(blob)},{result.status.value},"
            f"{duration_ms:.3f},{_rss_kb()}"
        )


if __name__ == "__main__":
    main()
