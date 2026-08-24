"""Configuration validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nova.config import Settings, clear_settings_cache


@pytest.fixture(autouse=True)
def _clear_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    yield
    clear_settings_cache()


def test_settings_require_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_settings_reject_empty_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="   ", _env_file=None)  # type: ignore[call-arg]


def test_settings_reject_url_without_scheme() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="nova:nova@localhost/nova", _env_file=None)  # type: ignore[call-arg]


def test_settings_accept_valid_url() -> None:
    settings = Settings(  # type: ignore[call-arg]
        database_url="postgresql+psycopg://nova:nova@localhost:5432/nova",
        environment="test",
        _env_file=None,
    )
    assert settings.environment == "test"
    assert "postgresql+psycopg://" in settings.database_url


def test_settings_reject_invalid_log_level() -> None:
    with pytest.raises(ValidationError):
        Settings(  # type: ignore[call-arg]
            database_url="postgresql+psycopg://nova:nova@localhost:5432/nova",
            log_level="VERBOSE",  # type: ignore[arg-type]
            _env_file=None,
        )
