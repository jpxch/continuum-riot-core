from __future__ import annotations

import asyncio

import pytest

from app.services import patch_poller


@pytest.mark.asyncio
async def test_poll_loop_sleeps_interval_after_success(monkeypatch):
    calls = 0
    sleeps: list[int] = []

    async def poll_once() -> None:
        nonlocal calls
        calls += 1

    async def sleep(seconds: int) -> None:
        sleeps.append(seconds)
        raise asyncio.CancelledError

    monkeypatch.setattr(patch_poller, "poll_once", poll_once)
    monkeypatch.setattr(patch_poller.asyncio, "sleep", sleep)

    with pytest.raises(asyncio.CancelledError):
        await patch_poller.poll_loop(interval_seconds=3600, retry_seconds=60)

    assert calls == 1
    assert sleeps == [3600]


@pytest.mark.asyncio
async def test_poll_loop_sleeps_retry_after_failure(monkeypatch):
    calls = 0
    sleeps: list[int] = []

    async def poll_once() -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("database is warming up")

    async def sleep(seconds: int) -> None:
        sleeps.append(seconds)
        raise asyncio.CancelledError

    monkeypatch.setattr(patch_poller, "poll_once", poll_once)
    monkeypatch.setattr(patch_poller.asyncio, "sleep", sleep)

    with pytest.raises(asyncio.CancelledError):
        await patch_poller.poll_loop(interval_seconds=3600, retry_seconds=60)

    assert calls == 1
    assert sleeps == [60]
