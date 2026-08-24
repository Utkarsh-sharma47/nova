"""Environment-backed application configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_PLACEHOLDER_TOKENS = {
    "change-me",
    "changeme",
    "example",
    "replace-me",
    "your-api-key",
    "your-token-here",
}


class Settings(BaseSettings):
    """Validated runtime settings. Secrets are read from the environment only."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_env: str = Field(
        default="local",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    log_level: str = "INFO"
    service_name: str = "nova-api"
    database_url: str = "postgresql+psycopg://nova:nova@localhost:5432/nova"
    api_auth_token: str | None = None
    document_storage_path: str = "./var/documents"
    max_document_size_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    allowed_mime_types: Annotated[tuple[str, ...], NoDecode] = (
        "application/pdf",
        "text/plain",
    )
    database_connect_timeout_seconds: int = Field(default=5, ge=1, le=60)
    llm_provider: str = "mock"
    llm_model: str | None = None
    llm_api_key: str | None = None

    @field_validator("allowed_mime_types", mode="before")
    @classmethod
    def parse_mime_types(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("invalid log level")
        return normalized

    @field_validator("api_auth_token")
    @classmethod
    def require_non_test_token(cls, value: str | None, info: object) -> str | None:
        # Cross-field enforcement is performed at app startup to keep test construction simple.
        if value == "":
            return None
        return value

    def validate_runtime(self) -> None:
        if self.app_env.lower() in {"test", "testing"}:
            return
        if not self.api_auth_token:
            raise ValueError("API_AUTH_TOKEN is required outside test environments")
        normalized = self.api_auth_token.strip().lower()
        if (
            normalized in _PLACEHOLDER_TOKENS
            or normalized.startswith("${")
            or (normalized.startswith("<") and normalized.endswith(">"))
        ):
            raise ValueError("API_AUTH_TOKEN must not be a placeholder")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
