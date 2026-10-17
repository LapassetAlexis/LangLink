"""Erreurs de domaine et rendu `application/problem+json` (RFC 9457).

La couche services lève des exceptions métier ; un seul endroit les traduit en HTTP.
Les codes `type` sont stables et font partie du contrat d'API (cf. core.spec.md §5.1).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM_MEDIA_TYPE = "application/problem+json"


class DomainError(Exception):
    """Erreur métier traduisible en problème HTTP."""

    status: int = 400
    type: str = "about:blank"
    title: str = "Requête invalide"

    def __init__(
        self,
        detail: str | None = None,
        *,
        errors: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(detail or self.title)
        self.detail = detail
        self.errors = errors or []
        self.headers = headers or {}


class Unauthorized(DomainError):
    status, type, title = 401, "auth.unauthenticated", "Authentification requise"


class InvalidCredentials(DomainError):
    status, type, title = 401, "auth.invalid_credentials", "Identifiants invalides"


class TokenExpired(DomainError):
    status, type, title = 401, "auth.token_expired", "Session expirée"


class Forbidden(DomainError):
    status, type, title = 403, "auth.forbidden", "Accès refusé"


class Blocked(DomainError):
    status, type, title = 403, "safety.blocked", "Interaction bloquée"


class NotFound(DomainError):
    status, type, title = 404, "resource.not_found", "Ressource introuvable"


class Conflict(DomainError):
    status, type, title = 409, "resource.conflict", "Conflit d'état"


class Unprocessable(DomainError):
    status, type, title = 422, "request.unprocessable", "Données invalides"


class PayloadTooLarge(DomainError):
    status, type, title = 413, "request.payload_too_large", "Fichier trop volumineux"


class UnsupportedMedia(DomainError):
    status, type, title = 415, "request.unsupported_media", "Format non supporté"


class RateLimited(DomainError):
    status, type, title = 429, "rate.limited", "Trop de requêtes"


class ProviderUnavailable(DomainError):
    status, type, title = 503, "language.provider_unavailable", "Service indisponible"


def problem_payload(
    *,
    type_: str,
    title: str,
    status: int,
    detail: str | None,
    instance: str,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "instance": instance,
    }
    if detail:
        payload["detail"] = detail
    if errors:
        payload["errors"] = errors
    return payload


def install_error_handlers(app: FastAPI) -> None:
    """Branche les gestionnaires d'erreurs sur l'application."""

    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            problem_payload(
                type_=exc.type,
                title=exc.title,
                status=exc.status,
                detail=exc.detail,
                instance=str(request.url.path),
                errors=exc.errors,
            ),
            status_code=exc.status,
            media_type=PROBLEM_MEDIA_TYPE,
            headers=exc.headers or None,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(part) for part in error.get("loc", ()) if part != "body"),
                "code": error.get("type", "invalid"),
                "message": error.get("msg", ""),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            problem_payload(
                type_="request.validation_failed",
                title="Données invalides",
                status=422,
                detail="Un ou plusieurs champs sont invalides.",
                instance=str(request.url.path),
                errors=errors,
            ),
            status_code=422,
            media_type=PROBLEM_MEDIA_TYPE,
        )
