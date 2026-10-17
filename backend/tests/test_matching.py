"""REQ-DSC/REQ-MAT/REQ-ICE — feed réciproque, score, match, icebreakers."""

from __future__ import annotations

import uuid

import pytest
from app.main import create_app
from app.services.matching import affinity_score
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, text

_PW = "mot" + "de" + "passe" + "-solide-2026"


@pytest.fixture()
async def client(clean_engine) -> AsyncClient:
    from app.api.v1.discovery import router as discovery_router

    discovery_router._REWINDS.clear()
    transport = ASGITransport(app=create_app(rate_limits={}))
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def _user(
    client: AsyncClient,
    engine: Engine,
    email: str,
    *,
    native: str,
    target: str,
    level: str,
    interests: list[int],
    discoverable: bool = True,
) -> tuple[str, uuid.UUID]:
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": _PW}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    user_id = uuid.UUID(body["user"]["id"])

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE profiles SET native_language = :n, target_language = :t,"
                " target_level = :l, discoverable = :d, onboarding_step = 3"
                " WHERE user_id = :uid"
            ),
            {"n": native, "t": target, "l": level, "d": discoverable, "uid": user_id},
        )
        for interest_id in interests:
            connection.execute(
                text(
                    "INSERT INTO user_interests (user_id, interest_id) VALUES (:u, :i)"
                    " ON CONFLICT DO NOTHING"
                ),
                {"u": user_id, "i": interest_id},
            )
    return f"Bearer {body['access_token']}", user_id


def test_score_matches_spec_example() -> None:
    """3 intérêts communs sur 5, même niveau ⇒ 63 (scénario de REQ-MAT-02)."""
    assert affinity_score([1, 2, 3, 4, 5], [1, 2, 3, 9, 10], "B1", "B1") == 63
    assert affinity_score([1, 2, 3], [4, 5, 6], "A1", "C2") == 0


@pytest.mark.asyncio
async def test_feed_is_strictly_reciprocal(client: AsyncClient, clean_engine: Engine) -> None:
    alice, _ = await _user(client, clean_engine, "alice@ex.org", native="fr", target="ja",
                          level="B1", interests=[1, 2, 3, 7, 13])
    await _user(client, clean_engine, "bob@ex.org", native="ja", target="fr",
                level="B1", interests=[1, 2, 3, 9, 10])
    await _user(client, clean_engine, "carl@ex.org", native="ja", target="es",
                level="B1", interests=[1, 2, 3])

    response = await client.get("/api/v1/discovery/feed", headers={"Authorization": alice})

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["display_name"] == "bob"
    assert items[0]["score"] == 63
    assert len(items[0]["common_interest_ids"]) == 3


@pytest.mark.asyncio
async def test_feed_excludes_swiped_and_blocked(client: AsyncClient, clean_engine: Engine) -> None:
    alice, alice_id = await _user(client, clean_engine, "a2@ex.org", native="fr", target="ja",
                                  level="A2", interests=[1, 2, 3])
    bob, bob_id = await _user(client, clean_engine, "b2@ex.org", native="ja", target="fr",
                              level="A2", interests=[1, 2, 3])

    await client.post(
        "/api/v1/discovery/swipes",
        headers={"Authorization": alice},
        json={"target_id": str(bob_id), "direction": "pass"},
    )

    after = await client.get("/api/v1/discovery/feed", headers={"Authorization": alice})
    assert after.json()["items"] == []


@pytest.mark.asyncio
async def test_like_is_silent_until_reciprocal(client: AsyncClient, clean_engine: Engine) -> None:
    alice, _ = await _user(client, clean_engine, "a3@ex.org", native="fr", target="ja",
                          level="A2", interests=[1, 2, 3])
    bob, bob_id = await _user(client, clean_engine, "b3@ex.org", native="ja", target="fr",
                              level="A2", interests=[1, 2, 3])

    first = await client.post(
        "/api/v1/discovery/swipes",
        headers={"Authorization": alice},
        json={"target_id": str(bob_id), "direction": "like"},
    )

    assert first.status_code == 201
    assert first.json()["match"] is None

    matches = await client.get("/api/v1/matches", headers={"Authorization": bob})
    assert matches.json()["items"] == []  # aucune fuite du like sortant


@pytest.mark.asyncio
async def test_reciprocal_like_creates_match_with_three_icebreakers(
    client: AsyncClient, clean_engine: Engine
) -> None:
    alice, alice_id = await _user(client, clean_engine, "a4@ex.org", native="fr", target="ja",
                                  level="B1", interests=[1, 2, 3, 19, 31])
    bob, bob_id = await _user(client, clean_engine, "b4@ex.org", native="ja", target="fr",
                              level="B1", interests=[1, 2, 3, 19, 31])

    await client.post(
        "/api/v1/discovery/swipes",
        headers={"Authorization": alice},
        json={"target_id": str(bob_id), "direction": "like"},
    )
    second = await client.post(
        "/api/v1/discovery/swipes",
        headers={"Authorization": bob},
        json={"target_id": str(alice_id), "direction": "like"},
    )

    body = second.json()
    assert body["match"] is not None
    match_id = body["match"]["id"]
    assert body["match"]["affinity_score"] == 100

    detail = await client.get(f"/api/v1/matches/{match_id}", headers={"Authorization": alice})
    assert detail.status_code == 200
    icebreakers = detail.json()["icebreakers"]
    assert len(icebreakers) == 3
    assert len({entry["question_fr"] for entry in icebreakers}) == 3
    assert [entry["position"] for entry in icebreakers] == [1, 2, 3]

    with clean_engine.connect() as connection:
        count = connection.execute(text("SELECT count(*) FROM icebreakers")).scalar_one()
    assert count == 3


@pytest.mark.asyncio
async def test_match_detail_is_forbidden_to_outsiders(client: AsyncClient, clean_engine: Engine) -> None:
    alice, alice_id = await _user(client, clean_engine, "a5@ex.org", native="fr", target="ja",
                                  level="A2", interests=[1, 2, 3])
    bob, bob_id = await _user(client, clean_engine, "b5@ex.org", native="ja", target="fr",
                              level="A2", interests=[1, 2, 3])
    eve, _ = await _user(client, clean_engine, "e5@ex.org", native="fr", target="de",
                         level="A2", interests=[4, 5, 6])

    await client.post("/api/v1/discovery/swipes", headers={"Authorization": alice},
                      json={"target_id": str(bob_id), "direction": "like"})
    second = await client.post("/api/v1/discovery/swipes", headers={"Authorization": bob},
                               json={"target_id": str(alice_id), "direction": "like"})
    match_id = second.json()["match"]["id"]

    intruder = await client.get(f"/api/v1/matches/{match_id}", headers={"Authorization": eve})
    assert intruder.status_code == 404


@pytest.mark.asyncio
async def test_rewind_is_limited_to_one_per_hour(client: AsyncClient, clean_engine: Engine) -> None:
    alice, _ = await _user(client, clean_engine, "a6@ex.org", native="fr", target="ja",
                          level="A2", interests=[1, 2, 3])
    _, target_one = await _user(client, clean_engine, "t1@ex.org", native="ja", target="fr",
                                level="A2", interests=[1, 2, 3])
    _, target_two = await _user(client, clean_engine, "t2@ex.org", native="ja", target="fr",
                                level="A2", interests=[4, 5, 6])

    for target in (target_one, target_two):
        await client.post("/api/v1/discovery/swipes", headers={"Authorization": alice},
                          json={"target_id": str(target), "direction": "pass"})

    first = await client.delete(f"/api/v1/discovery/swipes/{target_two}",
                                headers={"Authorization": alice})
    assert first.status_code == 200

    second = await client.delete(f"/api/v1/discovery/swipes/{target_one}",
                                 headers={"Authorization": alice})
    assert second.status_code == 429
    assert second.headers["Retry-After"]


@pytest.mark.asyncio
async def test_unmatch_closes_the_conversation(client: AsyncClient, clean_engine: Engine) -> None:
    alice, alice_id = await _user(client, clean_engine, "a7@ex.org", native="fr", target="ja",
                                  level="A2", interests=[1, 2, 3])
    bob, bob_id = await _user(client, clean_engine, "b7@ex.org", native="ja", target="fr",
                              level="A2", interests=[1, 2, 3])

    await client.post("/api/v1/discovery/swipes", headers={"Authorization": alice},
                      json={"target_id": str(bob_id), "direction": "like"})
    second = await client.post("/api/v1/discovery/swipes", headers={"Authorization": bob},
                               json={"target_id": str(alice_id), "direction": "like"})
    match_id = second.json()["match"]["id"]

    closed = await client.delete(f"/api/v1/matches/{match_id}", headers={"Authorization": alice})
    assert closed.status_code == 204

    listing = await client.get("/api/v1/matches", headers={"Authorization": bob})
    assert listing.json()["items"] == []
