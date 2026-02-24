from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx
import logging
logger = logging.getLogger(__name__)
from sqlalchemy import select

from app.core.config import settings
from app.core.paths import ddragon_asset_path, ddragon_locale_dir
from app.db.session import AsyncSessionLocal
from app.models.asset import AssetRegistry, AssetType
from app.utils.hash import sha256_bytes, sha256_file


AssetStatus = Literal["new", "updated", "skipped", "failed"]

@dataclass(frozen=True)
class AssetResult:
    asset_type: AssetType
    filename: str
    status: AssetStatus
    error: str | None = None

STATIC_FILES: dict[AssetType, str] = {
    AssetType.CHAMPION: "champion.json",
    AssetType.ITEM: "item.json",
    AssetType.RUNE: "runesReforged.json",
    AssetType.SUMMONER: "summoner.json",
}

def _static_url(*, patch: str, locale: str, filename: str) -> str:
    return f"{settings.DDDRAGON_BASE_URL}/cdn/{patch}/data/{locale}/{filename}"

async def _fetch(url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.content, r.headers.get("content-type", "application/octet-stream")

async def ingest_patch_static_data(*, patch: str, locale: str) -> list[AssetResult]:
    results: list[AssetResult] = []

    out_dir = ddragon_locale_dir(patch=patch, locale=locale)
    out_dir.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:

        for asset_type, filename in STATIC_FILES.items():
            path = ddragon_asset_path(patch=patch, locale=locale, filename=filename)

            try:
                stmt = (
                    select(AssetRegistry)
                    .where(AssetRegistry.patch == patch)
                    .where(AssetRegistry.locale == locale)
                    .where(AssetRegistry.asset_type == asset_type)
                    .where(AssetRegistry.filename == filename)
                )
                existing = (await db.execute(stmt)).scalar_one_or_none()

                if existing and path.exists():
                    local_hash = sha256_file(path)
                    if local_hash == existing.sha256:
                        results.append(AssetResult(asset_type, filename, "skipped"))
                        continue

                data, content_type = await _fetch(
                    _static_url(patch=patch, locale=locale, filename=filename)
                )

                new_hash = sha256_bytes(data)
                size = len(data)

                path.write_bytes(data)

                if existing is None:
                    db.add(
                        AssetRegistry(
                            patch=patch,
                            asset_type=asset_type,
                            locale=locale,
                            filename=filename,
                            sha256=new_hash,
                            file_size=size,
                            content_type=content_type,
                        )
                    )
                    results.append(AssetResult(asset_type, filename, "new"))
                else:
                    existing.sha256 = new_hash
                    existing.file_size = size
                    existing.content_type = content_type
                    results.append(AssetResult(asset_type, filename, "updated"))

                await db.commit()

            except Exception as e:
                await db.rollback()
                results.append(AssetResult(asset_type, filename, "failed", str(e)))
                logger.exception("Static ingestion failed for %s", filename)

    return results