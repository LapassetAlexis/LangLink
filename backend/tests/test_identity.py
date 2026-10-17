"""REQ-IDN-01/02/03 — inscription, sessions rotatives, OAuth, anti-énumération."""

from __future__ import annotations

import uuid

import pytest
from app.main import create_app
from app.services import oauth as oauth_service
from app.services.oauth import Identity
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

_PW = "un-mot-de-passe-solide"


def _app(rate_limits=None):
    return create_app(rate_limits={} if rate_limits is None else rate_limits)


@pytest.fixture()
async def client(clean_engine) -> AsyncClient:
    transport = ASGITransport(app=_app())
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def _register(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": _PW}
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_register_creates_user_and_empty_profile(client: AsyncClient, clean_engine) -> None:
    body = await _register(client, "Alice@Example.org")

    assert body["user"]["email"] == "alice@example.org"  # normalisé
    assert body["user"]["email_verified"] is False
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900

    with clean_engine.connect() as connection:
        profile = connection.execute(
            text("SELECT display_name, onboarding_step, discoverable FROM profiles")
        ).one()
    assert profile.onboarding_step == 1
    assert profile.discoverable is False
    assert profile.display_name


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email_case_insensitive(client: AsyncClient) -> None:
    await _register(client, "bob@example.org")

    response = await client.post(
        "/api/v1/auth/register", json={"email": "BOB@example.org", "password": _PW}
    )

    assert response.status_code == 409
    assert response.json()["type"] == "resource.conflict"
    assert response.json()["errors"][0]["code"] == "email_taken"


@pytest.mark.asyncio
async def test_register_rejects_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"email": "weak@example.org", "password": "court"}
    )

    assert response.status_code in (422,)
    assert any(e["field"] == "password" for e in response.json().get("errors", []))


@pytest.mark.asyncio
async def test_login_is_indistinguishable_for_unknown_email(client: AsyncClient) -> None:
    await _register(client, "carol@example.org")

    wrong_password = await client.post(
        "/api/v1/auth/login", json={"email": "carol@example.org", "password": "mauvais-mdp-1"}
    )
    unknown_email = await client.post(
        "/api/v1/auth/login", json={"email": "inconnu@example.org", "password": _PW}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["type"] == unknown_email.json()["type"]
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_rotates_and_reuse_revokes_everything(client: AsyncClient) -> None:
    await _register(client, "dave@example.org")
    first_refresh = client.cookies.get("refresh_token")
    assert first_refresh

    rotated = await client.post("/api/v1/auth/refresh")
    assert rotated.status_code == 200
    second_refresh = client.cookies.get("refresh_token")
    assert second_refresh and second_refresh != first_refresh

    # Rejeu de l'ancien jeton : toutes les sessions tombent
    async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://test") as replayer:
        replayer.cookies.set("refresh_token", first_refresh)
        replay = await replayer.post("/api/v1/auth/refresh")
        assert replay.status_code == 401

        replayer.cookies.set("refresh_token", second_refresh)
        after = await replayer.post("/api/v1/auth/refresh")
        assert after.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_token_and_reports_onboarding(client: AsyncClient) -> None:
    anonymous = await client.get("/api/v1/auth/me")
    assert anonymous.status_code == 401

    body = await _register(client, "eve@example.org")
    token = body["access_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    payload = me.json()
    assert payload["onboarding"]["step"] == 1
    assert payload["onboarding"]["discoverable"] is False
    assert set(payload["onboarding"]["missing"]) == {"languages", "interests"}


@pytest.mark.asyncio
async def test_expired_token_is_reported(client: AsyncClient) -> None:
    """Un jeton dont `exp` est passé doit être refusé avec le type dédié."""
    import datetime as dt

    import jwt
    from app.core.config import get_settings

    secret = get_settings().jwt_secret.get_secret_value()
    past = dt.datetime.now(dt.UTC) - dt.timedelta(hours=1)
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "role": "user", "exp": int(past.timestamp())},
        secret,
        algorithm="HS256",
    )

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401
    assert response.json()["type"] == "auth.token_expired"


@pytest.mark.asyncio
async def test_forgot_password_is_always_accepted(client: AsyncClient) -> None:
    await _register(client, "grace@example.org")

    known = await client.post("/api/v1/auth/forgot-password", json={"email": "grace@example.org"})
    unknown = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.org"})

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()


@pytest.mark.asyncio
async def test_oauth_unknown_state_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/oauth/google/callback?code=x&state=faux")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_oauth_creates_then_links_account(client: AsyncClient, monkeypatch, clean_engine) -> None:
    state = __import__("app.api.v1.auth.router", fromlist=["_signed_state"])._signed_state("github", "verifier")
    fake = Identity(provider="github", subject="42", email="oscar@example.org", email_verified=True)

    async def fake_exchange(*args, **kwargs) -> Identity:
        return fake

    monkeypatch.setattr(oauth_service, "exchange_code", fake_exchange)
    monkeypatch.setattr("app.core.config.Settings.github_client_id", "client", raising=False)

    from app.core import config as config_module

    monkeypatch.setenv("GITHUB_CLIENT_ID", "client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "secret-valeur-de-test")
    config_module.get_settings.cache_clear()

    first = await client.get(
        f"/api/v1/auth/oauth/github/callback?code=abc&state={state}", follow_redirects=False
    )
    assert first.status_code == 302, first.text
    assert client.cookies.get("refresh_token")

    with clean_engine.connect() as connection:
        created = connection.execute(
            text("SELECT email, oauth_provider, oauth_subject FROM users")
        ).one()
    assert created.oauth_provider == "github"
    assert created.oauth_subject == "42"
    config_module.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_register_is_rate_limited_with_real_rule() -> None:
    """REQ-DOC : la règle réelle 5/min sur /auth/register produit un 429 à la 6e."""
    transport = ASGITransport(app=create_app())  # limites par défaut
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        codes = []
        for index in range(6):
            response = await async_client.post(
                "/api/v1/auth/register",
                json={"email": f"burst{index}@example.org", "password": _PW},
            )
            codes.append(response.status_code)

    assert codes[:5] == [201] * 5, codes
    assert codes[5] == 429
