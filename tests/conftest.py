"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure settings can load during collection for non-integration tests.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://nova:nova@localhost:5432/nova_test",
)
os.environ.setdefault("API_AUTH_TOKEN", "test-token-not-for-production")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DOCUMENT_STORAGE_PATH", "./data/uploads-test")


@pytest.fixture()
def auth_token() -> str:
    return os.environ["API_AUTH_TOKEN"]


@pytest.fixture()
def tmp_storage_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setenv("DOCUMENT_STORAGE_PATH", str(root))
    from nova.config import clear_settings_cache

    clear_settings_cache()
    return root


@pytest.fixture()
def settings(tmp_storage_dir: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["DATABASE_URL"])
    monkeypatch.setenv("API_AUTH_TOKEN", os.environ["API_AUTH_TOKEN"])
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DOCUMENT_STORAGE_PATH", str(tmp_storage_dir))
    from nova.config import Settings, clear_settings_cache

    clear_settings_cache()
    return Settings()  # type: ignore[call-arg]


@pytest.fixture()
def test_database_url() -> str:
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://nova:nova@localhost:5432/nova_test",
    )


@pytest.fixture()
async def db_engine(test_database_url: str):
    engine = create_async_engine(test_database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
    except Exception as exc:  # pragma: no cover - environment dependent
        await engine.dispose()
        pytest.skip(f"PostgreSQL unavailable at {test_database_url}: {exc}")
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture()
def unique_suffix() -> str:
    return uuid4().hex[:8]


@pytest.fixture()
def clear_settings() -> Iterator[None]:
    from nova.config import clear_settings_cache

    clear_settings_cache()
    yield
    clear_settings_cache()
