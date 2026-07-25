from __future__ import annotations

import logging

import httpx

from app.errors import ExternalAPIError
from app.infrastructure.http_client import HttpClient

logger = logging.getLogger(__name__)


def _build_url(path: str) -> str:
    return f"https://www.googleapis.com/books/v1/{path}"


class GoogleBooksClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._http_client = HttpClient()

    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search Google Books for volumes matching the query and return the raw items list."""
        url = _build_url("volumes")
        params = {"q": query, "maxResults": max_results, "key": self.api_key}

        try:
            response = await self._http_client.get(url, params=params)
        except httpx.RequestError as exc:
            logger.error("Network error searching Google Books: %s", exc)
            raise ExternalAPIError(message="Network error contacting Google Books API", status_code=502)

        if 400 <= response.status_code < 500:
            logger.error("Google Books API returned client error %s: %s", response.status_code, response.text)
            raise ExternalAPIError(message=response.text or "Google Books API client error", status_code=response.status_code)

        if response.status_code >= 500:
            logger.error("Google Books API returned server error %s", response.status_code)
            raise ExternalAPIError(message="Google Books API server error", status_code=502)

        payload = response.json()
        return payload.get("items", []) or []

    async def get_by_id(self, volume_id: str) -> dict | None:
        """Fetch a single Google Books volume by its volume ID, or return None when not found."""
        url = _build_url(f"volumes/{volume_id}")
        params = {"key": self.api_key}

        try:
            response = await self._http_client.get(url, params=params)
        except httpx.RequestError as exc:
            logger.error("Network error fetching volume %s: %s", volume_id, exc)
            raise ExternalAPIError(message="Network error contacting Google Books API", status_code=502)

        if response.status_code == 404:
            return None

        if 400 <= response.status_code < 500:
            logger.error("Google Books API returned client error %s for volume %s", response.status_code, volume_id)
            raise ExternalAPIError(message=response.text or "Google Books API client error", status_code=response.status_code)

        if response.status_code >= 500:
            logger.error("Google Books API returned server error %s for volume %s", response.status_code, volume_id)
            raise ExternalAPIError(message="Google Books API server error", status_code=502)

        return response.json()
