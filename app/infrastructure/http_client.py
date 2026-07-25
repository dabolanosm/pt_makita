from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

from app.errors import ExternalAPIError

logger = logging.getLogger(__name__)

DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_READ_TIMEOUT = 30.0
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class HttpClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=DEFAULT_CONNECT_TIMEOUT,
                read=DEFAULT_READ_TIMEOUT,
                write=DEFAULT_READ_TIMEOUT,
                pool=DEFAULT_CONNECT_TIMEOUT,
            ),
            headers={"User-Agent": "BookLibrarySync/0.2 (https://github.com/tu-usuario/book-library-sync; contacto@example.com)"},
        )

    async def get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        retry_delays = [1, 2, 4]
        for attempt in range(3):
            try:
                response = await self._client.get(url, params=params)
                if response.status_code in RETRY_STATUS_CODES and attempt < 2:
                    jitter = random.uniform(0, 0.5)
                    wait_time = retry_delays[attempt] + jitter
                    logger.warning(
                        "Rate limit or server error on GET %s (status %s). Retrying after %.2f seconds (attempt %d/3).",
                        url,
                        response.status_code,
                        wait_time,
                        attempt + 1,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                elif response.status_code in RETRY_STATUS_CODES:
                    error_msg = f"Rate limit or server error from Google Books API (status {response.status_code}). Please try again later."
                    logger.error(error_msg)
                    raise ExternalAPIError(message=error_msg, status_code=response.status_code)
                return response
            except httpx.RequestError as exc:
                if attempt < 2:
                    jitter = random.uniform(0, 0.5)
                    wait_time = retry_delays[attempt] + jitter
                    logger.warning("Request error on GET %s: %s. Retrying after %.2f seconds (attempt %d/3).", url, exc, wait_time, attempt + 1)
                    await asyncio.sleep(wait_time)
                    continue
                logger.error("Request failed after 3 attempts: %s", exc)
                raise
        raise RuntimeError("Unexpected HTTP client error")

    async def close(self) -> None:
        await self._client.aclose()
