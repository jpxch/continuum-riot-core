from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.ddragon import fetch_latest_patch, set_current_patch

router = APIRouter()


@router.post("/ddragon/sync")
async def ddragon_sync(db: AsyncSession = Depends(get_db)):
    info = await fetch_latest_patch()
    await set_current_patch(db, info.latest)
    return {"status": "ok", "currentPatch": info.latest}