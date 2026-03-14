from __future__ import annotations

import asyncio
import logging
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.patch import PatchRegistry
from app.services.ddragon import fetch_latest_patch, set_current_patch
from app.services.static_ingestion import ingest_patch_static_data
from app.services.mode_authority import sync_modes_for_patch
from app.core.config import settings

logger = logging.getLogger(__name__)


async def get_current_patch(db) -> str | None:
    result = await db.execute(
        select(PatchRegistry.patch).where(PatchRegistry.is_current.is_(True))
    )
    row = result.scaler_one_or_none()
    return row

async def poll_once() -> None:
    latest = await fetch_latest_patch()

    async with AsyncSessionLocal() as db:
        current = await get_current_patch(db)

        if current == latest.latest:
            logger.debug("Patch unchanged (%s)", current)
            return

        logger.info("New patch detected: %s -> %s", current, latest.latest)

        await set_current_patch(db, latest.latest)

    await ingest_patch_static_data(patch=latest.latest, locale="en_US")
    await sync_modes_for_patch(patch=latest.latest)

async def poll_loop(interval_seconds: int) -> None:
     while True:
        try:
            await poll_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Patch poll failed")

        await asyncio.sleep(interval_seconds)

async def start_patch_poller() -> asyncio.Task:
    interval = settings.PATCH_POLL_INTERVAL_SECONDS
    logger.info("Starting patch poller (interval=%ss)", interval)
    return asyncio.create_task(poll_loop(interval))