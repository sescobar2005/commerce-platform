"""FastAPI application entry point for Plataforma de Comercio.

Assembles all API routers into a single FastAPI application.
"""

import json
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.auth.router import router as auth_router
from src.core.cart.router import router as cart_router
from src.core.categories.router import router as categories_router
from src.core.config import settings
from src.core.products.router import router as products_router
from src.core.sellers.router import router as sellers_router


def _parse_cors_origins(value: str) -> list[str]:
    """Parse CORS origins from a configuration string.

    Accepts a JSON array string (e.g. '["http://localhost:3000"]')
    or a comma-separated string (e.g. 'http://localhost:3000,http://localhost:8000').
    """
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(origin) for origin in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Registers all API routers under the /api/v1 prefix and configures
    CORS using the application settings.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Plataforma de Comercio - E-commerce backend",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(settings.BACKEND_CORS_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(sellers_router, prefix="/api/v1")
    app.include_router(products_router, prefix="/api/v1")
    app.include_router(categories_router, prefix="/api/v1")
    app.include_router(cart_router, prefix="/api/v1")

    return app


app = create_app()
