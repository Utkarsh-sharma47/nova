"""Repository integration tests."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nova.persistence.repositories import (
    CustomerRepository,
    DocumentRepository,
    DocumentVersionRepository,
    IdempotencyRepository,
    ShipmentRepository,
    VerificationRunRepository,
)

pytestmark = pytest.mark.integration


@pytest.fixture()
async def session() -> AsyncIterator[AsyncSession]:
    url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://nova:nova@localhost:5432/nova_test",
    )
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"PostgreSQL unavailable: {exc}")

    from alembic import command
    from alembic.config import Config

    os.environ["DATABASE_URL"] = url
    command.upgrade(Config("alembic.ini"), "head")

    factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as sess:
        yield sess
        await sess.rollback()

    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE idempotency_records, verification_runs, document_versions, "
                "documents, shipments, customers RESTART IDENTITY CASCADE"
            )
        )
    await engine.dispose()


@pytest.mark.asyncio
async def test_customer_shipment_document_roundtrip(session: AsyncSession) -> None:
    customers = CustomerRepository(session)
    shipments = ShipmentRepository(session)
    documents = DocumentRepository(session)
    versions = DocumentVersionRepository(session)
    runs = VerificationRunRepository(session)
    idem = IdempotencyRepository(session)

    customer = await customers.create(name="Acme Shipping")
    shipment = await shipments.create(customer_id=customer.customer_id)
    document = await documents.create(
        shipment_id=shipment.shipment_id,
        document_type="other",
        status="received",
        external_ref=f"ref-{uuid4().hex[:8]}",
    )
    version = await versions.create(
        document_id=document.document_id,
        shipment_id=shipment.shipment_id,
        document_type="other",
        version_number=1,
        storage_uri="file:///tmp/x",
        content_sha256="a" * 64,
        media_type="text/plain",
        byte_size=4,
        ingestion_idempotency_key=f"idem-{uuid4().hex[:10]}",
    )
    await documents.set_current_version(document, version.document_version_id)
    run = await runs.create(
        shipment_id=shipment.shipment_id,
        document_version_ids=[version.document_version_id],
        status="queued",
    )
    record = await idem.create(
        principal_hash="abc",
        idempotency_key=f"key-{uuid4().hex[:10]}",
        request_fingerprint="fp",
        document_id=document.document_id,
        shipment_id=shipment.shipment_id,
        verification_run_id=run.verification_run_id,
        response_json={"status": "ACCEPTED"},
    )
    await session.commit()

    fetched = await customers.get(customer.customer_id)
    assert fetched is not None
    assert fetched.name == "Acme Shipping"
    found = await idem.get(principal_hash="abc", idempotency_key=record.idempotency_key)
    assert found is not None
    assert found.document_id == document.document_id
