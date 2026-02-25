from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.patch import PatchRegistry
from app.api.response import success_response

router = APIRouter()


@router.get("/version")
async def version(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PatchRegistry).where(PatchRegistry.is_current.is_(True)).limit(1)
    row = (await db.execute(stmt)).scalar_one_or_none()

    data_version = row.patch if row else None

    return success_response(
        request,
        data={
            "service": settings.SERVICE_NAME,
            "env": settings.ENV,
        },
        data_version=data_version,
    )
