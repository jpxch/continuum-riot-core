from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.asset import AssetType
from app.services.mode_read import list_modes_for_patch
from app.services.static_read import REQUIRED_ASSETS, asset_exists, get_current_patch


STATIC_ASSET_ENDPOINTS = {
    AssetType.CHAMPION: "/v1/champions",
    AssetType.ITEM: "/v1/items",
    AssetType.RUNE: "/v1/runes",
    AssetType.SUMMONER: "/v1/summoners",
}


async def build_bootstrap(session: AsyncSession) -> dict:
    patch = await get_current_patch(session)
    if not patch:
        raise RuntimeError("NO_CURRENT_PATCH")

    assets = {}
    for asset_type, filename in REQUIRED_ASSETS.items():
        assets[asset_type.value] = {
            "ready": await asset_exists(session, patch, asset_type, filename=filename),
            "filename": filename,
            "endpoint": STATIC_ASSET_ENDPOINTS[asset_type],
        }

    modes = await list_modes_for_patch(session, patch)
    active_modes = [mode for mode in modes if mode["isActive"]]
    modes_ready = bool(active_modes) and all(
        mode["status"] == "ready"
        for mode in active_modes
    )

    ddragon_base = settings.DDRAGON_BASE_URL.rstrip("/")
    asset_base_url = f"{ddragon_base}/cdn/{patch}"

    return {
        "service": settings.SERVICE_NAME,
        "env": settings.ENV,
        "currentPatch": patch,
        "locale": settings.DEFAULT_LOCALE,
        "ddragon": {
            "baseUrl": ddragon_base,
            "dataBaseUrl": f"{asset_base_url}/data/{settings.DEFAULT_LOCALE}",
            "assetBaseUrl": asset_base_url,
            "imageBaseUrl": f"{asset_base_url}/img",
        },
        "assets": assets,
        "modes": {
            "ready": modes_ready,
            "total": len(modes),
            "active": len(active_modes),
            "endpoint": "/v1/modes",
        },
        "capabilities": {
            "staticData": True,
            "modes": True,
            "playerData": False,
            "matchData": False,
            "lcu": False,
        },
    }
