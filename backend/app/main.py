"""Fabrique d'application FastAPI."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.errors import install_error_handlers
from app.core.middleware import DEFAULT_LIMITS, RateLimitMiddleware, RequestContextMiddleware

API_PREFIX = "/api/v1"

DESCRIPTION = (
    "Plateforme de correspondance linguistique asynchrone. "
    "Aucune IA generative dans le produit : traduction deterministe, correction humaine."
)


def create_app(
    settings: Settings | None = None,
    *,
    rate_limits: dict[tuple[str, str], tuple[int, int]] | None = None,
) -> FastAPI:
    """Construit l'application à partir des réglages validés."""
    config = settings or get_settings()

    app = FastAPI(
        title="LangLink API",
        version=__version__,
        description=DESCRIPTION,
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    app.state.settings = config

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Ordre d'exécution inverse de l'ordre d'ajout : le contexte de requête doit englober
    # le rate limiting pour que même un 429 porte un X-Request-Id.
    app.add_middleware(RateLimitMiddleware, limits=rate_limits or DEFAULT_LIMITS)
    app.add_middleware(RequestContextMiddleware)

    install_error_handlers(app)
    app.include_router(health_router)

    return app


def app_factory() -> FastAPI:
    """Point d'entrée uvicorn (`--factory app.main:app_factory`)."""
    return create_app()
