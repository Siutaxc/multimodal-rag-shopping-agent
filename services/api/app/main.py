"""FastAPI application factory and process entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.assets import router as assets_router
from app.api.assistant import router as assistant_router
from app.api.health import router as health_router
from app.api.multimodal import router as multimodal_router
from app.api.observability import router as observability_router
from app.api.products import router as products_router
from app.api.search import router as search_router
from app.core.observability import RequestObservabilityMiddleware
from app.core.rate_limit import RateLimitMiddleware, create_rate_limit_store
from app.core.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an application with optional deterministic settings for tests."""

    resolved_settings = settings or get_settings()
    logging.basicConfig(
        level=getattr(logging, resolved_settings.log_level),
        format="%(message)s",
    )
    application = FastAPI(
        title="ShopLens API",
        summary="HTTP API for the ShopLens multimodal shopping agent",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).rstrip("/") for origin in resolved_settings.cors_allowed_origins
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    application.add_middleware(
        RateLimitMiddleware,
        settings=resolved_settings,
        store=create_rate_limit_store(resolved_settings),
    )
    application.add_middleware(RequestObservabilityMiddleware)

    if settings is not None:

        def settings_override() -> Settings:
            return resolved_settings

        application.dependency_overrides[get_settings] = settings_override

    application.include_router(health_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(products_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(search_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(assets_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(multimodal_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(assistant_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(observability_router)
    application.include_router(health_router, include_in_schema=False)
    return application


app = create_app()
