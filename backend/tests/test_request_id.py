"""REQ-PLT-07 — traçabilité des requêtes par `X-Request-Id` et journal JSON."""

from __future__ import annotations

import json
import logging

import pytest
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
async def client() -> AsyncClient:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_each_request_gets_a_distinct_id(client: AsyncClient) -> None:
    first = await client.get("/healthz")
    second = await client.get("/healthz")

    id_a = first.headers["X-Request-Id"]
    id_b = second.headers["X-Request-Id"]
    assert id_a and id_b
    assert id_a != id_b


@pytest.mark.asyncio
async def test_incoming_request_id_is_preserved(client: AsyncClient) -> None:
    response = await client.get("/healthz", headers={"X-Request-Id": "trace-42"})

    assert response.headers["X-Request-Id"] == "trace-42"


@pytest.mark.asyncio
async def test_access_log_is_json_with_request_id(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="langlink.access")

    response = await client.get("/readyz")
    request_id = response.headers["X-Request-Id"]

    lines = [json.loads(record.message) for record in caplog.records if record.name == "langlink.access"]
    matching = [line for line in lines if line.get("request_id") == request_id]
    assert matching, lines
    entry = matching[0]
    assert entry["event"] == "request"
    assert entry["path"] == "/readyz"
    assert entry["status"] == 200
    assert isinstance(entry["duration_ms"], float)
