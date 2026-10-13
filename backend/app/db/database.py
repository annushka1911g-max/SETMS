"""
SETMS Backend — Database Engine and Session Factory
Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite) via the DATABASE_URL setting.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _make_engine():
    settings = get_settings()
    url = settings.database_url

    connect_args: dict = {}
    engine_kwargs: dict = {
        "echo": settings.app_debug and not settings.is_production,
        "future": True,
    }

    if url.startswith("sqlite"):
        # SQLite does not support connection pools in the same way
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
    else:
        # PostgreSQL async pool settings
        engine_kwargs.update(
            {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "pool_recycle": 300,
            }
        )

    return create_async_engine(url, **engine_kwargs)


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.
    The session is automatically closed after the request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions outside of request scope."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables. Used in development and testing only."""
    async with engine.begin() as conn:
        import app.models  # noqa: F401 — ensure models are registered
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")


async def drop_tables() -> None:
    """Drop all tables. Used in testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("database_tables_dropped")
