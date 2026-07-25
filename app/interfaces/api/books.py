from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.application.book_service import BookService
from app.domain.schemas import BookCreate, BookRead, BookUpdate
from app.infrastructure.db import get_db
from app.infrastructure.external_books_client import GoogleBooksClient
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    settings = get_settings()
    books_client = GoogleBooksClient(api_key=settings.google_books_api_key)
    return BookService(db=db, books_client=books_client)


@router.get("/books", response_model=list[BookRead], tags=["books"])
async def list_books(book_service: BookService = Depends(get_book_service)) -> list[BookRead]:
    books = book_service.list_books()
    return books


@router.get("/books/{book_id}", response_model=BookRead, tags=["books"])
async def get_book(book_id: int, book_service: BookService = Depends(get_book_service)) -> BookRead:
    book = book_service.get_book(book_id=book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/books", response_model=BookRead, status_code=201, tags=["books"])
async def create_book(book_data: BookCreate, book_service: BookService = Depends(get_book_service)) -> BookRead:
    book = book_service.create_book(data=book_data)
    return book


@router.put("/books/{book_id}", response_model=BookRead, tags=["books"])
async def update_book(book_id: int, book_data: BookUpdate, book_service: BookService = Depends(get_book_service)) -> BookRead:
    book = book_service.update_book(book_id=book_id, data=book_data)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.delete("/books/{book_id}", status_code=204, tags=["books"])
async def delete_book(book_id: int, book_service: BookService = Depends(get_book_service)) -> Response:
    deleted = book_service.delete_book(book_id=book_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")
    return Response(status_code=204)


@router.delete("/books", status_code=200, tags=["books"])
async def delete_all_books(book_service: BookService = Depends(get_book_service)) -> dict[str, int]:
    """Delete all books from the library. Returns count of deleted books."""
    deleted_count = book_service.delete_all_books()
    logger.info("Deleted all books via API: count=%d", deleted_count)
    return {"deleted": deleted_count}
