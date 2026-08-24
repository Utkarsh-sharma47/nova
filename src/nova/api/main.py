"""FastAPI application factory and uvicorn entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nova import __version__
from nova.api.deps import build_local_storage
from nova.api.errors import register_exception_handlers
from nova.api.middleware import CorrelationIdMiddleware
from nova.api.routes import documents, health
from nova.config import clear_settings_cache, get_settings
from nova.observability.logging import configure_logging, get_logger
from nova.persistence.database import Database

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    database = Database(settings)
    storage = build_local_storage(settings)
    app.state.settings = settings
    app.state.database = database
    app.state.storage = storage
    logger.info("nova_api_started", extra={"status": "started"})
    try:
        yield
    finally:
        await database.dispose()
        clear_settings_cache()
        logger.info("nova_api_stopped", extra={"status": "stopped"})


def create_app() -> FastAPI:
    app = FastAPI(
        title="Nova API",
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(documents.router)
    return app


def run() -> None:
    import uvicorn

    uvicorn.run(
        "nova.api.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


app = create_app()
