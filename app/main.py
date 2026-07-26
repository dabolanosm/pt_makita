from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.errors import ExternalAPIError, NotFoundError, ValidationError
from app.infrastructure.db import init_db
from app.interfaces.api.books import router as books_router
from app.interfaces.api.health import router as health_router
from app.interfaces.api.sync import router as sync_router
from app.interfaces.web.routes import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    init_db()
    yield


def _json_error_response(message: str, error_type: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": message, "type": error_type})


async def _external_api_error_handler(request: Request, exc: ExternalAPIError) -> JSONResponse:
    logging.getLogger("app").error("ExternalAPIError: %s", exc.message)
    return _json_error_response(exc.message, "ExternalAPIError", exc.status_code)


async def _not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    logging.getLogger("app").warning("NotFoundError: %s", exc.message)
    return _json_error_response(exc.message, "NotFoundError", exc.status_code)


async def _validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    logging.getLogger("app").warning("ValidationError: %s", exc.message)
    return _json_error_response(exc.message, "ValidationError", exc.status_code)


async def _fastapi_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logging.getLogger("app").warning("FastAPI validation failed: %s", exc)
    return _json_error_response("Solicitud inválida", "RequestValidationError", 422)


def create_app() -> FastAPI:
    app = FastAPI(title="Book Library Sync", version="0.1.0", lifespan=lifespan)
    static_dir = Path(__file__).resolve().parent / "interfaces" / "web" / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.add_exception_handler(ExternalAPIError, _external_api_error_handler)
    app.add_exception_handler(NotFoundError, _not_found_error_handler)
    app.add_exception_handler(ValidationError, _validation_error_handler)
    app.add_exception_handler(RequestValidationError, _fastapi_validation_error_handler)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger = logging.getLogger("app")
        start = time.time()
        logger.info("Request start %s %s", request.method, request.url.path)
        response = await call_next(request)
        elapsed_ms = int((time.time() - start) * 1000)
        logger.info("Request end %s %s status=%s duration_ms=%s", request.method, request.url.path, response.status_code, elapsed_ms)
        return response

    app.include_router(health_router)
    app.include_router(books_router, prefix="/api")
    app.include_router(sync_router, prefix="/api")
    app.include_router(web_router)

    # TODO: Routers de la API se montarán aquí en P2/P3

    return app


app = create_app()
