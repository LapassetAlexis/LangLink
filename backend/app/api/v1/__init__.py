"""Agrégateur des routeurs métier de l'API v1."""

from app.api.v1.auth.router import router as auth_router
from app.api.v1.corrections.router import router as corrections_router
from app.api.v1.discovery.router import router as discovery_router
from app.api.v1.language.router import router as language_router
from app.api.v1.matching.router import router as matching_router
from app.api.v1.media.router import router as media_router
from app.api.v1.messaging.router import router as messaging_router
from app.api.v1.onboarding.router import router as onboarding_router
from app.api.v1.safety.router import router as safety_router
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(discovery_router)
api_router.include_router(matching_router)
api_router.include_router(messaging_router)
api_router.include_router(corrections_router)
api_router.include_router(language_router)
api_router.include_router(safety_router)
api_router.include_router(media_router)

__all__ = ["api_router"]
