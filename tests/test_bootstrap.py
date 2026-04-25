import pytest

from app.core.config import settings
from app.models.asset import AssetRegistry, AssetType
from app.models.mode import ModeFamily, ModePatchRegistry, ModeRegistry, ModeStatus
from app.models.patch import PatchRegistry


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
async def test_bootstrap_success(client, db_session):
    patch = "1.0.0"

    db_session.add(PatchRegistry(patch=patch, is_current=True))
    db_session.add_all(
        [
            _asset_registry_entry(
                id=1,
                patch=patch,
                asset_type=AssetType.CHAMPION,
                filename="champion.json",
            ),
            _asset_registry_entry(
                id=2,
                patch=patch,
                asset_type=AssetType.ITEM,
                filename="item.json",
            ),
            _asset_registry_entry(
                id=3,
                patch=patch,
                asset_type=AssetType.RUNE,
                filename="runesReforged.json",
            ),
            _asset_registry_entry(
                id=4,
                patch=patch,
                asset_type=AssetType.SUMMONER,
                filename="summoner.json",
            ),
        ]
    )
    db_session.add(
        ModeRegistry(
            mode_key="sr",
            mode_family=ModeFamily.SR,
            display_name="Summoner's Rift",
            is_active=True,
        )
    )
    db_session.add(
        ModePatchRegistry(
            mode_key="sr",
            patch=patch,
            status=ModeStatus.READY,
        )
    )
    await db_session.commit()

    response = await client.get("/v1/bootstrap")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["meta"]["dataVersion"] == patch
    assert body["data"]["currentPatch"] == patch
    assert body["data"]["locale"] == settings.DEFAULT_LOCALE
    assert body["data"]["ddragon"]["dataBaseUrl"].endswith(f"/cdn/{patch}/data/{settings.DEFAULT_LOCALE}")
    assert body["data"]["assets"]["champion"] == {
        "ready": True,
        "filename": "champion.json",
        "endpoint": "/v1/champions",
    }
    assert body["data"]["modes"]["ready"] is True
    assert body["data"]["modes"]["total"] == 1
    assert body["data"]["capabilities"]["playerData"] is False
    assert body["data"]["capabilities"]["lcu"] is False


@pytest.mark.asyncio
async def test_bootstrap_404_when_no_patch(client):
    response = await client.get("/v1/bootstrap")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "NO_CURRENT_PATCH"


@pytest.mark.asyncio
async def test_bootstrap_reports_unready_assets_and_modes(client, db_session):
    patch = "1.0.0"

    db_session.add(PatchRegistry(patch=patch, is_current=True))
    db_session.add(
        ModeRegistry(
            mode_key="sr",
            mode_family=ModeFamily.SR,
            display_name="Summoner's Rift",
            is_active=True,
        )
    )
    await db_session.commit()

    response = await client.get("/v1/bootstrap")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["assets"]["champion"]["ready"] is False
    assert body["data"]["assets"]["item"]["ready"] is False
    assert body["data"]["modes"]["ready"] is False
    assert body["data"]["modes"]["active"] == 1
