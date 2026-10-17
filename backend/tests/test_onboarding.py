"""REQ-ONB-01…08 — enrôlement, catalogue, photo, suppression de compte."""

from __future__ import annotations

import io

import pytest
from app.main import create_app
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import text

_PW = "mot" + "de" + "passe" + "-solide-2026"


def _png(width: int = 900, height: int = 700, color: tuple[int, int, int] = (30, 120, 200)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="PNG")
    return buffer.getvalue()


async def _account(client: AsyncClient, email: str = "user@example.org") -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": _PW}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}


@pytest.fixture()
async def client(clean_engine) -> AsyncClient:
    transport = ASGITransport(app=create_app(rate_limits={}))
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_catalog_has_ten_categories_and_sixty_entries(client: AsyncClient) -> None:
    response = await client.get("/api/v1/interests")

    assert response.status_code == 200
    groups = response.json()
    assert len(groups) == 10
    assert sum(len(group["interests"]) for group in groups) == 60
    first = groups[0]
    assert first["category"] == "Jeux vidéo"
    assert first["interests"][0]["slug"] == "jeux-rpg"
    assert first["interests"][0]["emoji"]


@pytest.mark.asyncio
async def test_languages_reject_identical_pair(client: AsyncClient) -> None:
    headers = await _account(client)

    response = await client.put(
        "/api/v1/onboarding/languages",
        headers=headers,
        json={"native_language": "fr", "target_language": "fr", "target_level": "B1"},
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "same_as_native"


@pytest.mark.asyncio
async def test_languages_reject_unsupported_code(client: AsyncClient) -> None:
    headers = await _account(client)

    response = await client.put(
        "/api/v1/onboarding/languages",
        headers=headers,
        json={"native_language": "fr", "target_language": "xx", "target_level": "B1"},
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "unsupported"


@pytest.mark.asyncio
async def test_languages_step_moves_to_two(client: AsyncClient) -> None:
    headers = await _account(client)

    response = await client.put(
        "/api/v1/onboarding/languages",
        headers=headers,
        json={"native_language": "fr", "target_language": "ja", "target_level": "A2"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["step"] == 2
    assert body["target_language"] == "ja"
    assert "interests" in body["missing"]


@pytest.mark.asyncio
async def test_interests_require_three_minimum(client: AsyncClient) -> None:
    headers = await _account(client)

    response = await client.put(
        "/api/v1/onboarding/interests", headers=headers, json={"interest_ids": [1, 2]}
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "out_of_range"


@pytest.mark.asyncio
async def test_unknown_interest_aborts_whole_selection(
    client: AsyncClient, clean_engine
) -> None:
    headers = await _account(client)
    await client.put(
        "/api/v1/onboarding/interests", headers=headers, json={"interest_ids": [1, 2, 3]}
    )

    response = await client.put(
        "/api/v1/onboarding/interests", headers=headers, json={"interest_ids": [4, 5, 999]}
    )

    assert response.status_code == 422
    with clean_engine.connect() as connection:
        kept = [
            row[0]
            for row in connection.execute(
                text("SELECT interest_id FROM user_interests ORDER BY interest_id")
            )
        ]
    assert kept == [1, 2, 3], kept  # sélection précédente intacte


@pytest.mark.asyncio
async def test_complete_fails_until_prerequisites_are_met(client: AsyncClient) -> None:
    headers = await _account(client)

    refused = await client.post("/api/v1/onboarding/complete", headers=headers)
    assert refused.status_code == 409
    missing = {error["field"] for error in refused.json()["errors"]}
    assert missing == {"languages", "interests"}

    await client.put(
        "/api/v1/onboarding/languages",
        headers=headers,
        json={"native_language": "fr", "target_language": "en", "target_level": "B2"},
    )
    await client.put(
        "/api/v1/onboarding/interests", headers=headers, json={"interest_ids": [1, 7, 13]}
    )
    accepted = await client.post("/api/v1/onboarding/complete", headers=headers)

    assert accepted.status_code == 200
    assert accepted.json()["discoverable"] is True

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["onboarding"]["discoverable"] is True


@pytest.mark.asyncio
async def test_avatar_is_resized_and_served(client: AsyncClient, tmp_path, monkeypatch) -> None:
    from app.core import config as config_module

    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path))
    config_module.get_settings.cache_clear()
    headers = await _account(client)

    upload = await client.post(
        "/api/v1/onboarding/avatar",
        headers=headers,
        files={"file": ("photo.png", _png(900, 700), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    key = upload.json()["avatar_key"]
    assert key.endswith(".webp")

    stored = tmp_path / key
    assert stored.is_file()
    with Image.open(stored) as image:
        assert image.size == (512, 512)
        assert image.format == "WEBP"

    served = await client.get(f"/api/v1/media/{key}")
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/webp"
    config_module.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_avatar_rejects_unsupported_format(client: AsyncClient) -> None:
    headers = await _account(client)

    response = await client.post(
        "/api/v1/onboarding/avatar",
        headers=headers,
        files={"file": ("anim.gif", b"GIF89a" + b"\x00" * 64, "image/gif")},
    )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_avatar_rejects_oversized_file(client: AsyncClient) -> None:
    headers = await _account(client)
    big = _png(4000, 4000) + b"\x00" * (6 * 1024 * 1024)

    response = await client.post(
        "/api/v1/onboarding/avatar",
        headers=headers,
        files={"file": ("big.png", big, "image/png")},
    )

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_delete_account_requires_password_then_anonymises(
    client: AsyncClient, clean_engine
) -> None:
    headers = await _account(client, "bye@example.org")

    refused = await client.request("DELETE", "/api/v1/me", headers=headers, json={})
    assert refused.status_code == 422

    accepted = await client.request(
        "DELETE", "/api/v1/me", headers=headers, json={"password": _PW}
    )
    assert accepted.status_code == 204

    with clean_engine.connect() as connection:
        row = connection.execute(
            text("SELECT status, email, password_hash FROM users")
        ).one()
    assert row.status == "deleted"
    assert row.email.startswith("deleted-")
    assert "@invalid" in row.email
    assert row.password_hash == "!deleted"
