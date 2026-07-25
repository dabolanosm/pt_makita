from __future__ import annotations

import asyncio
import json
import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.application.book_service import BookService
from app.config import get_settings
from app.domain.models import Book
from app.errors import ExternalAPIError
from app.infrastructure.db import get_db
from app.infrastructure.external_books_client import GoogleBooksClient

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/interfaces/web/templates")

SEARCH_SEEDS = [
    ("Programación Python", "python programming"),
    ("Ciencia ficción", "science fiction"),
    ("Historia de Colombia", "colombia history"),
    ("Literatura latinoamericana", "latin american literature"),
    ("Desarrollo web", "web development"),
    ("Inteligencia artificial", "artificial intelligence"),
]


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    settings = get_settings()
    books_client = GoogleBooksClient(api_key=settings.google_books_api_key)
    return BookService(db=db, books_client=books_client)


def _parse_json_field(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else [str(parsed)]
    except ValueError:
        return [value]


def _serialize_book(book: Book) -> dict:
    authors = _parse_json_field(book.authors)
    categories = _parse_json_field(book.categories)
    return {
        "id": book.id,
        "title": book.title,
        "authors": authors,
        "authors_text": ", ".join(authors) if authors else "Desconocido",
        "publisher": book.publisher,
        "published_date": book.published_date,
        "description": book.description,
        "page_count": book.page_count,
        "categories": categories,
        "categories_text": ", ".join(categories) if categories else "Ninguna",
        "language": book.language,
        "thumbnail_url": book.thumbnail_url,
        "preview_link": book.preview_link,
    }


@router.get("/")
async def home(
    request: Request,
    book_service: BookService = Depends(get_book_service),
    message: str | None = None,
    error: str | None = None,
    google_results: list[dict] | None = None,
):
    books = [_serialize_book(book) for book in book_service.list_books()]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "books": books,
            "message": message,
            "error": error,
            "google_results": google_results or [],
            "search_seeds": SEARCH_SEEDS,
        },
    )


@router.post("/web/sync")
async def web_sync(
    request: Request,
    query: str = Form(...),
    book_service: BookService = Depends(get_book_service),
):
    if not query or not query.strip():
        return RedirectResponse(url="/?error=Query+no+puede+estar+vacía", status_code=303)
    
    try:
        await book_service.sync_from_query(query=query, max_results=10)
        return RedirectResponse(
            url=f"/?message=Libros+sincronizados+para+{quote(query)}",
            status_code=303,
        )
    except ExternalAPIError as exc:
        logger.error("Sync error: %s", exc.message)
        return RedirectResponse(
            url=f"/?error={quote(exc.message)}",
            status_code=303,
        )
    except Exception as exc:
        logger.error("Unexpected error during sync: %s", exc)
        return RedirectResponse(
            url="/?error=Error+durante+sincronización.+Por+favor+intente+más+tarde",
            status_code=303,
        )


@router.post("/web/sync/{query}")
async def web_sync_shortcut(
    request: Request,
    query: str,
    book_service: BookService = Depends(get_book_service),
):
    try:
        await book_service.sync_from_query(query=query, max_results=10)
        return RedirectResponse(
            url=f"/?message=Libros+sincronizados+para+{quote(query)}",
            status_code=303,
        )
    except ExternalAPIError as exc:
        logger.error("Sync error: %s", exc.message)
        return RedirectResponse(
            url=f"/?error={quote(exc.message)}",
            status_code=303,
        )
    except Exception as exc:
        logger.error("Unexpected error during sync: %s", exc)
        return RedirectResponse(
            url="/?error=Error+durante+sincronización.+Por+favor+intente+más+tarde",
            status_code=303,
        )


@router.post("/web/search/local")
async def search_local(
    request: Request,
    query: str = Form(...),
    book_service: BookService = Depends(get_book_service),
):
    """Search in local library by title, authors, or categories."""
    if not query or not query.strip():
        return RedirectResponse(url="/?error=Query+no+puede+estar+vacía", status_code=303)
    
    try:
        local_books = book_service.search_local(query=query)
        books = [_serialize_book(book) for book in local_books]
        logger.info("Local search completed for query=%s results=%s", query, len(books))
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "books": books,
                "search_query": query,
                "search_seeds": SEARCH_SEEDS,
                "message": f"Encontrados {len(books)} libro(s) en tu biblioteca",
            },
        )
    except Exception as exc:
        logger.error("Error during local search: %s", exc)
        return RedirectResponse(
            url="/?error=Error+durante+búsqueda.+Por+favor+intente+de+nuevo",
            status_code=303,
        )


@router.post("/web/search/google")
async def search_google(
    request: Request,
    query: str = Form(...),
    book_service: BookService = Depends(get_book_service),
):
    """Search Google Books without saving results."""
    if not query or not query.strip():
        return RedirectResponse(url="/?error=Query+no+puede+estar+vacía", status_code=303)
    
    try:
        items = await book_service.search_books(query=query, max_results=10)
        google_results = []
        for item in items:
            volume_info = item.get("volumeInfo", {})
            google_results.append({
                "id": item.get("id"),
                "title": volume_info.get("title", "Desconocido"),
                "authors": volume_info.get("authors", []),
                "description": volume_info.get("description", ""),
                "thumbnail_url": volume_info.get("imageLinks", {}).get("thumbnail"),
                "publisher": volume_info.get("publisher"),
                "published_date": volume_info.get("publishedDate"),
            })
        
        logger.info("Google search completed for query=%s results=%s", query, len(google_results))
        
        # Also get local books for display
        local_books = book_service.list_books()
        books = [_serialize_book(book) for book in local_books]
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "books": books,
                "google_results": google_results,
                "search_query": query,
                "search_seeds": SEARCH_SEEDS,
                "message": f"Encontrados {len(google_results)} resultado(s) en Google Books",
            },
        )
    except ExternalAPIError as exc:
        logger.error("Google search error: %s", exc.message)
        return RedirectResponse(
            url=f"/?error={quote(exc.message)}",
            status_code=303,
        )
    except Exception as exc:
        logger.error("Error during Google search: %s", exc)
        return RedirectResponse(
            url="/?error=Error+durante+búsqueda+en+Google+Books.+Por+favor+intente+más+tarde",
            status_code=303,
        )


@router.post("/web/books/add")
async def add_book(
    request: Request,
    google_id: str = Form(...),
    book_service: BookService = Depends(get_book_service),
):
    """Add a single book from Google Books by ID."""
    if not google_id or not google_id.strip():
        return RedirectResponse(url="/?error=ID+inválido", status_code=303)
    
    try:
        # Get book details from Google
        book_data = await book_service.books_client.get_by_id(google_id)
        if not book_data:
            return RedirectResponse(url="/?error=No+se+encontró+el+libro", status_code=303)
        
        volume_info = book_data.get("volumeInfo", {})
        parsed = book_service._parse_volume_info(volume_info)
        parsed["google_id"] = google_id
        
        # Check if already exists (dedupe by google_id)
        existing = book_service.db.query(Book).filter(Book.google_id == google_id).one_or_none()
        if existing:
            logger.info("Book already exists: google_id=%s", google_id)
            return RedirectResponse(url="/?message=Este+libro+ya+está+en+tu+biblioteca", status_code=303)
        
        # Insert new book
        new_book = Book(**parsed)
        book_service.db.add(new_book)
        book_service.db.commit()
        logger.info("Added book: google_id=%s title=%s", google_id, parsed.get("title"))
        
        return RedirectResponse(url="/?message=Libro+agregado+a+tu+biblioteca", status_code=303)
    except ExternalAPIError as exc:
        logger.error("Error adding book from Google: %s", exc.message)
        return RedirectResponse(
            url=f"/?error={quote(exc.message)}",
            status_code=303,
        )
    except Exception as exc:
        book_service.db.rollback()
        logger.error("Error adding book: %s", exc)
        return RedirectResponse(
            url="/?error=Error+al+agregar+libro.+Por+favor+intente+de+nuevo",
            status_code=303,
        )


@router.post("/web/books/delete-selected")
async def delete_selected(
    request: Request,
    selected_ids: list[str] = Form(...),
    book_service: BookService = Depends(get_book_service),
):
    """Delete multiple books by ID."""
    if not selected_ids:
        return RedirectResponse(url="/?error=No+se+seleccionó+ningún+libro", status_code=303)
    
    try:
        book_ids = [int(bid) for bid in selected_ids if bid.strip()]
        deleted_count = book_service.delete_books(book_ids)
        logger.info("Deleted %d books", deleted_count)
        
        return RedirectResponse(
            url=f"/?message={deleted_count}+libro(s)+eliminado(s)",
            status_code=303,
        )
    except Exception as exc:
        logger.error("Error deleting books: %s", exc)
        return RedirectResponse(
            url="/?error=Error+al+eliminar+libros.+Por+favor+intente+de+nuevo",
            status_code=303,
        )


@router.post("/web/library/clear")
async def clear_library(
    request: Request,
    book_service: BookService = Depends(get_book_service),
):
    """Clear all books from the library."""
    try:
        deleted_count = book_service.delete_all_books()
        logger.info("Cleared entire library: deleted %d books", deleted_count)
        
        return RedirectResponse(
            url="/?message=Biblioteca+limpiada.+Se+eliminaron+%d+libro(s)" % deleted_count,
            status_code=303,
        )
    except Exception as exc:
        logger.error("Error clearing library: %s", exc)
        return RedirectResponse(
            url="/?error=Error+al+limpiar+biblioteca.+Por+favor+intente+de+nuevo",
            status_code=303,
        )


@router.get("/books/{book_id}")
async def book_detail(
    request: Request,
    book_id: int,
    book_service: BookService = Depends(get_book_service),
):
    book = book_service.get_book(book_id=book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse(
        "book_detail.html",
        {"request": request, "book": _serialize_book(book)},
    )


@router.post("/web/books/{book_id}/delete")
async def delete_book(book_id: int, book_service: BookService = Depends(get_book_service)):
    deleted = book_service.delete_book(book_id=book_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")
    return RedirectResponse(url="/?message=Libro+eliminado", status_code=303)
