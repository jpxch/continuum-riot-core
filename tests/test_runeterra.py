import json

import pytest

from app.core.config import settings
from app.core.paths import ddragon_asset_path
from app.models.asset import AssetRegistry, AssetType
from app.models.patch import PatchRegistry


def _write_static_asset(tmp_path, monkeypatch, *, patch: str, filename: str, payload: dict):
    monkeypatch.setattr(settings, "STATIC_ROOT", str(tmp_path))
    path = ddragon_asset_path(patch=patch, locale=settings.DEFAULT_LOCALE, filename=filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _asset_registry_entry(*, id: int, patch: str, asset_type: AssetType, filename: str) -> AssetRegistry:
    return AssetRegistry(
        id=id,
        patch=patch,
        asset_type=asset_type,
        locale=settings.DEFAULT_LOCALE,
        filename=filename,
        sha256="hash",
        file_size=1,
        content_type="application/json",
    )


@pytest.mark.asyncio
async def test_runeterra_lore_list_success(client, db_session, tmp_path, monkeypatch):
    patch = "1.0.0"
    champion_summary = {
        "data": {
            "Aatrox": {
                "id": "Aatrox",
                "key": "266",
                "name": "Aatrox",
                "title": "the Darkin Blade",
                "blurb": "Once honored defenders of Shurima...",
                "tags": ["Fighter", "Tank"],
                "partype": "Blood Well",
                "image": {"full": "Aatrox.png"},
            },
            "Ahri": {
                "id": "Ahri",
                "key": "103",
                "name": "Ahri",
                "title": "the Nine-Tailed Fox",
                "blurb": "Innately connected to the magic...",
                "tags": ["Mage", "Assassin"],
                "partype": "Mana",
                "image": {"full": "Ahri.png"},
            },
        }
    }

    _write_static_asset(
        tmp_path,
        monkeypatch,
        patch=patch,
        filename="champion.json",
        payload=champion_summary,
    )

    db_session.add(PatchRegistry(patch=patch, is_current=True))
    db_session.add(
        _asset_registry_entry(
            id=1,
            patch=patch,
            asset_type=AssetType.CHAMPION,
            filename="champion.json",
        )
    )
    await db_session.commit()

    response = await client.get("/v1/runeterra/lore")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["meta"]["dataVersion"] == patch
    assert [champion["id"] for champion in body["data"]] == ["Aatrox", "Ahri"]
    assert body["data"][0]["shortBio"] == "Once honored defenders of Shurima..."
    assert "lore" not in body["data"][0]


@pytest.mark.asyncio
async def test_runeterra_lore_detail_success(client, db_session, tmp_path, monkeypatch):
    patch = "1.0.0"
    champion_detail = {
        "data": {
            "Aatrox": {
                "id": "Aatrox",
                "key": "266",
                "name": "Aatrox",
                "title": "the Darkin Blade",
                "blurb": "Once honored defenders of Shurima...",
                "lore": "Aatrox and his brethren once defended Shurima.",
                "allytips": ["Use World Ender to force fights."],
                "enemytips": ["Keep your distance when his ultimate is active."],
                "tags": ["Fighter", "Tank"],
                "partype": "Blood Well",
                "image": {"full": "Aatrox.png"},
            }
        }
    }

    _write_static_asset(
        tmp_path,
        monkeypatch,
        patch=patch,
        filename="champion/Aatrox.json",
        payload=champion_detail,
    )

    db_session.add(PatchRegistry(patch=patch, is_current=True))
    db_session.add(
        _asset_registry_entry(
            patch=patch,
            id=1,
            asset_type=AssetType.CHAMPION_LORE,
            filename="champion/Aatrox.json",
        )
    )
    await db_session.commit()

    response = await client.get("/v1/runeterra/lore/Aatrox")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["id"] == "Aatrox"
    assert body["data"]["lore"] == "Aatrox and his brethren once defended Shurima."
    assert body["data"]["allyTips"] == ["Use World Ender to force fights."]
    assert body["data"]["enemyTips"] == ["Keep your distance when his ultimate is active."]


@pytest.mark.asyncio
async def test_runeterra_lore_detail_404_when_champion_missing(client, db_session, tmp_path, monkeypatch):
    patch = "1.0.0"
    champion_detail = {"data": {}}

    _write_static_asset(
        tmp_path,
        monkeypatch,
        patch=patch,
        filename="champion/Aatrox.json",
        payload=champion_detail,
    )

    db_session.add(PatchRegistry(patch=patch, is_current=True))
    db_session.add(
        _asset_registry_entry(
            patch=patch,
            id=1,
            asset_type=AssetType.CHAMPION_LORE,
            filename="champion/Aatrox.json",
        )
    )
    await db_session.commit()

    response = await client.get("/v1/runeterra/lore/Aatrox")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CHAMPION_NOT_FOUND"
