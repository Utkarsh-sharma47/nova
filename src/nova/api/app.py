"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from nova import __version__
from nova.api.routes import router
from nova.config import Settings, get_settings
from nova.domain.errors import NovaError
from nova.observability.logging import configure_logging
from nova.observability.middleware import ObservabilityMiddleware
from nova.persistence.database import configure_database, dispose_database

logger = logging.getLogger("nova.api")


def _error_body(
    request: Request,
    code: str,
    message: str,
    retryable: bool,
    details: object | None = None,
) -> dict[str, object]:
    error: dict[str, object] = {
        "code": code,
        "message": message,
        "trace_id": str(getattr(request.state, "trace_id", "unavailable")),
        "retryable": retryable,
    }
    if details:
        error["details"] = details
    return {"error": error}


def create_app(app_settings: Settings | None = None) -> FastAPI:
    configured_settings = app_settings or get_settings()

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        configured_settings.validate_runtime()
        configure_logging(
            configured_settings.service_name,
            configured_settings.app_env,
            configured_settings.log_level,
        )
        configure_database(configured_settings)
        logger.info("application_started", extra={"event": "app.start", "status": "ok"})
        try:
            yield
        finally:
            dispose_database()

    application = FastAPI(title="Nova API", version=__version__, lifespan=lifespan)
    application.state.settings = configured_settings
    application.add_middleware(ObservabilityMiddleware)
    application.include_router(router)

    @application.exception_handler(NovaError)
    async def nova_error_handler(request: Request, exc: NovaError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                request,
                exc.code,
                exc.message,
                exc.retryable,
                exc.details,
            ),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            {"field": ".".join(str(item) for item in error["loc"]), "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body(
                request,
                "VALIDATION_FAILED",
                "The request failed validation.",
                False,
                details,
            ),
        )

    @application.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, _exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_error",
            extra={"event": "http.unhandled_error", "status": "error"},
        )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                request,
                "INTERNAL_ERROR",
                "An internal error occurred.",
                False,
            ),
        )

    return application


app = create_app()
