"""Aide lexicale : plusieurs sens par mot, via le Wiktionnaire francophone.

L'API REST `/api/rest_v1/page/definition` est hors service (501 sur tous les mots). On passe
par l'API MediaWiki `action=parse` et on extrait les définitions du **wikitext** : ce sont
les lignes commençant par `#` (et non `##`, qui sont des sous-sens) et la catégorie
grammaticale est en tête, entre parenthèses.

Aucune génération de texte : on restitue un dictionnaire existant.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

WIKTIONARY_API = "https://fr.wiktionary.org/w/api.php"
USER_AGENT = "LangLink/0.1 (projet personnel; https://github.com/LapassetAlexis/LangLink)"
MAX_SENSES = 6
_TIMEOUT = 8.0

# Cache mémoire borné : un mot consulté deux fois ne repart pas sur le réseau.
_CACHE: dict[str, list[dict[str, str]]] = {}
_CACHE_LIMIT = 500

_LINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
_TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
_REF = re.compile(r"<ref[^>]*>.*?</ref>", re.S)
_TAG = re.compile(r"<[^>]+>")
_QUOTES = re.compile(r"'{2,}")
_POS = re.compile(r"^\(([^)]{2,40})\)\s*(.+)$")
# En wikitext la catégorie est un template en tête de ligne : {{figuré|fr}}.
_LEAD_TEMPLATE = re.compile(r"^\{\{\s*([^}|]+)")


def clean_wikitext(text: str) -> str:
    """Retire le balisage MediaWiki d'une définition."""
    text = _REF.sub("", text)
    text = _TEMPLATE.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _TAG.sub("", text)
    text = _QUOTES.sub("", text)
    text = text.replace("&nbsp;", " ").replace("&#160;", " ")
    return re.sub(r"\s{2,}", " ", text).strip()


def parse_definitions(wikitext: str, limit: int = MAX_SENSES) -> list[dict[str, str]]:
    """Extrait `{part_of_speech, definition}` des lignes `#` du wikitext."""
    senses: list[dict[str, str]] = []
    for raw in wikitext.splitlines():
        line = raw.strip()
        if not line.startswith("#") or line.startswith("##"):
            continue
        raw_definition = line[1:].strip()
        lead = _LEAD_TEMPLATE.match(raw_definition)
        speech = lead.group(1).strip().lower() if lead else "—"

        text = clean_wikitext(raw_definition)
        if not text or len(text) < 3:
            continue

        parenthesised = _POS.match(text)
        if parenthesised:  # certains articles écrivent la catégorie en clair
            speech, definition = parenthesised.group(1).lower(), parenthesised.group(2).strip()
        else:
            definition = text
        if not definition:
            continue
        senses.append({"part_of_speech": speech, "definition": definition})
        if len(senses) >= limit:
            break
    return senses


async def lookup(word: str) -> list[dict[str, str]]:
    """Interroge le Wiktionnaire. Renvoie une liste vide si le mot est inconnu."""
    key = word.strip().lower()
    if not key:
        return []
    if key in _CACHE:
        return _CACHE[key]

    params = {
        "action": "parse",
        "page": word.strip(),
        "prop": "wikitext",
        "format": "json",
        "formatversion": "2",
        "disableeditsection": "1",
        "redirects": "1",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                WIKTIONARY_API,
                params=params,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
        if response.status_code >= 400:
            return []
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    if "error" in payload:
        return []

    senses = parse_definitions(payload.get("parse", {}).get("wikitext", ""))
    if len(_CACHE) >= _CACHE_LIMIT:
        _CACHE.clear()
    _CACHE[key] = senses
    return senses


__all__: list[Any] = ["clean_wikitext", "lookup", "parse_definitions"]
