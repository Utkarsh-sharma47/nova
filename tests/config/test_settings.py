"""Settings validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nova.config import Settings, clear_settings_cache


def test_settings_normalizes_postgresql_url(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("DATABASE_URL", "postgresql://nova:nova@localhost:5432/nova")
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token-not-for-production")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.sync_database_url.startswith("postgresql+psycopg://")


def test_settings_rejects_placeholder_token(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://nova:nova@localhost:5432/nova")
    monkeypatch.setenv("API_AUTH_TOKEN", "change-me")
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_settings_rejects_non_postgres_url(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp.db")
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token-not-for-production")
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_allowed_mime_types_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://nova:nova@localhost:5432/nova")
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token-not-for-production")
    monkeypatch.setenv("ALLOWED_DOCUMENT_TYPES", "application/pdf, text/plain")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.allowed_mime_types == frozenset({"application/pdf", "text/plain"})


def test_max_document_size_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://nova:nova@localhost:5432/nova")
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token-not-for-production")
    monkeypatch.delenv("MAX_DOCUMENT_SIZE_BYTES", raising=False)
    monkeypatch.setenv("MAX_DOCUMENT_SIZE", "2048")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.max_document_size_bytes == 2048
