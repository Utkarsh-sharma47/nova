"""Environment-based application configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str = Field(default="nova-api", alias="SERVICE_NAME")
    environment: Literal["local", "test", "ci", "demo", "production"] = Field(
        default="local",
        alias="ENVIRONMENT",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
        description="SQLAlchemy URL, e.g. postgresql+psycopg://nova:nova@db:5432/nova",
    )
    database_connect_timeout_seconds: float = Field(
        default=5.0,
        alias="DATABASE_CONNECT_TIMEOUT_SECONDS",
        gt=0,
        le=60,
    )

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT", ge=1, le=65535)
    api_auth_token: str | None = Field(default=None, alias="API_AUTH_TOKEN")

    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("DATABASE_URL must not be empty")
        if "://" not in cleaned:
            raise ValueError("DATABASE_URL must be a SQLAlchemy URL with a scheme")
        return cleaned

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings. Clear cache in tests via `get_settings.cache_clear()`."""
    return Settings()  # type: ignore[call-arg]


def clear_settings_cache() -> None:
    get_settings.cache_clear()
