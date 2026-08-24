"""Alembic migration smoke tests."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.integration


@pytest.fixture()
async def migrated_url() -> AsyncIterator[str]:
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
    await engine.dispose()

    from alembic import command
    from alembic.config import Config

    os.environ["DATABASE_URL"] = url
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield url


@pytest.mark.asyncio
async def test_phase3_tables_exist(migrated_url: str) -> None:
    engine = create_async_engine(migrated_url, pool_pre_ping=True)
    expected = {
        "customers",
        "shipments",
        "documents",
        "document_versions",
        "verification_runs",
        "idempotency_records",
    }
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename = ANY(:names)"
            ),
            {"names": list(expected)},
        )
        found = {row[0] for row in result.fetchall()}
    await engine.dispose()
    assert expected <= found


@pytest.mark.asyncio
async def test_document_status_check(migrated_url: str) -> None:
    engine = create_async_engine(migrated_url, pool_pre_ping=True)
    async with engine.connect() as conn:
        cust = await conn.execute(
            text(
                "INSERT INTO customers (name, status) VALUES ('mig', 'active') "
                "RETURNING customer_id"
            )
        )
        customer_id = cust.scalar_one()
        shp = await conn.execute(
            text(
                "INSERT INTO shipments (customer_id, status) VALUES (:c, 'open') "
                "RETURNING shipment_id"
            ),
            {"c": customer_id},
        )
        shipment_id = shp.scalar_one()
        with pytest.raises(DBAPIError):
            await conn.execute(
                text(
                    "INSERT INTO documents (shipment_id, document_type, status, "
                    "ingestion_channel) VALUES (:s, 'other', 'not_a_status', 'upload')"
                ),
                {"s": shipment_id},
            )
        await conn.rollback()
    await engine.dispose()
