"""Health and readiness endpoints (no auth)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    database = request.app.state.database
    storage = request.app.state.storage
    db_ok = await database.ping()
    storage_ok = True
    try:
        storage_ok = bool(storage.ping())
    except Exception:
        storage_ok = False

    # Storage is optional for readiness (degraded ok); DB is required.
    body: dict[str, Any] = {
        "status": "ready" if db_ok else "not_ready",
        "checks": {
            "database": "ok" if db_ok else "fail",
            "storage": "ok" if storage_ok else "degraded",
        },
    }
    status_code = 200 if db_ok else 503
    return JSONResponse(status_code=status_code, content=body)
