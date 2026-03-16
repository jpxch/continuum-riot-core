import pytest
import httpx

from app.services.http_client import fetch_json


@pytest.mark.asyncio
async def test_fetch_json_success(monkeypatch):
    async def fake_request_with_retries(method: str, url: str) -> httpx.Response:
        return httpx.Response(
            200,
            json={"ok": True},
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(
        "app.services.http_client._request_with_retries",
        fake_request_with_retries,
    )

    result = await fetch_json("https://example.com/test")

    assert result["ok"] is True
