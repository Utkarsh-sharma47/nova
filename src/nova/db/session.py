"""Database session and readiness helpers."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from nova.config import Settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": int(settings.database_connect_timeout_seconds)},
    )


def configure_engine(settings: Settings) -> Engine:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = create_db_engine(settings)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database engine is not configured")
    return _engine


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError("Database session factory is not configured")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_ready(settings: Settings | None = None) -> None:
    """Raise if the database cannot accept connections / simple queries."""
    engine = get_engine() if settings is None else create_db_engine(settings)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    finally:
        if settings is not None and engine is not _engine:
            engine.dispose()


def dispose_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
