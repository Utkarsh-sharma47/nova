#!/usr/bin/env python3
"""Local baseline timings for the Part 1 pipeline (MockLLM; not a production SLO)."""

from __future__ import annotations

import statistics
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from nova.api.app import create_app
from nova.application.pipeline import PipelineOrchestrator
from nova.application.extraction import build_default_llm
from nova.config import Settings
from nova.extraction.service import ExtractorService
from nova.infrastructure.storage import LocalFilesystemStorage
from nova.persistence.database import get_engine, session_scope
from nova.persistence.models import Base, Customer


AUTH = {"X-API-Key": "nova-bench-token"}
INVOICE = (
    b"Invoice Number: INV-42\nInvoice Date: 2026-02-01\nSeller: Acme Trading\n"
    b"Buyer: Globex Corp\nCurrency: USD\nTotal Amount: 1250.00\n"
)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        settings = Settings(
            app_env="test",
            api_auth_token="nova-bench-token",
            database_url=f"sqlite:///{root / 'bench.db'}",
            document_storage_path=str(root / "documents"),
            llm_provider="mock",
        )
        totals: list[int] = []
        extractions: list[int] = []
        validations: list[int] = []
        routings: list[int] = []
        with TestClient(create_app(settings)) as client:
            Base.metadata.create_all(get_engine())
            customer_id = uuid4()
            with session_scope() as session:
                session.add(Customer(customer_id=customer_id, name="Bench", status="active"))
            for i in range(5):
                resp = client.post(
                    "/v1/documents",
                    headers={**AUTH, "Idempotency-Key": f"bench-key-{i:04d}"},
                    data={"customer_id": str(customer_id), "document_type": "INVOICE"},
                    files={"file": ("inv.txt", INVOICE, "text/plain")},
                )
                resp.raise_for_status()
                body = resp.json()
                storage = LocalFilesystemStorage(str(root / "documents"))
                with session_scope() as session:
                    result = PipelineOrchestrator(
                        session,
                        storage,
                        extractor=ExtractorService(build_default_llm("mock", None, None)),
                        auto_commit=False,
                    ).run(
                        document_id=__import__("uuid").UUID(body["document_id"]),
                        verification_run_id=__import__("uuid").UUID(body["run_id"]),
                        trace_id=uuid4(),
                    )
                    # First call completed pipeline; replay timings are near-zero.
                    # Capture from first ingest by reading agent rows is harder;
                    # re-ingest unique keys above already ran pipeline once.
                    # Use response path: re-run only for structure; collect from
                    # a fresh document each iteration via a second local run.
                    _ = result

            # Dedicated measured runs
            for i in range(5):
                resp = client.post(
                    "/v1/documents",
                    headers={**AUTH, "Idempotency-Key": f"bench-meas-{i:04d}"},
                    data={"customer_id": str(customer_id), "document_type": "INVOICE"},
                    files={"file": ("inv.txt", INVOICE, "text/plain")},
                )
                resp.raise_for_status()
                # Pipeline already ran during ingest; timings were logged.
                # Re-seed measured orchestrator path with skip_if_decided false not available;
                # report ingest-side by constructing orchestrator on fresh seeded docs.
            from nova.persistence.models import Document, DocumentVersion, Shipment, VerificationRun

            for i in range(5):
                with session_scope() as session:
                    shipment = Shipment(customer_id=customer_id, status="open")
                    session.add(shipment)
                    session.flush()
                    document_id = uuid4()
                    version_id = uuid4()
                    run_id = uuid4()
                    storage = LocalFilesystemStorage(str(root / "documents"))
                    uri = storage.put(document_id, version_id, "inv.txt", INVOICE)
                    session.add(
                        Document(
                            document_id=document_id,
                            shipment_id=shipment.shipment_id,
                            document_type="commercial_invoice",
                            status="content_available",
                            ingestion_channel="upload",
                            current_version_id=version_id,
                        )
                    )
                    session.flush()
                    session.add(
                        DocumentVersion(
                            document_version_id=version_id,
                            document_id=document_id,
                            shipment_id=shipment.shipment_id,
                            document_type="commercial_invoice",
                            version_number=1,
                            storage_uri=uri,
                            content_sha256=f"{i:064d}"[:64].replace(" ", "0"),
                            media_type="text/plain",
                            byte_size=len(INVOICE),
                            original_filename="inv.txt",
                        )
                    )
                    session.add(
                        VerificationRun(
                            verification_run_id=run_id,
                            shipment_id=shipment.shipment_id,
                            status="queued",
                            trigger="bench",
                            document_version_ids=[str(version_id)],
                        )
                    )
                    session.flush()
                    out = PipelineOrchestrator(
                        session,
                        storage,
                        extractor=ExtractorService(build_default_llm("mock", None, None)),
                        auto_commit=False,
                    ).run(document_id=document_id, verification_run_id=run_id, trace_id=uuid4())
                    totals.append(out.timings.total_ms)
                    extractions.append(out.timings.extraction_ms)
                    validations.append(out.timings.validation_ms)
                    routings.append(out.timings.routing_ms)

        def fmt(name: str, values: list[int]) -> str:
            return (
                f"{name}: n={len(values)} mean={statistics.mean(values):.1f}ms "
                f"p50={statistics.median(values):.1f}ms max={max(values)}ms"
            )

        print("Nova Phase 7 pipeline local baseline (MockLLM, SQLite)")
        print(fmt("total", totals))
        print(fmt("extraction", extractions))
        print(fmt("validation", validations))
        print(fmt("routing", routings))
        print("Note: local baseline only — not a production latency claim.")


if __name__ == "__main__":
    main()
