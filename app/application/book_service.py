from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import Book
from app.domain.schemas import BookCreate, BookUpdate
from app.infrastructure.external_books_client import GoogleBooksClient

logger = logging.getLogger(__name__)


class BookService:
    def __init__(self, db: Session, books_client: GoogleBooksClient) -> None:
        self.db = db
        self.books_client = books_client

    def list_books(self, skip: int = 0, limit: int = 50) -> list[Book]:
        """List all books with pagination."""
        return self.db.query(Book).offset(skip).limit(limit).all()

    def get_book(self, book_id: int) -> Optional[Book]:
        """Get a book by ID."""
        return self.db.query(Book).filter(Book.id == book_id).one_or_none()

    def search_local(self, query: str) -> list[Book]:
        """Search in local library by title, authors, or categories (case-insensitive)."""
        q_lower = f"%{query.lower()}%"
        return self.db.query(Book).filter(
            (Book.title.ilike(q_lower)) |
            (Book.authors.ilike(q_lower)) |
            (Book.categories.ilike(q_lower))
        ).all()

    def create_book(self, data: BookCreate) -> Book:
        """Create a new book."""
        book = Book(**data.model_dump())
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        logger.info("Created book: id=%s title=%s", book.id, book.title)
        return book

    def update_book(self, book_id: int, data: BookUpdate) -> Optional[Book]:
        """Update an existing book."""
        book = self.get_book(book_id=book_id)
        if book is None:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(book, field, value)
        book.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(book)
        logger.info("Updated book: id=%s", book_id)
        return book

    def delete_book(self, book_id: int) -> bool:
        """Delete a single book by ID. Returns True if deleted, False if not found."""
        book = self.get_book(book_id)
        if book:
            self.db.delete(book)
            self.db.commit()
            logger.info("Deleted book id=%s", book_id)
            return True
        return False

    def delete_books(self, book_ids: list[int]) -> int:
        """Delete multiple books by IDs. Returns count of deleted books."""
        deleted_count = 0
        try:
            for book_id in book_ids:
                book = self.get_book(book_id)
                if book:
                    self.db.delete(book)
                    deleted_count += 1
            self.db.commit()
            logger.info("Deleted %d books", deleted_count)
        except Exception:
            self.db.rollback()
            raise
        return deleted_count

    def delete_all_books(self) -> int:
        """Delete all books from the library. Returns count of deleted books."""
        try:
            count = self.db.query(Book).count()
            self.db.query(Book).delete()
            self.db.commit()
            logger.info("Deleted all %d books", count)
            return count
        except Exception:
            self.db.rollback()
            raise

    async def search_books(self, query: str, max_results: int = 10) -> list[dict]:
        """Search books in Google Books API."""
        return await self.books_client.search(query=query, max_results=max_results)

    async def sync_from_query(self, query: str, max_results: int = 10) -> list[Book]:
        """Sync books from Google Books query with deduplication and transactional persistence."""
        if max_results > 10:
            raise ValueError("max_results must be 10 or less")

        items = await self.books_client.search(query=query, max_results=max_results)

        saved_books: list[Book] = []
        new_count = 0
        updated_count = 0
        start = datetime.utcnow()

        try:
            seen_google_ids: set[str] = set()
            for item in items:
                google_id = item.get("id")
                if google_id is None or google_id in seen_google_ids:
                    continue
                seen_google_ids.add(google_id)

                volume_info = item.get("volumeInfo", {})
                parsed = self._parse_volume_info(volume_info)
                parsed["google_id"] = google_id

                book = self.db.query(Book).filter(Book.google_id == google_id).one_or_none()
                if book is None:
                    book = Book(**parsed)
                    self.db.add(book)
                    self.db.flush()
                    new_count += 1
                else:
                    for key, value in parsed.items():
                        setattr(book, key, value)
                    book.updated_at = datetime.utcnow()
                    updated_count += 1
                saved_books.append(book)

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        finally:
            elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            logger.info(
                "Sync completed query=%s results=%s new=%s updated=%s elapsed_ms=%s",
                query,
                len(items),
                new_count,
                updated_count,
                elapsed_ms,
            )
        
        return saved_books

    def _parse_volume_info(self, volume_info: dict) -> dict:
        """Parse Google Books volumeInfo into Book fields."""
        image_links = volume_info.get("imageLinks", {}) or {}
        thumbnail_url = self._select_best_thumbnail(image_links)

        return {
            "title": volume_info.get("title", "Unknown"),
            "authors": json.dumps(volume_info.get("authors", [])),
            "publisher": volume_info.get("publisher"),
            "published_date": volume_info.get("publishedDate"),
            "description": volume_info.get("description"),
            "page_count": volume_info.get("pageCount"),
            "categories": json.dumps(volume_info.get("categories", [])),
            "language": volume_info.get("language", "en"),
            "thumbnail_url": thumbnail_url,
            "preview_link": volume_info.get("previewLink"),
        }

    def _select_best_thumbnail(self, image_links: dict) -> Optional[str]:
        """Pick the highest-quality available thumbnail from Google Books image links."""
        for key in ("extraLarge", "large", "medium", "small", "thumbnail", "smallThumbnail"):
            value = image_links.get(key)
            if value:
                return value
        return None
