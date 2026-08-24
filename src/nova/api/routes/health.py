"""Health and readiness routes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select

from nova.config import get_settings
from nova.db.models import SchemaMeta
from nova.db.session import check_database_ready, session_scope

router = APIRouter(tags=["ops"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: process is up. Does not check dependencies."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
    }


@router.get("/ready")
def ready() -> JSONResponse:
    """Readiness: database reachable and migrations applied (`schema_meta`)."""
    settings = get_settings()
    try:
        check_database_ready()
        with session_scope() as session:
            row = session.scalar(
                select(SchemaMeta).where(SchemaMeta.key == "schema_bootstrap")
            )
            if row is None:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "not_ready",
                        "reason": "migrations_pending",
                        "service": settings.service_name,
                    },
                )
            schema_value = row.value
    except Exception as exc:  # noqa: BLE001 — surface readiness failure, not crash
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": "database_unavailable",
                "error_type": type(exc).__name__,
                "service": settings.service_name,
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "service": settings.service_name,
            "environment": settings.environment,
            "schema": schema_value,
        },
    )
