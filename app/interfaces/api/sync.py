from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.application.book_service import BookService
from app.domain.schemas import BookRead
from app.errors import ExternalAPIError, ValidationError
from app.infrastructure.db import get_db
from app.infrastructure.external_books_client import GoogleBooksClient
from app.config import get_settings
from sqlalchemy.orm import Session


class SyncRequest(BaseModel):
    query: str
    max_results: int = Field(default=10, le=10)


SEARCH_SEED_QUERIES = [
    "python programming",
    "science fiction",
    "colombia history",
    "latin american literature",
    "web development",
    "artificial intelligence",
]

router = APIRouter()


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    settings = get_settings()
    books_client = GoogleBooksClient(api_key=settings.google_books_api_key)
    return BookService(db=db, books_client=books_client)


@router.post("/sync", response_model=list[BookRead], tags=["sync"])
async def sync_books(request: SyncRequest, book_service: BookService = Depends(get_book_service)) -> list[BookRead]:
    try:
        books = await book_service.sync_from_query(query=request.query, max_results=request.max_results)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return books


@router.post("/sync/seed", response_model=list[BookRead], tags=["sync"])
async def sync_seed(confirm: bool = Query(default=False), book_service: BookService = Depends(get_book_service)) -> list[BookRead]:
    if not confirm:
        raise ValidationError("Confirmación requerida para sincronizar las búsquedas semilla")

    synced_books: list[BookRead] = []
    last_books: list[BookRead] = []
    for query in SEARCH_SEED_QUERIES:
        try:
            last_books = await book_service.sync_from_query(query=query, max_results=5)
            synced_books.extend(last_books)
        except ExternalAPIError as exc:
            raise HTTPException(status_code=502, detail=f"Seed sync failed for {query}: {exc.message}") from exc
    return synced_books
