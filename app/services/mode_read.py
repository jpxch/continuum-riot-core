from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mode import ModeRegistry, ModePatchRegistry, ModeQueueBinding, ModeStatus
from app.models.patch import PatchRegistry

async def get_current_patch(session: AsyncSession) -> str | None:
    stmt = select(PatchRegistry.patch).where(PatchRegistry.is_current.is_(True)).limit(1)
    return (await session.execute(stmt)).scalar_one_or_none()

def _derive_status(row: ModePatchRegistry | None) -> str:
    if row is None:
        return "partial"
    return row.status.value

async def list_modes_for_patch(session: AsyncSession, patch: str) -> list[dict]:
    modes = (await session.execute(select(ModeRegistry))).scalars().all()

    mpr = (
        await session.execute(
            select(ModePatchRegistry).where(ModePatchRegistry.patch == patch)
        )
    ).scalars().all()
    mpr_map = {r.mode_key: r for r in mpr}

    bindings = (
        await session.execute(select(ModeQueueBinding))
    ).scalars().all()
    queues_by_mode: dict[str, list[int]] = {}
    for b in bindings:
        queues_by_mode.setdefault(b.mode_key, []).append(b.queue_id)

    out: list[dict] = []
    for mode in modes:
        row = mpr_map.get(mode.mode_key)
        out.append(
            {
                "modeKey": mode.mode_key,
                "displayName": mode.display_name,
                "modeFamily": mode.mode_family,
                "isActive": mode.is_active,
                "patch": patch,
                "status": _derive_status(row),
                "queues": queues_by_mode.get(mode.mode_key, [] ),
            }
        )

    out.sort(key=lambda x: (x["modeFamily"], x["modeKey"]))
    return out

async def get_mode_manifest(session: AsyncSession, patch: str, mode_key: str) -> dict | None:
    mode = (
        await session.execute(
            select(ModeRegistry).where(ModeRegistry.mode_key == mode_key).limit(1)
        )
    ).scalar_one_or_none()
    if mode is None:
        return None

    row = (
        await session.execute(
            select(ModePatchRegistry).where(
                ModePatchRegistry.mode_key == mode_key,
                ModePatchRegistry.patch == patch,
            ).limit(1)
        )
    ).scalar_one_or_none()

    bindings = (
        await session.execute(
            select(ModeQueueBinding).where(ModeQueueBinding.mode_key == mode_key)
        )
    ).scalars().all()

    return {
        "modeKey": mode.mode_key,
        "displayName": mode.display_name,
        "modeFamily": mode.mode_family.value,
        "isActive": mode.is_active,
        "patch": patch,
        "status": _derive_status(row),
        "queues": [
            {"queueId": b.queue_id, "description": b.queue_description}
            for b in sorted(bindings, key=lambda b: b.queue_id)
        ],
        "checksum": row.checksum if row else None,
        "generatedAt": row.generated_at.isoformat() if row else None,
    }