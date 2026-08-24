"""FastAPI dependency wiring."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Iterator
from typing import Annotated, cast

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from nova.application.extraction import build_default_llm
from nova.application.ingestion import IngestionService
from nova.config import Settings
from nova.domain.errors import NovaError
from nova.extraction.service import ExtractorService
from nova.infrastructure.storage import LocalFilesystemStorage
from nova.persistence.database import get_session


class AuthenticationError(NovaError):
    code = "UNAUTHENTICATED"
    status_code = 401
    safe_message = "Valid API authentication is required."


def settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def authenticate(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    configured = settings(request).api_auth_token
    if configured is None and settings(request).app_env.lower() in {"test", "testing"}:
        configured = "nova-test-token"
    supplied = x_api_key
    if authorization and authorization.startswith("Bearer "):
        supplied = authorization.removeprefix("Bearer ").strip()
    if not configured or not supplied or not hmac.compare_digest(configured, supplied):
        raise AuthenticationError()
    return hashlib.sha256(configured.encode()).hexdigest()


def session_dependency() -> Iterator[Session]:
    yield from get_session()


def ingestion_service(
    request: Request,
    session: Annotated[Session, Depends(session_dependency)],
) -> IngestionService:
    app_settings = settings(request)
    storage = LocalFilesystemStorage(app_settings.document_storage_path)
    llm = build_default_llm(
        app_settings.llm_provider,
        app_settings.llm_model,
        app_settings.llm_api_key,
    )
    extractor = ExtractorService(llm)
    return IngestionService(
        session,
        storage,
        max_document_size_bytes=app_settings.max_document_size_bytes,
        allowed_mime_types=app_settings.allowed_mime_types,
        extractor=extractor,
        auto_extract=True,
    )
