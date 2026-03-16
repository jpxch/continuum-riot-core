from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _request_with_retries(
    method: str,
    url: str,
) -> httpx.Response:

    retries = settings.HTTP_MAX_RETRIES
    base_backoff = settings.HTTP_RETRY_BACKOFF_SECONDS

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
                response = await client.request(method, url)

            response.raise_for_status()
            return response

        except httpx.HTTPError as exc:
            if attempt >= retries:
                logger.error(
                    "HTTP request failed after retries",
                    url=url,
                    error=str(exc),
                )
                raise

            backoff = base_backoff * (2 ** attempt)
            jitter = random.uniform(0, 0.25)

            delay = backoff + jitter

            logger.warning(
                "HTTP request failed, retrying",
                url=url,
                attempt=attempt + 1,
                delay=delay,
            )

            await asyncio.sleep(delay)


async def fetch_json(url: str) -> Any:
    response = await _request_with_retries("GET", url)
    return response.json()


async def fetch_bytes(url: str) -> tuple[bytes, str]:
    response = await _request_with_retries("GET", url)

    content_type = response.headers.get("content-type", "")

    return response.content, content_type
