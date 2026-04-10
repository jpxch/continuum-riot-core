from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import time
import structlog

logger = structlog.get_logger(__name__)

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


async def ingest_patch_static_data(*, patch: str, locale: str) -> list[AssetResult]:
    results: list[AssetResult] = []

    out_dir = ddragon_locale_dir(patch=patch, locale=locale)
    out_dir.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:

        for asset_type, filename in STATIC_FILES.items():

            path = ddragon_asset_path(
                patch=patch,
                locale=locale,
                filename=filename
            )

            url = _static_url(
                patch=patch,
                locale=locale,
                filename=filename,
            )

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
                        results.append(
                            AssetResult(asset_type, filename, "skipped")
                        )

                        duration_ms = int((time.perf_counter() - start) * 1000)

                        logger.info(
                            "ddragon.asset.skipped",
                            asset_type=asset_type.value,
                            filename=filename,
                            patch=patch,
                            locale=locale,
                            duration_ms=duration_ms,
                        )

                        continue

                data, content_type = await fetch_bytes(url)

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

                    status = "new"

                else:
                    existing.sha256 = new_hash
                    existing.file_size = size
                    existing.content_type = content_type

                    status = "updated"

                results.append(
                    AssetResult(asset_type, filename, status)
                )

                await db.commit()

                duration_ms = int((time.perf_counter() - start) * 1000)

                logger.info(
                    "ddragon.asset.ingested",
                    asset_type=asset_type.value,
                    filename=filename,
                    patch=patch,
                    locale=locale,
                    status=status,
                    file_size=size,
                    duration_ms=duration_ms,
                )

            except Exception as e:

                await db.rollback()

                logger.error(
                    "ddragon.asset.failed",
                    asset_type=asset_type.value,
                    filename=filename,
                    patch=patch,
                    locale=locale,
                    url=url,
                    error=str(e),
                    exc_info=True,
                )

                results.append(
                    AssetResult(
                        asset_type,
                        filename,
                        "failed",
                        str(e)
                    )
                )

    failures = [r for r in results if r.status == "failed"]

    if failures:
        raise RuntimeError(
            f"Static ingestion failed for {len(failures)} assets"
        )

    return results


def summarize_results(results: list[AssetResult]) -> dict:
    summary = {
        "total": len(results),
        "new": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }

    for r in results:
        summary[r.status] += 1

    return summary