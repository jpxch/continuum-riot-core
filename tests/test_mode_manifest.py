import pytest

from app.models.patch import PatchRegistry
from app.models.mode import ModeRegistry, ModeFamily


async def test_manifest_404_for_unknown_mode(client, db_session):
    db_session.add(PatchRegistry(patch="1.0.0", is_current=True))
    await db_session.commit()

    response = await client.get("/v1/modes/unknown/manifest")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODE_NOT_FOUND"
    assert response.json()["status"] == "error"


async def test_manifest_success(client, db_session):
    db_session.add(PatchRegistry(patch="1.0.0", is_current=True))
    db_session.add(
        ModeRegistry(
            mode_key="sr",
            mode_family=ModeFamily.SR,
            display_name="Summoner's Rift",
            is_active=True,
        )
    )

    await db_session.commit()

    response = await client.get("/v1/modes/sr/manifest")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["modeKey"] == "sr"
    assert body["meta"]["dataVersion"] == "1.0.0"
