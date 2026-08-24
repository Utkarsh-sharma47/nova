"""Environment-based application configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    database_url: str = Field(
        ...,
        description="SQLAlchemy async URL, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )

    api_auth_token: str = Field(
        ...,
        min_length=8,
        description="Shared Part 1 API token (Bearer / X-API-Key).",
    )

    document_storage_path: str = Field(default="./data/uploads")
    max_document_size_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    allowed_document_types: str = Field(
        default="application/pdf,image/png,image/jpeg,image/tiff,text/plain",
        description="Comma-separated MIME allow-list",
    )

    llm_provider: str = Field(default="mock")
    llm_model: str = Field(default="")
    llm_api_key: str = Field(default="")

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("DATABASE_URL must not be empty")
        if not (
            normalized.startswith("postgresql+asyncpg://")
            or normalized.startswith("postgresql+psycopg://")
            or normalized.startswith("postgresql://")
        ):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL URL "
                "(postgresql+asyncpg:// recommended for the API)"
            )
        return normalized

    @field_validator("api_auth_token")
    @classmethod
    def _reject_placeholder_token(cls, value: str) -> str:
        token = value.strip()
        if token in {"change-me", "change-me-generate-locally", "changeme", "secret"}:
            raise ValueError("API_AUTH_TOKEN must be set to a non-placeholder value")
        return token

    @model_validator(mode="after")
    def _normalize_async_url(self) -> Settings:
        url = self.database_url
        if url.startswith("postgresql://"):
            object.__setattr__(
                self, "database_url", url.replace("postgresql://", "postgresql+asyncpg://", 1)
            )
        elif url.startswith("postgresql+psycopg://"):
            object.__setattr__(
                self,
                "database_url",
                url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1),
            )
        return self

    @property
    def allowed_mime_types(self) -> frozenset[str]:
        parts = [p.strip().lower() for p in self.allowed_document_types.split(",") if p.strip()]
        if not parts:
            raise ValueError("ALLOWED_DOCUMENT_TYPES must include at least one MIME type")
        return frozenset(parts)

    @property
    def sync_database_url(self) -> str:
        """Sync URL for Alembic (psycopg3)."""
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
