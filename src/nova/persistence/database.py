"""Database engine, sessions, and migration-only production bootstrap."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from nova.config import Settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_REQUIRED_TABLES = {
    "customers",
    "shipments",
    "documents",
    "document_versions",
    "verification_runs",
    "idempotency_records",
    "agent_executions",
    "model_call_metadata",
    "extracted_fields",
}


def configure_database(settings: Settings) -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("postgresql"):
        connect_args["connect_timeout"] = settings.database_connect_timeout_seconds
    _engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    _session_factory = sessionmaker(_engine, expire_on_commit=False)


def set_engine(engine: Engine) -> None:
    """Override the engine for tests; production setup uses configure_database."""
    global _engine, _session_factory
    _engine = engine
    _session_factory = sessionmaker(engine, expire_on_commit=False)


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("database is not configured")
    return _engine


def get_session() -> Iterator[Session]:
    if _session_factory is None:
        raise RuntimeError("database is not configured")
    session = _session_factory()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    if _session_factory is None:
        raise RuntimeError("database is not configured")
    with _session_factory.begin() as session:
        yield session


def database_ready() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            tables = set(inspect(connection).get_table_names())
            if not _REQUIRED_TABLES <= tables:
                return False
    except Exception:
        return False
    return True


def dispose_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
