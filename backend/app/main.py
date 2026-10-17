"""Fabrique d'application FastAPI.

Aucune route métier ici : les routeurs par domaine sont montés au fil des lots
(`app/api/v1/<domaine>/router.py`). Les sondes `/healthz` et `/readyz` arrivent au lot 2.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import Settings, get_settings

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construit l'application à partir des réglages validés."""
    config = settings or get_settings()

    app = FastAPI(
        title="LangLink API",
        version=__version__,
        description="Plateforme de correspondance linguistique asynchrone.",
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

    return app


app = create_app
