from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.static_read import load_asset_json, load_champion_lore_json


def _extract_champion_payload(payload: dict[str, Any], champion_id: str) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("INVALID_JSON")

    champion = data.get(champion_id)
    if not isinstance(champion, dict):
        raise RuntimeError("CHAMPION_NOT_FOUND")

    return champion


def _build_lore_summary(champion: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": champion.get("id"),
        "key": champion.get("key"),
        "name": champion.get("name"),
        "title": champion.get("title"),
        "shortBio": champion.get("blurb"),
        "roles": champion.get("tags") or [],
        "resource": champion.get("partype"),
        "image": champion.get("image"),
    }


def build_companion_lore(champion: dict[str, Any]) -> dict[str, Any]:
    lore = _build_lore_summary(champion)
    lore["lore"] = champion.get("lore")
    lore["allyTips"] = champion.get("allytips") or []
    lore["enemyTips"] = champion.get("enemytips") or []
    return lore


async def list_champion_lore(session: AsyncSession) -> list[dict[str, Any]]:
    payload = await load_asset_json(session, "champion")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("INVALID_JSON")

    champions = [_build_lore_summary(champion) for champion in data.values() if isinstance(champion, dict)]
    champions.sort(key=lambda champion: (champion.get("name") or champion.get("id") or "").lower())
    return champions


async def get_champion_lore(session: AsyncSession, champion_id: str) -> dict[str, Any]:
    payload = await load_champion_lore_json(session, champion_id)
    champion = _extract_champion_payload(payload, champion_id)
    return build_companion_lore(champion)
