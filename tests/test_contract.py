import pytest


@pytest.mark.asyncio
async def test_success_response_contract(client):
    response = await client.get("/v1/health")

    body = response.json()

    assert response.status_code == 200

    assert body["status"] == "success"
    assert "data" in body
    assert "meta" in body

    meta = body["meta"]

    assert "requestId" in meta
    assert "apiVersion" in meta
    assert "generatedAt" in meta


@pytest.mark.asyncio
async def test_error_response_contract(client):
    response = await client.get("/v1/jobs/00000000-0000-0000-0000-000000000000")

    body = response.json()

    assert body["status"] == "error"
    assert "error" in body

    error = body["error"]

    assert "code" in error
    assert "message" in error
    assert "requestId" in error


@pytest.mark.asyncio
async def test_pagination_contract(client):
    response = await client.get("/v1/jobs/recent")

    body = response.json()

    assert body["status"] == "success"

    meta = body["meta"]

    assert "pagination" in meta
    pagination = meta["pagination"]
    assert "limit" in pagination
    assert "offset" in pagination
    assert "total" in pagination