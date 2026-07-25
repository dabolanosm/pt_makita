from __future__ import annotations

import httpx
import pytest

from app.infrastructure.external_books_client import GoogleBooksClient
from app.infrastructure.http_client import HttpClient
from app.infrastructure.external_books_client import _build_url


@pytest.mark.asyncio
async def test_google_books_client_search_returns_items(monkeypatch):
    response_data = {"items": [{"id": "abc", "volumeInfo": {"title": "Test Book"}}]}
    response = httpx.Response(status_code=200, json=response_data)

    async def fake_get(self, url: str, params=None):
        assert url == _build_url("volumes")
        assert params["q"] == "python"
        assert params["maxResults"] == 2
        return response

    monkeypatch.setattr(HttpClient, "get", fake_get)
    client = GoogleBooksClient(api_key="test-key")
    items = await client.search("python", max_results=2)
    assert items == response_data["items"]
