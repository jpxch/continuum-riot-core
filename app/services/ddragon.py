from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.patch import PatchRegistry


@dataclass(frozen=True)
class DDragonVersionInfo:
    latest: str


async def fetch_latest_patch() -> DDragonVersionInfo:
    url = f"{settings.DDDRAGON_BASE_URL}/api/versions.json"
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        versions = r.json()

    if not versions or not isinstance(versions, list):
        raise RuntimeError("Unexpected DDragon versions payload")

    latest = versions[0]
    return DDragonVersionInfo(latest=latest)

async def set_current_patch(db: AsyncSession, patch: str) -> None:
    # unset current
    await db.execute(update(PatchRegistry).values(is_current=False))

    existing = (await db.execute(select(PatchRegistry).where(PatchRegistry.patch == patch))).scalar_one_or_none()
    if existing is None:
        db.add(PatchRegistry(patch=patch, is_current=True))
    else:
        existing.is_current = True


    await db.commit()