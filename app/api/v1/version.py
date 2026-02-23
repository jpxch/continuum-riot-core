from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.patch import PatchRegistry

router = APIRouter()


@router.get("/version")
async def version(db: AsyncSession = Depends(get_db)):
    stmt = select(PatchRegistry).where(PatchRegistry.is_current.is_(True)).limit(1)
    row = (await db.execute(stmt)).scalar_one_or_none()

    return {
        "service": settings.SERVICE_NAME,
        "env": settings.ENV,
        "apiVersion": "v1",
        "dataVersion": row.patch if row else None,
    }
