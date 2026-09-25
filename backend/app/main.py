"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=__version__,
        description="Dispute Management System — REST API. All responses use the standard envelope "
        "`{success, data, message, error_code}`.",
        docs_url=f"{settings.api_prefix}/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url=f"{settings.api_prefix}/openapi.json" if settings.docs_enabled else None,
    )

    if settings.cors_origins:  # development only (e.g. `flutter run` on another port)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID", settings.client_header_name],
            expose_headers=["X-Request-ID"],
        )
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    logger.info(
        "API started",
        extra={"environment": settings.app_env, "version": __version__, "auth_provider": settings.auth_provider},
    )
    return app


app = create_app()
