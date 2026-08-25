from __future__ import annotations

import os
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from nova.application.ingestion import IngestCommand, IngestionService
from nova.infrastructure.storage import LocalFilesystemStorage
from nova.persistence.models import Customer


@pytest.mark.integration
def test_migrations_upgrade_clean_database_and_are_repeatable() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    environment = {**os.environ, "DATABASE_URL": database_url, "APP_ENV": "test"}
    subprocess.run(["alembic", "downgrade", "base"], check=True, env=environment)
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=environment)
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=environment)
    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert {
        "customers",
        "shipments",
        "documents",
        "document_versions",
        "verification_runs",
        "idempotency_records",
        "decisions",
    } <= tables


@pytest.mark.integration
def test_ingestion_uses_migrated_postgresql_schema(tmp_path: Path) -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    engine = create_engine(database_url)
    customer_id = uuid4()
    with Session(engine) as session:
        session.add(Customer(customer_id=customer_id, name="Integration", status="active"))
        session.commit()
        service = IngestionService(
            session,
            LocalFilesystemStorage(tmp_path),
            max_document_size_bytes=1024,
            allowed_mime_types=("text/plain",),
        )
        response = service.ingest(
            IngestCommand(
                blob=b"invoice",
                filename="invoice.txt",
                media_type="text/plain",
                customer_id=customer_id,
                shipment_id=None,
                document_type="INVOICE",
                external_ref=None,
                idempotency_key="postgres-ingest-0001",
                principal="integration",
                trace_id=str(uuid4()),
            )
        )
    assert response["status"] == "ACCEPTED"
