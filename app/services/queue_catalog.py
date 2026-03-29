from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from app.services.http_client import fetch_json


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
    payload = await fetch_json(QUEUE_CATALOG_URL)

    if not isinstance(payload, list):
        raise RuntimeError("Unexpected queues.json payload (expected list)")

    out: list[QueueCatalogItem] = []

    for item in payload:
        if isinstance(item, dict):
            out.append(_normalize_item(item))

    return out