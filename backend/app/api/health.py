"""
SETMS — Health and Readiness Endpoints.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.db.database import AsyncSessionLocal
from app.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness check")
async def health():
    """
    Returns 200 OK when the application process is running.
    Used by Docker health checks and load balancers.
    """
    return {
        "status": "ok",
        "service": "setms-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready", summary="Readiness check")
async def readiness():
    """
    Returns 200 when the app is ready to serve traffic.
    Verifies database connectivity.
    """
    settings = get_settings()
    db_ok = False
    db_error = None

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = str(exc)

    status_code = 200 if db_ok else 503
    body = {
        "status": "ready" if db_ok else "not_ready",
        "service": "setms-backend",
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": "ok" if db_ok else f"error: {db_error}",
        },
    }

    if not db_ok:
        from fastapi import Response
        from fastapi.responses import JSONResponse
        return JSONResponse(content=body, status_code=503)

    return body
