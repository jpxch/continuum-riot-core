from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.paths import ddragon_asset_path
from app.models.asset import AssetRegistry, AssetType
from app.models.patch import PatchRegistry


REQUIRED_ASSETS = {
    AssetType.CHAMPION: "champion.json",
    AssetType.ITEM: "item.json",
    AssetType.RUNE: "runesReforged.json",
    AssetType.SUMMONER: "summoner.json",
}

async def get_current_patch(session: AsyncSession) -> str | None:
    stmt = select(PatchRegistry.patch).where(PatchRegistry.is_current.is_(True)).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def asset_exists(
    session: AsyncSession,
    patch: str,
    asset_type: AssetType,
    filename: str | None = None
) -> bool:
    target_file = filename or REQUIRED_ASSETS.get(asset_type)
    if not target_file:
        return False

    stmt = (
        select(AssetRegistry.patch)
        .where(
            AssetRegistry.patch == patch,
            AssetRegistry.asset_type == asset_type,
            AssetRegistry.locale == settings.DEFAULT_LOCALE,
            AssetRegistry.filename == target_file,
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None

async def load_champion_lore_json(session: AsyncSession, champion_id: str) -> dict[str, Any]:
    patch = await get_current_patch(session)
    if not patch: raise RuntimeError("NO_CURRENT_PATCH")

    filename = f"champion/{champion_id}.json"
    if not await asset_exists(session, patch, AssetType.CHAMPION_LORE, filename=filename):
        raise RuntimeError("ASSET_NOT_READY")

    path = ddragon_asset_path(patch=patch, locale=settings.DEFAULT_LOCALE, filename=filename)
    if not path.exists(): raise RuntimeError("FILE_MISSING")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def build_asset_path(patch: str, asset_type: AssetType) -> Path:
    filename = REQUIRED_ASSETS[asset_type]
    return ddragon_asset_path(patch=patch, locale=settings.DEFAULT_LOCALE, filename=filename)

def normalize_asset_type(asset_type: str | AssetType) -> AssetType:
    if isinstance(asset_type, AssetType): return asset_type
    try: return AssetType(asset_type)
    except ValueError as exc: raise RuntimeError("UNKNOWN_ASSET_TYPE") from exc

async def load_asset_json(session: AsyncSession, asset_type: str | AssetType) -> dict[str, Any]:
    resolved_asset_type = normalize_asset_type(asset_type)
    patch = await get_current_patch(session)
    if not patch: raise RuntimeError("NO_CURRENT_PATCH")

    if not await asset_exists(session, patch, resolved_asset_type):
        raise RuntimeError("ASSET_NOT_READY")

    path = build_asset_path(patch, resolved_asset_type)
    if not path.exists(): raise RuntimeError("FILE_MISSING")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)