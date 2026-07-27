from __future__ import annotations

from fastapi.testclient import TestClient

from app.application.book_service import BookService
from app.interfaces.api.books import get_book_service as api_get_book_service
from app.interfaces.web.routes import get_book_service as web_get_book_service
from app.main import app


class DummyBooksClient:
    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        return []


def test_library_clear_button_uses_direct_clear_form(in_memory_session, monkeypatch):
    service = BookService(db=in_memory_session, books_client=DummyBooksClient())
    app.dependency_overrides[api_get_book_service] = lambda: service
    app.dependency_overrides[web_get_book_service] = lambda: service

    with TestClient(app) as client:
        response = client.post("/api/books", json={"title": "Book one"})
        assert response.status_code == 201

        home_response = client.get("/")
        assert home_response.status_code == 200
        html = home_response.text
        assert 'action="/web/library/clear"' in html
        assert 'Confirmar limpieza' in html

    app.dependency_overrides.clear()


def test_detail_page_delete_button_uses_direct_delete_form(in_memory_session, monkeypatch):
    service = BookService(db=in_memory_session, books_client=DummyBooksClient())
    app.dependency_overrides[api_get_book_service] = lambda: service
    app.dependency_overrides[web_get_book_service] = lambda: service

    with TestClient(app) as client:
        create_response = client.post("/api/books", json={"title": "Detail Book"})
        assert create_response.status_code == 201
        book_id = create_response.json()["id"]

        detail_response = client.get(f"/books/{book_id}")
        assert detail_response.status_code == 200
        html = detail_response.text
        assert f'action="/web/books/{book_id}/delete"' in html
        assert 'Confirmar eliminación' in html

    app.dependency_overrides.clear()


def test_quick_sync_forms_include_pending_ui_hooks():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert 'data-pending-submit="true"' in html
        assert 'pending-overlay' in html
