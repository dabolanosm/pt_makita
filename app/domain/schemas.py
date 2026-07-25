from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict


class BookCreate(BaseModel):
    google_id: Optional[str] = None
    title: str
    authors: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    description: Optional[str] = None
    page_count: Optional[int] = None
    categories: Optional[str] = None
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_link: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    description: Optional[str] = None
    page_count: Optional[int] = None
    categories: Optional[str] = None
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_link: Optional[str] = None


class BookRead(BaseModel):
    id: int
    google_id: Optional[str] = None
    title: str
    authors: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    description: Optional[str] = None
    page_count: Optional[int] = None
    categories: Optional[str] = None
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_link: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
