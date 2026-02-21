from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings


def make_async_engine() -> AsyncEngine:
    return create_async_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        future=True,
    )