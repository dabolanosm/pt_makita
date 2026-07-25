from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.interfaces.api.books import get_book_service
from app.application.book_service import BookService
from app.main import app


class DummyBooksClient:
    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        return []


@pytest.fixture
def test_client(in_memory_session, monkeypatch):
    service = BookService(db=in_memory_session, books_client=DummyBooksClient())
    app.dependency_overrides[get_book_service] = lambda: service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_get_books_empty(test_client):
    response = test_client.get("/api/books")
    assert response.status_code == 200
    assert response.json() == []


def test_create_update_delete_book(test_client):
    response = test_client.post("/api/books", json={"title": "API Book"})
    assert response.status_code == 201
    book = response.json()
    assert book["title"] == "API Book"

    book_id = book["id"]
    response = test_client.put(f"/api/books/{book_id}", json={"title": "Updated API Book"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated API Book"

    response = test_client.delete(f"/api/books/{book_id}")
    assert response.status_code == 204
    response = test_client.get(f"/api/books/{book_id}")
    assert response.status_code == 404
