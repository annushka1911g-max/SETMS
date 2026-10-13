"""
SETMS — FastAPI Application Factory.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.database import create_tables

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # Configure structured logging first
    configure_logging()

    logger.info(
        "setms_backend_starting",
        environment=settings.app_env,
        debug=settings.app_debug,
        database=settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
    )

    # Auto-create tables in development (Alembic handles production migrations)
    if not settings.is_production:
        await create_tables()
        logger.info("dev_tables_created")

    logger.info("setms_backend_ready")
    yield

    logger.info("setms_backend_shutting_down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="SETMS — Smart Emergency Traffic Management System",
        description=(
            "Backend API for SETMS. Tracks authorized ambulances, coordinates simulated "
            "traffic signals, creates safe green corridors, and notifies hospitals.\n\n"
            "⚠️ **Safety Notice**: All traffic signal commands in this system are **simulated** "
            "and do not connect to real public-road infrastructure."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        # Disable debug mode in production
        debug=settings.app_debug and not settings.is_production,
    )

    # ---- CORS ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    # ---- Request Logging Middleware ----
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "http_request",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    # ---- Global Exception Handler ----
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(
            "unhandled_exception",
            exc_type=type(exc).__name__,
            exc_msg=str(exc),
            path=request.url.path,
        )
        # Never expose internal traces to ordinary clients
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again later."},
        )

    # ---- Routers ----
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()
