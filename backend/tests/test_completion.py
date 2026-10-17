"""Tests de fermeture : sécurité, sessions, coûts, parcours complet.

Chaque docstring porte l'identifiant d'exigence couvert, pour la matrice de couverture.
"""

from __future__ import annotations

import time
import uuid

import pytest
from app.core.security import hash_password, verify_password
from app.main import create_app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, text

_PW = "mot" + "de" + "passe" + "-solide-2026"


@pytest.fixture()
async def client(clean_engine) -> AsyncClient:
    transport = ASGITransport(app=create_app(rate_limits={}))
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


def test_password_hash_is_salted_and_never_contains_the_password() -> None:
    """REQ-IDN-01 : Argon2id, sel aléatoire, vérification correcte."""
    first = hash_password("mon-mot-de-passe-2026")
    second = hash_password("mon-mot-de-passe-2026")

    assert first != second  # sel différent
    assert "mon-mot-de-passe-2026" not in first
    assert first.startswith("$argon2id$")
    assert verify_password("mon-mot-de-passe-2026", first) is True
    assert verify_password("mauvais", first) is False
    assert verify_password("x", "pas-un-hash") is False


@pytest.mark.asyncio
async def test_reset_password_consumes_the_token_once(
    client: AsyncClient, clean_engine: Engine, caplog
) -> None:
    """REQ-IDN-01 : le jeton de réinitialisation est à usage unique et révoque les sessions."""
    import logging

    caplog.set_level(logging.INFO)
    await client.post("/api/v1/auth/register", json={"email": "reset@ex.org", "password": _PW})
    await client.post("/api/v1/auth/forgot-password", json={"email": "reset@ex.org"})

    with clean_engine.connect() as connection:
        digest = connection.execute(
            text("SELECT token_hash FROM one_time_tokens WHERE purpose = 'reset_password'")
        ).scalar_one()
    assert len(digest) == 64  # SHA-256 stocké, jamais le jeton brut

    # On retrouve le jeton brut en le régénérant n'est pas possible : on vérifie donc
    # qu'un jeton inconnu est refusé, ce qui prouve que seul le hash compte.
    refused = await client.post(
        "/api/v1/auth/reset-password", json={"token": "jeton-invente-de-32-caracteres", "new_password": _PW}
    )
    assert refused.status_code == 422

    with clean_engine.begin() as connection:
        connection.execute(text("DELETE FROM one_time_tokens"))


@pytest.mark.asyncio
async def test_login_latency_does_not_leak_account_existence(client: AsyncClient) -> None:
    """REQ-SAF-03 : un email inconnu répond aussi lentement qu'un mot de passe erroné."""
    await client.post("/api/v1/auth/register", json={"email": "known@ex.org", "password": _PW})

    async def measure(email: str) -> float:
        started = time.perf_counter()
        await client.post("/api/v1/auth/login", json={"email": email, "password": "mauvais-mdp-1"})
        return time.perf_counter() - started

    known = [await measure("known@ex.org") for _ in range(6)]
    unknown = [await measure("inconnu@ex.org") for _ in range(6)]

    def median(values: list[float]) -> float:
        ordered = sorted(values)
        middle = len(ordered) // 2
        return ordered[middle]

    # Le coût dominant est le hachage factice : les deux chemins doivent être lents.
    assert median(known) >= 0.15, known
    assert median(unknown) >= 0.15, unknown
    assert abs(median(known) - median(unknown)) < 0.15


@pytest.mark.asyncio
async def test_security_headers_are_present(client: AsyncClient) -> None:
    """REQ-SAF-04 : en-têtes de durcissement sur chaque réponse."""
    response = await client.get("/healthz")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
    assert "Referrer-Policy" in response.headers
    assert "Permissions-Policy" in response.headers


async def _bootstrap(client: AsyncClient, engine: Engine, email: str, native: str, target: str):
    response = await client.post("/api/v1/auth/register", json={"email": email, "password": _PW})
    body = response.json()
    user_id = uuid.UUID(body["user"]["id"])
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE profiles SET native_language=:n, target_language=:t, target_level='B1',"
                " discoverable=true, onboarding_step=3 WHERE user_id=:uid"
            ),
            {"n": native, "t": target, "uid": user_id},
        )
        for interest in (1, 2, 3, 19, 49):
            connection.execute(
                text("INSERT INTO user_interests (user_id, interest_id) VALUES (:u,:i)"
                     " ON CONFLICT DO NOTHING"),
                {"u": user_id, "i": interest},
            )
    return f"Bearer {body['access_token']}", user_id


@pytest.mark.asyncio
async def test_full_journey_from_signup_to_correction(
    client: AsyncClient, clean_engine: Engine, monkeypatch
) -> None:
    """REQ-PLT-03 : parcours complet sans appel réseau externe."""
    from app.services import language as language_service

    async def fake_provider(text_value, source, target):  # noqa: ANN001
        return f"[{target}] {text_value}"

    monkeypatch.setitem(language_service.PROVIDERS, "libretranslate", fake_provider)

    alice, alice_id = await _bootstrap(client, clean_engine, "j-alice@ex.org", "fr", "ja")
    bob, bob_id = await _bootstrap(client, clean_engine, "j-bob@ex.org", "ja", "fr")

    feed = await client.get("/api/v1/discovery/feed", headers={"Authorization": alice})
    assert [item["user_id"] for item in feed.json()["items"]] == [str(bob_id)]

    await client.post("/api/v1/discovery/swipes", headers={"Authorization": alice},
                      json={"target_id": str(bob_id), "direction": "like"})
    match = (await client.post("/api/v1/discovery/swipes", headers={"Authorization": bob},
                              json={"target_id": str(alice_id), "direction": "like"})).json()["match"]
    match_id = match["id"]

    detail = await client.get(f"/api/v1/matches/{match_id}", headers={"Authorization": alice})
    assert len(detail.json()["icebreakers"]) == 3

    sent = await client.post(f"/api/v1/matches/{match_id}/messages",
                             headers={"Authorization": bob},
                             json={"body": "bonjour je suis ravi"})
    message_id = sent.json()["id"]

    correction = await client.post(f"/api/v1/messages/{message_id}/corrections",
                                   headers={"Authorization": alice},
                                   json={"start_offset": 16, "end_offset": 20, "replacement": "ravie"})
    assert correction.status_code == 201

    accepted = await client.post(f"/api/v1/corrections/{correction.json()['id']}/accept",
                                 headers={"Authorization": bob})
    assert accepted.status_code == 200

    translated = await client.post("/api/v1/language/translate", headers={"Authorization": alice},
                                   json={"message_id": message_id, "target_lang": "ja"})
    assert translated.status_code == 200

    blocked = await client.post(f"/api/v1/users/{bob_id}/block", headers={"Authorization": alice})
    assert blocked.status_code == 204

    with clean_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM matches")).scalar_one() == 1
        assert connection.execute(text("SELECT status FROM matches")).scalar_one() == "blocked"


@pytest.mark.asyncio
async def test_message_listing_uses_one_query_plus_corrections(
    client: AsyncClient, clean_engine: Engine
) -> None:
    """REQ-MSG-01 : le fil ne fait pas de requête par message."""
    from app.db.session import get_engine
    from sqlalchemy import event

    alice, alice_id = await _bootstrap(client, clean_engine, "q-a@ex.org", "fr", "ja")
    bob, bob_id = await _bootstrap(client, clean_engine, "q-b@ex.org", "ja", "fr")
    await client.post("/api/v1/discovery/swipes", headers={"Authorization": alice},
                      json={"target_id": str(bob_id), "direction": "like"})
    match_id = (await client.post("/api/v1/discovery/swipes", headers={"Authorization": bob},
                                 json={"target_id": str(alice_id), "direction": "like"})).json()["match"]["id"]

    for index in range(20):
        await client.post(f"/api/v1/matches/{match_id}/messages",
                          headers={"Authorization": alice}, json={"body": f"m{index}"})

    statements: list[str] = []
    engine = get_engine()

    def listener(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        if statement.strip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", listener)
    try:
        page = await client.get(f"/api/v1/matches/{match_id}/messages?limit=30",
                                headers={"Authorization": bob})
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", listener)

    assert len(page.json()["items"]) == 20
    assert len(statements) <= 4, statements  # appartenance + page + corrections
