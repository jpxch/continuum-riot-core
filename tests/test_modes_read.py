import pytest

from app.models.patch import PatchRegistry
from app.models.mode import ModeRegistry, ModeFamily


async def test_modes_404_when_no_patch(client):
    response = await client.get("/v1/modes")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NO_CURRENT_PATCH"

async def test_modes_list_success(client, db_session):
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

    response = await client.get("/v1/modes")
    assert response.status_code == 200

    body = response.json()
    assert "data" in body
    assert body["meta"]["dataVersion"] == "1.0.0"

    assert len(body["data"]) == 1
    assert body["data"][0]["modeKey"] == "sr"
