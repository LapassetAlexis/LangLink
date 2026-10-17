"""Sondes d'exploitation : vivacité et disponibilité."""

from __future__ import annotations

import time

from app import __version__
from app.db.session import get_sessionmaker
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

router = APIRouter(tags=["platform"])
STARTED_AT = time.time()


@router.get("/healthz", summary="Vivacité du processus")
async def healthz() -> dict[str, str | float]:
    """Le processus répond : aucune dépendance n'est interrogée."""
    return {"status": "ok", "version": __version__, "uptime_s": round(time.time() - STARTED_AT, 1)}


@router.get("/readyz", summary="Disponibilité (base incluse)")
async def readyz() -> JSONResponse:
    """Vérifie la base ; renvoie 503 si elle ne répond pas."""
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - toute panne doit être signalée, pas propagée
        return JSONResponse(
            {"status": "unavailable", "db": "down", "error": type(exc).__name__},
            status_code=503,
        )
    return JSONResponse({"status": "ok", "db": "ok", "version": __version__})
