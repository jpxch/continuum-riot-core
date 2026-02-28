from __future__ import annotations

import logging
import hashlib

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.mode import ModeRegistry, ModeQueueBinding, ModePatchRegistry, ModeStatus
from app.services.mode_seed import ensure_mode_seed, CANONICAL_SEED
from app.services.queue_catalog import fetch_queue_catalog, QueueCatalogItem
from app.services.mode_classifier import classify_mode_key

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModeAuthorityResult:
    patch: str
    seeded_created: int
    seeded_touched: int
    queues_fetched: int
    bindings_created: int
    bindings_updated: int
    modes_seen: int
    patch_rows_written: int
    status: str
    error: str | None

def _checksum_for_items(items: list[tuple[int, str, str | None]]) -> str:
    """
    Deterministic checksum for discovery inputs.
    Tuple: (queue_id, mode_key, description)
    """
    h = hashlib.sha256()
    for queue_id, mode_key, desc in sorted(items, key=lambda x: x[0]):
        h.update(str(queue_id).encode("utf-8"))
        h.update(b"|")
        h.update(mode_key.encode("utf-8"))
        h.update(b"|")
        h.update((desc or "").encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()

async def _upsert_queue_binding(
        *, db: AsyncSession, queue_id: int, mode_key: str, description: str | None
) -> tuple[bool, bool]:
    """
    Returns (created, updated).
    """
    existing = (
        await db.execute(
            select(ModeQueueBinding).where(ModeQueueBinding.queue_id == queue_id).limit(1)
        )
    ).scalar_one_or_none()

    if existing is None:
        db.add(
            ModeQueueBinding(
                mode_key=mode_key,
                queue_id=queue_id,
                queue_description=description,
            )
        )
        return True, False

    updated = False
    if existing.mode_key != mode_key:
        existing.mode_key = mode_key
        updated = True

    if (existing.queue_description or None) != (description or None):
        existing.queue_description = description
        updated = True

    return False, updated

async def _touch_mode_seen(*, db: AsyncSession, patch: str, mode_key: str) -> None:
    mode = (
        await db.execute(select(ModeRegistry).where(ModeRegistry.mode_key == mode_key).limit(1))
    ).scalar_one()

    if mode.first_seen_patch is None:
        mode.first_seen_patch = patch
    mode.last_seen_patch = patch

    mode.is_active = True

async def _write_patch_statuses(
        *,
        db: AsyncSession,
        patch: str,
        checksum: str,
        discovered_mode_keys: set[str],
) -> int:
    """
    Upsert ModePatchRegistry rows for the patch.
    """
    core_keys = {"sr", "aram", "tft"}

    modes = (await db.execute(select(ModeRegistry))).scalars().all()
    count = 0

    for mode in modes:
        desired = (
            ModeStatus.READY if (mode.mode_key in discovered_mode_keys or mode.mode_key in core_keys)
            else ModeStatus.PARTIAL
        )

        existing = (
            await db.execute(
                select(ModePatchRegistry).where(
                    ModePatchRegistry.mode_key == mode.mode_key,
                    ModePatchRegistry.patch == patch,
                ).limit(1)
            )
        ).scalar_one_or_none()

        if existing is None:
            db.add(
                ModePatchRegistry(
                    mode_key=mode.mode_key,
                    patch=patch,
                    status=desired,
                    checksum=checksum,
                )
            )
            count += 1
        else:
            changed = False
            if existing.status != desired:
                existing.status = desired
                changed = True
            if (existing.checksum or None) != (checksum or None):
                existing.checksum = checksum
                changed = True
            if changed:
                count += 1

    return count


async def sync_modes_for_patch(*, patch: str) -> ModeAuthorityResult:
    """
    Background-task safe mode authority sync for a patch.
    """
    try:
        async with AsyncSessionLocal() as db:
            seed_info = await ensure_mode_seed(db=db, patch=patch)

            catalog = await fetch_queue_catalog()

            bindings_created = 0
            bindings_updated = 0
            discovered_modes: set[str] = set()
            checksum_inputs: list[tuple[int, str, str | None]] = []

            for item in catalog:
                mode_key = classify_mode_key(item)
                discovered_modes.add(mode_key)
                checksum_inputs.append((item.queue_id, mode_key, item.description))

                created, updated = await _upsert_queue_binding(
                    db=db,
                    queue_id=item.queue_id,
                    mode_key=mode_key,
                    description=item.description,
                )
                if created:
                    bindings_created += 1
                if updated:
                    bindings_updated += 1

            for mode_key in discovered_modes:
                await _touch_mode_seen(db=db, patch=patch, mode_key=mode_key)

            checksum = _checksum_for_items(checksum_inputs)
            patch_rows_written = await _write_patch_statuses(
                db=db,
                patch=patch,
                checksum=checksum,
                discovered_mode_keys=discovered_modes,
            )

            await db.commit()

            logger.info(
                "Mode authority sync complete",
                extra={
                    "patch": patch,
                    "queues_fetched": len(catalog),
                    "seed_created": seed_info["created"],
                    "seed_touched": seed_info["touched"],
                    "bindings_created": bindings_created,
                    "bindings_updated": bindings_updated,
                    "modes_seen": len(discovered_modes),
                    "patch_rows_written": patch_rows_written,
                },
            )

            return ModeAuthorityResult(
                patch=patch,
                seeded_created=seed_info["created"],
                seeded_touched=seed_info["touched"],
                queues_fetched=len(catalog),
                bindings_created=bindings_created,
                bindings_updated=bindings_updated,
                modes_seen=len(discovered_modes),
                patch_rows_written=patch_rows_written,
                status="ok",
                error=None,
            )

    except Exception as e:
        logger.exception("Mode authority sync failed", extra={"patch": patch})
        return ModeAuthorityResult(
            patch=patch,
            seeded_created=0,
            seeded_touched=0,
            queues_fetched=0,
            bindings_created=0,
            bindings_updated=0,
            modes_seen=0,
            patch_rows_written=0,
            status="error",
            error=str(e),
        )