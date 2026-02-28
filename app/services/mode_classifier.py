from __future__ import annotations

from app.services.queue_catalog import QueueCatalogItem


def classify_mode_key(item: QueueCatalogItem) -> str:
    """
    Map queue catalog item into a stable mode_key.
    """
    map_name = (item.map_name or "").lower()
    desc = (item.description or "").lower()
    notes = (item.notes or "").lower()

    text = " ".join([map_name, desc, notes])

    if "tft" in text or "teamfight tactics" in text:
        return "tft"

    if "howling abyss" in text or "aram" in text:
        return "aram"

    if "summoner's rift" in text or "summoner's rift" in text:
        return "sr"

    return "rotating"