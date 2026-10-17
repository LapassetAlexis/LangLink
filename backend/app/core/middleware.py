"""Middlewares transverses : identifiant de requête, journalisation JSON, rate limiting."""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from app.core.ids import uuid7
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger("langlink.access")

# (méthode, chemin) -> (max requêtes, fenêtre en secondes). Complété par les routeurs.
DEFAULT_LIMITS: dict[tuple[str, str], tuple[int, int]] = {
    ("POST", "/api/v1/auth/register"): (5, 60),
    ("POST", "/api/v1/auth/login"): (10, 900),
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Ajoute `X-Request-Id` et journalise une ligne JSON par requête."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid7())
        request.state.request_id = request_id
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                json.dumps(
                    {
                        "event": "request_failed",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    }
                )
            )
            raise

        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        response.headers["X-Request-Id"] = request_id
        logger.info(
            json.dumps(
                {
                    "event": "request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
        )
        return response


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fenêtre glissante en mémoire, par (route, client).

    Suffisant pour une instance unique (le MVP vise une seule machine) ; une montée en
    charge imposerait Redis, ce qui est explicitement hors périmètre V1.
    """

    def __init__(
        self, app: ASGIApp, limits: dict[tuple[str, str], tuple[int, int]] | None = None
    ) -> None:
        super().__init__(app)
        self.limits = dict(limits or DEFAULT_LIMITS)
        self._hits: dict[tuple[str, str, str], deque[float]] = defaultdict(deque)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rule = self.limits.get((request.method, request.url.path))
        if rule is None:
            return await call_next(request)

        max_requests, window = rule
        client = _client_key(request)
        key = (request.method, request.url.path, client)
        now = time.monotonic()
        hits = self._hits[key]

        while hits and now - hits[0] >= window:
            hits.popleft()

        remaining = max(0, max_requests - len(hits))
        if len(hits) >= max_requests:
            retry_after = max(1, int(window - (now - hits[0])))
            from app.core.errors import problem_payload  # import local : évite un cycle

            return Response(
                content=json.dumps(
                    problem_payload(
                        type_="rate.limited",
                        title="Trop de requêtes",
                        status=429,
                        detail=f"Réessayez dans {retry_after} secondes.",
                        instance=request.url.path,
                    )
                ),
                status_code=429,
                media_type="application/problem+json",
                headers={
                    "Retry-After": str(retry_after),
                    "RateLimit-Limit": str(max_requests),
                    "RateLimit-Remaining": "0",
                    "RateLimit-Reset": str(retry_after),
                },
            )

        hits.append(now)
        response = await call_next(request)
        response.headers["RateLimit-Limit"] = str(max_requests)
        response.headers["RateLimit-Remaining"] = str(max(0, remaining - 1))
        response.headers["RateLimit-Reset"] = str(window)
        return response
