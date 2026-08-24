"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from nova.config import Settings, get_settings
from nova.domain.errors import InvalidApiKeyError, UnauthenticatedError
from nova.infrastructure.storage import DocumentStoragePort, LocalFilesystemDocumentStorage
from nova.persistence.database import Database


def get_app_settings() -> Settings:
    return get_settings()


def get_database(request: Request) -> Database:
    return request.app.state.database  # type: ignore[no-any-return]


def get_storage(request: Request) -> DocumentStoragePort:
    return request.app.state.storage  # type: ignore[no-any-return]


async def get_db_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    async with database.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def require_api_auth(
    settings: Annotated[Settings, Depends(get_app_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    """Require Bearer token or X-API-Key matching API_AUTH_TOKEN."""
    token: str | None = None
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
            token = parts[1].strip()
        elif authorization.strip():
            # Treat raw Authorization value as token when scheme omitted.
            token = authorization.strip()
    if token is None and x_api_key:
        token = x_api_key.strip()
    if not token:
        raise UnauthenticatedError()
    if token != settings.api_auth_token:
        raise InvalidApiKeyError()
    return token


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
DatabaseDep = Annotated[Database, Depends(get_database)]
StorageDep = Annotated[DocumentStoragePort, Depends(get_storage)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
AuthTokenDep = Annotated[str, Depends(require_api_auth)]


def build_local_storage(settings: Settings) -> LocalFilesystemDocumentStorage:
    return LocalFilesystemDocumentStorage(settings.document_storage_path)
