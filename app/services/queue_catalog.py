from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

QUEUE_CATALOG_URL = "https://static.developer.riotgames.com/docs/lol/queues.json"


@dataclass(frozen=True)
class QueueCatalogItem:
    queue_id: int
    map_name: str | None
    description: str | None
    notes: str | None


def _normalize_item(raw: dict[str, Any]) -> QueueCatalogItem:
    queue_id = raw.get("queueId")
    if not isinstance(queue_id, int):
        raise RuntimeError(f"Invalid queueId in queues.json item: {raw!r}")

    map_name = raw.get("map")
    description = raw.get("description")
    notes = raw.get("notes")

    return QueueCatalogItem(
        queue_id=queue_id,
        map_name=map_name if isinstance(map_name, str) else None,
        description=description if isinstance(description, str) else None,
        notes=notes if isinstance(notes, str) else None,
    )

async def fetch_queue_catalog() -> list[QueueCatalogItem]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(QUEUE_CATALOG_URL)
        r.raise_for_status()
        payload = r.json()

    if not isinstance(payload, list):
        raise RuntimeError("Unexpected queues.json payload (expected list)")

    out: list[QueueCatalogItem] = []
    for item in payload:
        if isinstance(item, dict):
            out.append(_normalize_item(item))
    return out