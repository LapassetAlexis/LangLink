"""REQ-PLT-02 / tâche 2.4 — tout refus est un `application/problem+json` explicite.

Les routes de test sont ajoutées localement à une application fraîche : on vérifie le
gestionnaire d'erreurs réel, pas une imitation.
"""

from __future__ import annotations

import pytest
from app.core.errors import Blocked, Conflict, Forbidden, NotFound
from app.main import create_app
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel


class Payload(BaseModel):
    age: int


def _build_app() -> FastAPI:
    app = create_app(rate_limits={("GET", "/_test/limited"): (2, 60)})

    @app.get("/_test/conflict")
    async def conflict() -> None:
        raise Conflict("Le match est déjà fermé.")

    @app.get("/_test/forbidden")
    async def forbidden() -> None:
        raise Forbidden("Réservé à l'auteur du message.")

    @app.get("/_test/missing")
    async def missing() -> None:
        raise NotFound("Match introuvable.")

    @app.get("/_test/blocked")
    async def blocked() -> None:
        raise Blocked("Vous avez bloqué ce profil.")

    @app.post("/_test/validate")
    async def validate(payload: Payload) -> dict[str, int]:
        return {"age": payload.age}

    @app.get("/_test/limited")
    async def limited() -> dict[str, bool]:
        return {"ok": True}

    return app


@pytest.fixture()
async def client() -> AsyncClient:
    transport = ASGITransport(app=_build_app())
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_conflict_returns_problem_json(client: AsyncClient) -> None:
    response = await client.get("/_test/conflict")

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "resource.conflict"
    assert body["status"] == 409
    assert body["detail"] == "Le match est déjà fermé."
    assert body["instance"] == "/_test/conflict"


@pytest.mark.asyncio
async def test_forbidden_and_not_found_and_blocked(client: AsyncClient) -> None:
    forbidden = await client.get("/_test/forbidden")
    missing = await client.get("/_test/missing")
    blocked = await client.get("/_test/blocked")

    assert forbidden.status_code == 403
    assert missing.status_code == 404
    assert missing.json()["type"] == "resource.not_found"
    assert blocked.status_code == 403
    assert blocked.json()["type"] == "safety.blocked"


@pytest.mark.asyncio
async def test_validation_error_lists_fields(client: AsyncClient) -> None:
    response = await client.post("/_test/validate", json={"age": "pas un entier"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "request.validation_failed"
    assert body["errors"][0]["field"] == "age"


@pytest.mark.asyncio
async def test_rate_limit_headers_and_429(client: AsyncClient) -> None:
    first = await client.get("/_test/limited")
    second = await client.get("/_test/limited")
    third = await client.get("/_test/limited")

    assert first.status_code == 200
    assert first.headers["RateLimit-Limit"] == "2"
    assert second.status_code == 200
    assert second.headers["RateLimit-Remaining"] == "0"
    assert third.status_code == 429
    assert third.headers["Retry-After"].isdigit()
    assert third.json()["type"] == "rate.limited"
