"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nova import __version__
from nova.api.routes import health, metrics
from nova.config import get_settings
from nova.db.session import configure_engine, dispose_engine
from nova.observability.logging import configure_logging, get_logger
from nova.observability.middleware import ObservabilityMiddleware

logger = get_logger("nova.api")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(
        service=settings.service_name,
        environment=settings.environment,
        level=settings.log_level,
    )
    configure_engine(settings)
    logger.info(
        "application_started",
        extra={
            "event": "app.start",
            "status": "ok",
            "extra_fields": {"version": __version__},
        },
    )
    try:
        yield
    finally:
        dispose_engine()
        logger.info(
            "application_stopped",
            extra={"event": "app.stop", "status": "ok"},
        )


def create_app() -> FastAPI:
    """Build the ASGI application. Settings are read lazily from the environment."""
    application = FastAPI(
        title="Nova API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    application.add_middleware(ObservabilityMiddleware)
    application.include_router(health.router)
    application.include_router(metrics.router)
    return application


app = create_app()
