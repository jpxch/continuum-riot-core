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
async def test_champions_success(client, db_session, tmp_path, monkeypatch):
    patch = "1.0.0"
    champions = {
        "type": "champion",
        "version": patch,
        "data": {
            "Aatrox": {
                "id": "Aatrox",
                "key": "266",
                "name": "Aatrox",
                "title": "the Darkin Blade",
            }
        },
    }

    _write_static_asset(
        tmp_path,
        monkeypatch,
        patch=patch,
        filename="champion.json",
        payload=champions,
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

    response = await client.get("/v1/champions")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["meta"]["dataVersion"] == patch
    assert body["data"] == champions


@pytest.mark.asyncio
async def test_champions_409_when_asset_not_ready(client, db_session):
    patch = "1.0.0"
    db_session.add(PatchRegistry(patch=patch, is_current=True))
    await db_session.commit()

    response = await client.get("/v1/champions")

    assert response.status_code == 409
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "ASSET_NOT_READY"
