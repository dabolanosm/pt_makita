from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_books_api_key: str = ""
    database_url: str = "sqlite:///./data/books.db"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    if settings.database_url.startswith("sqlite"):
        db_url = settings.database_url
        if db_url.startswith("sqlite:///./") or db_url.startswith("sqlite:///"):
            db_path_str = db_url.removeprefix("sqlite:///")
            db_path_str = db_path_str.replace("/./", "/")
            db_path = Path(db_path_str)
            if not db_path.is_absolute():
                db_path = (Path(__file__).resolve().parent.parent / db_path).resolve()
            settings.database_url = f"sqlite:///{db_path}"
    return settings
