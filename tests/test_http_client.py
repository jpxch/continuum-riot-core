import httpx
import pytest

from app.services.http_client import _request_with_retries, fetch_json


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

    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_request_with_retries_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    def fake_uniform(_start: float, _end: float) -> float:
        return 0.0

    class FakeAsyncClient:
        def __init__(self, *, timeout: float):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def request(self, method: str, url: str) -> httpx.Response:
            calls["count"] += 1

            if calls["count"] == 1:
                raise httpx.HTTPError("temporary failure")

            return httpx.Response(
                200,
                json={"ok": True},
                request=httpx.Request(method, url),
            )

    monkeypatch.setattr("app.services.http_client.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("app.services.http_client.random.uniform", fake_uniform)
    monkeypatch.setattr("app.services.http_client.httpx.AsyncClient", FakeAsyncClient)

    response = await _request_with_retries("GET", "https://example.com/test")

    assert response.json() == {"ok": True}
    assert calls["count"] == 2
    assert sleeps == [0.5]


@pytest.mark.asyncio
async def test_fetch_json_fails_after_retries(monkeypatch):
    async def always_fail(method: str, url: str):
        raise httpx.HTTPError("permanent failure")

    monkeypatch.setattr(
        "app.services.http_client._request_with_retries",
        always_fail,
    )

    with pytest.raises(httpx.HTTPError):
        await fetch_json("https://example.com/test")
