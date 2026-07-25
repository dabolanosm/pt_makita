from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.infrastructure.db import get_db

router = APIRouter()


@router.get("/health", tags=["health"])
async def health(settings=Depends(get_settings)) -> dict[str, str]:
    if not settings.google_books_api_key:
        raise HTTPException(status_code=500, detail="Google Books API key is not configured")
    return {"status": "ok", "version": "0.1.0"}


@router.get("/health/db", tags=["health"])
async def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Database connection failed") from exc
    return {"status": "ok", "database": "connected"}
