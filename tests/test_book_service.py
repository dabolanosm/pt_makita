from __future__ import annotations

import pytest
from app.application.book_service import BookService
from app.domain.models import Book
from app.domain.schemas import BookCreate, BookUpdate


class DummyBooksClient:
    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        return []


@pytest.mark.asyncio
async def test_create_update_delete_book(in_memory_session):
    service = BookService(db=in_memory_session, books_client=DummyBooksClient())
    created = service.create_book(BookCreate(title="Test Book"))

    assert created.id is not None
    assert created.title == "Test Book"

    updated = service.update_book(created.id, BookUpdate(title="Updated Title"))
    assert updated is not None
    assert updated.title == "Updated Title"

    deleted = service.delete_book(created.id)
    assert deleted is True
    assert service.get_book(created.id) is None


@pytest.mark.asyncio
async def test_sync_from_query_deduplicates_by_google_id(in_memory_session):
    class FakeBooksClient:
        async def search(self, query: str, max_results: int = 10) -> list[dict]:
            return [
                {"id": "g1", "volumeInfo": {"title": "Duplicate", "authors": ["Author"]}},
                {"id": "g1", "volumeInfo": {"title": "Duplicate", "authors": ["Author"]}},
            ]

    service = BookService(db=in_memory_session, books_client=FakeBooksClient())
    books = await service.sync_from_query(query="python", max_results=2)

    assert len(books) == 1
    count = in_memory_session.query(Book).count()
    assert count == 1


@pytest.mark.asyncio
async def test_sync_from_query_retries_google_lookup_on_repeated_calls(in_memory_session):
    class FakeBooksClient:
        def __init__(self) -> None:
            self.calls = 0

        async def search(self, query: str, max_results: int = 10) -> list[dict]:
            self.calls += 1
            return [{"id": "g1", "volumeInfo": {"title": "Book", "authors": ["Author"]}}]

    client = FakeBooksClient()
    service = BookService(db=in_memory_session, books_client=client)

    await service.sync_from_query(query="python", max_results=1)
    await service.sync_from_query(query="python", max_results=1)

    assert client.calls == 2
