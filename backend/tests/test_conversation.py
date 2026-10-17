"""REQ-MSG/COR/LNG/SAF — conversation, corrections, outils linguistiques, sécurité."""

from __future__ import annotations

import uuid

import pytest
from app.main import create_app
from app.services import language as language_service
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, text

_PW = "mot" + "de" + "passe" + "-solide-2026"


@pytest.fixture()
async def client(clean_engine) -> AsyncClient:
    transport = ASGITransport(app=create_app(rate_limits={}))
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def _user(client, engine, email, native="fr", target="ja", interests=(1, 2, 3)):
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
        for interest in interests:
            connection.execute(
                text("INSERT INTO user_interests (user_id, interest_id) VALUES (:u,:i)"
                     " ON CONFLICT DO NOTHING"),
                {"u": user_id, "i": interest},
            )
    return f"Bearer {body['access_token']}", user_id


async def _matched(client, engine):
    alice, alice_id = await _user(client, engine, "m-alice@ex.org")
    bob, bob_id = await _user(client, engine, "m-bob@ex.org", native="ja", target="fr")
    await client.post("/api/v1/discovery/swipes", headers={"Authorization": alice},
                      json={"target_id": str(bob_id), "direction": "like"})
    second = await client.post("/api/v1/discovery/swipes", headers={"Authorization": bob},
                               json={"target_id": str(alice_id), "direction": "like"})
    return alice, alice_id, bob, bob_id, second.json()["match"]["id"]


@pytest.mark.asyncio
async def test_send_message_updates_last_message(client, clean_engine: Engine) -> None:
    alice, _, bob, _, match_id = await _matched(client, clean_engine)

    response = await client.post(
        f"/api/v1/matches/{match_id}/messages",
        headers={"Authorization": alice},
        json={"body": "  Bonjour !  "},
    )

    assert response.status_code == 201
    assert response.json()["body"] == "Bonjour !"
    with clean_engine.connect() as connection:
        stored = connection.execute(text("SELECT body, body_lang FROM messages")).one()
        last = connection.execute(text("SELECT last_message_at FROM matches")).scalar_one()
    assert stored.body == "Bonjour !"
    assert last is not None


@pytest.mark.asyncio
async def test_empty_and_oversized_messages_are_rejected(client, clean_engine: Engine) -> None:
    alice, _, _, _, match_id = await _matched(client, clean_engine)

    empty = await client.post(f"/api/v1/matches/{match_id}/messages",
                              headers={"Authorization": alice}, json={"body": "   "})
    too_long = await client.post(f"/api/v1/matches/{match_id}/messages",
                                 headers={"Authorization": alice}, json={"body": "a" * 4001})

    assert empty.status_code == 422
    assert too_long.status_code == 422


@pytest.mark.asyncio
async def test_idempotency_key_prevents_duplicates(client, clean_engine: Engine) -> None:
    alice, _, _, _, match_id = await _matched(client, clean_engine)
    headers = {"Authorization": alice, "Idempotency-Key": "cle-1"}

    first = await client.post(f"/api/v1/matches/{match_id}/messages", headers=headers,
                              json={"body": "Salut"})
    second = await client.post(f"/api/v1/matches/{match_id}/messages", headers=headers,
                               json={"body": "Salut"})

    assert first.status_code == second.status_code == 201
    with clean_engine.connect() as connection:
        count = connection.execute(text("SELECT count(*) FROM messages")).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_keyset_pagination_and_read_status(client, clean_engine: Engine) -> None:
    alice, _, bob, _, match_id = await _matched(client, clean_engine)
    for index in range(35):
        await client.post(f"/api/v1/matches/{match_id}/messages",
                          headers={"Authorization": alice}, json={"body": f"msg {index}"})

    page_one = await client.get(f"/api/v1/matches/{match_id}/messages?limit=30",
                                headers={"Authorization": bob})
    cursor = page_one.json()["next_cursor"]
    page_two = await client.get(f"/api/v1/matches/{match_id}/messages?limit=30&before={cursor}",
                                headers={"Authorization": bob})

    assert len(page_one.json()["items"]) == 30
    assert len(page_two.json()["items"]) == 5
    ids = {item["id"] for item in page_one.json()["items"]} | {
        item["id"] for item in page_two.json()["items"]
    }
    assert len(ids) == 35

    unread = await client.get(f"/api/v1/matches/{match_id}/unread-count",
                              headers={"Authorization": bob})
    assert unread.json()["unread_count"] == 35
    etag = unread.headers["ETag"]

    not_modified = await client.get(
        f"/api/v1/matches/{match_id}/unread-count",
        headers={"Authorization": bob, "If-None-Match": etag},
    )
    assert not_modified.status_code == 304

    last_id = page_one.json()["items"][0]["id"]
    read = await client.post(f"/api/v1/matches/{match_id}/read", headers={"Authorization": bob},
                             json={"last_message_id": last_id})
    assert read.status_code == 200
    after = await client.get(f"/api/v1/matches/{match_id}/unread-count",
                             headers={"Authorization": bob})
    assert after.json()["unread_count"] < 35


@pytest.mark.asyncio
async def test_outsider_cannot_read_the_thread(client, clean_engine: Engine) -> None:
    _, _, _, _, match_id = await _matched(client, clean_engine)
    eve, _ = await _user(client, clean_engine, "eve-thread@ex.org", target="de")

    response = await client.get(f"/api/v1/matches/{match_id}/messages",
                                headers={"Authorization": eve})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_edit_window_and_soft_delete(client, clean_engine: Engine) -> None:
    alice, _, _, _, match_id = await _matched(client, clean_engine)
    created = await client.post(f"/api/v1/matches/{match_id}/messages",
                                headers={"Authorization": alice}, json={"body": "faute"})
    message_id = created.json()["id"]

    edited = await client.patch(f"/api/v1/messages/{message_id}",
                                headers={"Authorization": alice}, json={"body": "corrigé"})
    assert edited.status_code == 200

    with clean_engine.begin() as connection:
        connection.execute(
            text("UPDATE messages SET created_at = now() - interval '20 minutes' WHERE id = :id"),
            {"id": message_id},
        )

    late = await client.patch(f"/api/v1/messages/{message_id}",
                              headers={"Authorization": alice}, json={"body": "trop tard"})
    assert late.status_code == 403

    deleted = await client.delete(f"/api/v1/messages/{message_id}",
                                  headers={"Authorization": alice})
    assert deleted.status_code == 204
    with clean_engine.connect() as connection:
        row = connection.execute(
            text("SELECT body, deleted_at FROM messages WHERE id = :id"), {"id": message_id}
        ).one()
    assert row.body == "[message supprimé]"
    assert row.deleted_at is not None


@pytest.mark.asyncio
async def test_correction_is_localised_and_validated(client, clean_engine: Engine) -> None:
    alice, _, bob, bob_id, match_id = await _matched(client, clean_engine)
    created = await client.post(f"/api/v1/matches/{match_id}/messages",
                                headers={"Authorization": bob},
                                json={"body": "je suis allé au marché"})
    message_id = created.json()["id"]

    own = await client.post(f"/api/v1/messages/{message_id}/corrections",
                            headers={"Authorization": bob},
                            json={"start_offset": 0, "end_offset": 2, "replacement": "x"})
    assert own.status_code == 422
    assert own.json()["errors"][0]["code"] == "own_message"

    out_of_range = await client.post(f"/api/v1/messages/{message_id}/corrections",
                                     headers={"Authorization": alice},
                                     json={"start_offset": 0, "end_offset": 999,
                                           "replacement": "x"})
    assert out_of_range.status_code == 422

    valid = await client.post(f"/api/v1/messages/{message_id}/corrections",
                              headers={"Authorization": alice},
                              json={"start_offset": 8, "end_offset": 12,
                                    "replacement": "allée", "explanation": "accord"})
    assert valid.status_code == 201
    assert valid.json()["original_text"] == "allé"

    overlap = await client.post(f"/api/v1/messages/{message_id}/corrections",
                                headers={"Authorization": alice},
                                json={"start_offset": 9, "end_offset": 11, "replacement": "y"})
    assert overlap.status_code == 409


@pytest.mark.asyncio
async def test_author_accepts_and_original_body_is_untouched(client, clean_engine: Engine) -> None:
    alice, _, bob, _, match_id = await _matched(client, clean_engine)
    created = await client.post(f"/api/v1/matches/{match_id}/messages",
                                headers={"Authorization": bob},
                                json={"body": "je suis allé au marché"})
    message_id = created.json()["id"]
    correction = await client.post(f"/api/v1/messages/{message_id}/corrections",
                                   headers={"Authorization": alice},
                                   json={"start_offset": 8, "end_offset": 12,
                                         "replacement": "allée"})
    correction_id = correction.json()["id"]

    forbidden = await client.post(f"/api/v1/corrections/{correction_id}/accept",
                                  headers={"Authorization": alice})
    assert forbidden.status_code == 403  # le correcteur ne décide pas

    accepted = await client.post(f"/api/v1/corrections/{correction_id}/accept",
                                 headers={"Authorization": bob})
    assert accepted.status_code == 200

    page = await client.get(f"/api/v1/matches/{match_id}/messages",
                            headers={"Authorization": bob})
    rendered = page.json()["items"][0]["body_rendered"]
    assert rendered == "je suis allée au marché"

    with clean_engine.connect() as connection:
        stored = connection.execute(
            text("SELECT body FROM messages WHERE id = :id"), {"id": message_id}
        ).scalar_one()
    assert stored == "je suis allé au marché"  # original immuable


@pytest.mark.asyncio
async def test_translation_is_cached_and_never_automatic(client, clean_engine: Engine, monkeypatch) -> None:
    alice, _, bob, _, match_id = await _matched(client, clean_engine)
    await client.post(f"/api/v1/matches/{match_id}/messages",
                      headers={"Authorization": bob}, json={"body": "Bonjour"})
    calls = {"n": 0}

    async def fake_provider(text, source, target):
        calls["n"] += 1
        return f"[{target}] {text}"

    monkeypatch.setitem(language_service.PROVIDERS, "libretranslate", fake_provider)
    monkeypatch.setitem(language_service.PROVIDERS, "deepl", fake_provider)

    first = await client.post("/api/v1/language/translate", headers={"Authorization": alice},
                              json={"text": "Bonjour", "source_lang": "fr", "target_lang": "ja"})
    second = await client.post("/api/v1/language/translate", headers={"Authorization": alice},
                               json={"text": "Bonjour", "source_lang": "fr", "target_lang": "ja"})

    assert first.status_code == 200
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_reading_aid_returns_offsets_that_match_the_text(client, clean_engine: Engine) -> None:
    alice, _ = await _user(client, clean_engine, "aid@ex.org")
    response = await client.post(
        "/api/v1/language/reading-aid",
        headers={"Authorization": alice},
        json={"text": "私は学生です"},
    )

    assert response.status_code == 200
    tokens = response.json()["tokens"]
    assert 4 <= len(tokens) <= 6
    assert "".join(token["surface"] for token in tokens) == "私は学生です"
    assert all(token["reading"] for token in tokens)
    assert tokens[0]["start"] == 0
    assert tokens[-1]["end"] == len("私は学生です")


@pytest.mark.asyncio
async def test_blocking_closes_thread_and_hides_profile(client, clean_engine: Engine) -> None:
    alice, alice_id, bob, bob_id, match_id = await _matched(client, clean_engine)
    await client.post(f"/api/v1/matches/{match_id}/messages",
                      headers={"Authorization": alice}, json={"body": "coucou"})

    blocked = await client.post(f"/api/v1/users/{bob_id}/block", headers={"Authorization": alice})
    assert blocked.status_code == 204

    refused = await client.post(f"/api/v1/matches/{match_id}/messages",
                                headers={"Authorization": bob}, json={"body": "toujours là ?"})
    assert refused.status_code in (403, 409)

    feed = await client.get("/api/v1/discovery/feed", headers={"Authorization": bob})
    assert all(item["user_id"] != str(alice_id) for item in feed.json()["items"])


@pytest.mark.asyncio
async def test_report_keeps_snapshot_and_admin_routes_are_protected(
    client, clean_engine: Engine
) -> None:
    alice, _, bob, _, match_id = await _matched(client, clean_engine)
    created = await client.post(f"/api/v1/matches/{match_id}/messages",
                                headers={"Authorization": alice}, json={"body": "message signalé"})
    message_id = created.json()["id"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": alice})
    alice_real = me.json()["user"]["id"]

    report = await client.post(
        "/api/v1/reports",
        headers={"Authorization": bob},
        json={"reported_user_id": alice_real, "message_id": message_id, "category": "spam"},
    )
    assert report.status_code == 201, report.text

    with clean_engine.connect() as connection:
        snapshot = connection.execute(text("SELECT content_snapshot FROM reports")).scalar_one()
    assert snapshot == "message signalé"

    forbidden = await client.patch(
        f"/api/v1/admin/reports/{report.json()['id']}",
        headers={"Authorization": bob},
        json={"status": "actioned"},
    )
    assert forbidden.status_code == 403
