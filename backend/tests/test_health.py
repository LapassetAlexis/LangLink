"""REQ-PLT-07 — sondes de vivacité et de disponibilité."""

from __future__ import annotations

import app.api.health as health_module
import pytest
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
async def client() -> AsyncClient:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_healthz_does_not_touch_the_database(client: AsyncClient) -> None:
    response = await client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]
    assert "uptime_s" in body


@pytest.mark.asyncio
async def test_readyz_reports_database_ok(client: AsyncClient) -> None:
    response = await client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["db"] == "ok"


@pytest.mark.asyncio
async def test_readyz_returns_503_when_database_is_down(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom() -> None:
        raise RuntimeError("connexion refusée")

    monkeypatch.setattr(health_module, "get_sessionmaker", _boom)

    response = await client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["db"] == "down"
    assert body["error"] == "RuntimeError"
