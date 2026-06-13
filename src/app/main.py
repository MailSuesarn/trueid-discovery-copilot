"""FastAPI application factory. Exposes `app` so the notebook can `from app.main import app`."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.middleware import RateLimitMiddleware, RequestIdMiddleware
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    application = FastAPI(title=settings.app.name, version="0.1.0")
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(RequestIdMiddleware)
    application.include_router(router)
    return application


app = create_app()
