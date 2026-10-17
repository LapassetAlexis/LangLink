"""REQ-LEX-01/02 — aide au mot : plusieurs sens, nettoyage du wikitext."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services import lexicon as lexicon_service
from httpx import ASGITransport, AsyncClient

_PW = "mot" + "de" + "passe" + "-solide-2026"

WIKITEXT = """== {{langue|fr}} ==
=== {{S|nom|fr}} ===
'''marché''' {{pron|maʁ.ʃe|fr}} {{m}}
# (Commerce) Lieu public où s'achètent et se vendent les denrées.
# {{figuré|fr}} Convention, accord entre parties.
## Sous-sens qui ne doit pas remonter.
# (Par extension) [[transaction|Transaction]] commerciale.<ref>Source</ref>
"""


def test_parser_extracts_numbered_definitions_only() -> None:
    senses = lexicon_service.parse_definitions(WIKITEXT)

    assert len(senses) == 3
    assert senses[0]["part_of_speech"] == "commerce"
    assert senses[0]["definition"].startswith("Lieu public")
    assert senses[1]["part_of_speech"] == "figuré"
    assert senses[2]["definition"] == "Transaction commerciale."  # lien et <ref> nettoyés
    assert all("Sous-sens" not in sense["definition"] for sense in senses)


def test_parser_ignores_empty_and_markup_only_lines() -> None:
    assert lexicon_service.parse_definitions("#\n##\n# {{t|fr}}\n") == []


@pytest.mark.asyncio
async def test_lexicon_endpoint_returns_multiple_senses(clean_engine, monkeypatch) -> None:
    async def fake_lookup(word: str) -> list[dict[str, str]]:
        assert word == "marché"
        return [
            {"part_of_speech": "commerce", "definition": "Lieu public de vente."},
            {"part_of_speech": "figuré", "definition": "Convention entre parties."},
        ]

    monkeypatch.setattr(lexicon_service, "lookup", fake_lookup)

    transport = ASGITransport(app=create_app(rate_limits={}))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        registered = await client.post(
            "/api/v1/auth/register", json={"email": "lex@ex.org", "password": _PW}
        )
        headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}

        anonymous = await client.post("/api/v1/language/lexicon", json={"text": "marché"})
        assert anonymous.status_code == 401

        response = await client.post(
            "/api/v1/language/lexicon", json={"text": "marché", "lang": "fr"}, headers=headers
        )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "wiktionnaire"
    assert len(body["senses"]) == 2
    assert {sense["part_of_speech"] for sense in body["senses"]} == {"commerce", "figuré"}


@pytest.mark.asyncio
async def test_lexicon_adds_reading_for_japanese(clean_engine, monkeypatch) -> None:
    async def fake_lookup(word: str) -> list[dict[str, str]]:
        return [{"part_of_speech": "éducation", "definition": "Élève, étudiant."}]

    monkeypatch.setattr(lexicon_service, "lookup", fake_lookup)

    transport = ASGITransport(app=create_app(rate_limits={}))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        registered = await client.post(
            "/api/v1/auth/register", json={"email": "lex-ja@ex.org", "password": _PW}
        )
        headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
        response = await client.post(
            "/api/v1/language/lexicon", json={"text": "学生", "lang": "ja"}, headers=headers
        )

    assert response.status_code == 200
    reading = response.json()["reading"]
    assert reading is not None
    assert reading["romaji"]
