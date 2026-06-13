"""FastAPI application factory. Exposes `app` so the notebook can `from app.main import app`."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    application = FastAPI(title=settings.app.name, version="0.1.0")
    application.include_router(router)
    # TODO(claude-code, Phase 5): add RequestId + PII-redaction + rate-limit middleware.
    return application


app = create_app()
