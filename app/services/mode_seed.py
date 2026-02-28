from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mode import ModeFamily, ModeRegistry

@dataclass(frozen=True)
class SeedMode:
    mode_key: str
    mode_family: ModeFamily
    display_name: str
    is_active: bool

CANONICAL_SEED: tuple[SeedMode, ...] = (
    SeedMode("sr", ModeFamily.SR, "Summoner's Rift", True),
    SeedMode("aram", ModeFamily.ARAM, "ARAM", True),
    SeedMode("tft", ModeFamily.TFT, "Teamfight Tactics", True),
    SeedMode("rotating", ModeFamily.ROTATING, "Rotating Modes", False),
)

async def ensure_mode_seed(*, db: AsyncSession, patch: str | None = None) -> dict:
    """
    Ensure canonical modes exist in mode_registry.
    """
    created = 0
    touched = 0

    for seed in CANONICAL_SEED:
        existing = (
            await db.execute(
                select(ModeRegistry).where(ModeRegistry.mode_key == seed.mode_key).limit(1)
            )
        ).scalar_one_or_none()

        if existing is None:
            db.add(
                ModeRegistry(
                    mode_key=seed.mode_key,
                    mode_family=seed.mode_family,
                    display_name=seed.display_name,
                    is_active=seed.is_active,
                    first_seen_patch=patch,
                    last_seen_patch=patch,
                )
            )
            created += 1
        else:
            if seed.is_active and existing.is_active is False:
                existing.is_active = True
                touched += 1

    if created or touched:
        await db.commit()

    return {"created": created, "touched": touched}