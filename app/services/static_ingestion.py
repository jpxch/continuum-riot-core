from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

import time
import structlog

logger = structlog.get_logger()

from sqlalchemy import select

from app.core.config import settings
from app.core.paths import ddragon_asset_path, ddragon_locale_dir
from app.db.session import AsyncSessionLocal
from app.models.asset import AssetRegistry, AssetType
from app.utils.hash import sha256_bytes, sha256_file
from app.services.http_client import fetch_bytes


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
    return f"{settings.DDRAGON_BASE_URL}/cdn/{patch}/data/{locale}/{filename}"

async def _process_asset_ingestion(
    db: AsyncSessionLocal,
    asset_type: AssetType,
    patch: str,
    locale: str,
    filename: str,
    url: str
) -> AssetResult:
    path = ddragon_asset_path(patch=patch, locale=locale, filename=filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        start = time.perf_counter()

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
                return AssetResult(asset_type, filename, "skipped")

        data, content_type = await fetch_bytes(url)
        new_hash = sha256_bytes(data)
        size = len(data)
        path.write_bytes(data)

        if existing is None:
            db.add(AssetRegistry(
                patch=patch, asset_type=asset_type, locale=locale,
                filename=filename, sha256=new_hash, file_size=size,
                content_type=content_type,
            ))
            status = "new"
        else:
            existing.sha256 = new_hash
            existing.file_size = size
            existing.content_type = content_type
            status = "updated"

        await db.commit()
        return AssetResult(asset_type, filename, status)

    except Exception as e:
        await db.rollback()
        return AssetResult(asset_type, filename, "failed", str(e))


async def ingest_patch_static_data(*, patch: str, locale: str) -> list[AssetResult]:
    results: list[AssetResult] = []

    async with AsyncSessionLocal() as db:
        for asset_type, filename in STATIC_FILES.items():
            url = _static_url(patch=patch, locale=locale, filename=filename)
            res = await _process_asset_ingestion(db, asset_type, patch, locale, filename, url)
            results.append(res)

        champ_res = next((r for r in results if r.asset_type == AssetType.CHAMPION), None)
        if champ_res and champ_res.status != "failed":
            lore_results = await ingest_champion_lore_assets(db, patch=patch, locale=locale)
            results.extend(lore_results)

    failures = [r for r in results if r.status == "failed"]
    if failures:
        raise RuntimeError(f"Static ingestion failed for {len(failures)} assets")

    return results


async def ingest_champion_lore_assets(db: AsyncSessionLocal, patch: str, locale: str) -> list[AssetResult]:
    results = []
    summary_path = ddragon_asset_path(patch=patch, locale=locale, filename="champion.json")

    with open(summary_path, "r") as f:
        summary_data = json.load(f)

    for champ_id in summary_data["data"].keys():
        filename = f"champion/{champ_id}.json"
        url = _static_url(patch=patch, locale=locale, filename=filename)
        res = await _process_asset_ingestion(db, AssetType.CHAMPION_LORE, patch, locale, filename, url)
        results.append(res)

    return results

def summarize_results(results: list[AssetResult]) -> dict:
    summary = {"total": len(results), "new": 0, "updated": 0, "skipped": 0, "failed": 0}
    for r in results:
        summary[r.status] += 1
    return summary