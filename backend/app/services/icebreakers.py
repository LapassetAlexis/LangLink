"""Sélection déterministe des icebreakers (catalogue statique, aucune génération)."""

from __future__ import annotations

import hashlib
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "icebreakers.yaml"


@lru_cache(maxsize=1)
def catalog() -> dict[str, list[dict[str, str]]]:
    """Catalogue catégorie -> questions. Chargé une fois, immuable."""
    data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    return {str(category): entries for category, entries in data.items()}


def _rank(match_id: uuid.UUID, slug: str, question: str) -> str:
    return hashlib.sha256(f"{match_id}{slug}{question}".encode()).hexdigest()


def select(
    match_id: uuid.UUID, common: list[tuple[str, str]]
) -> list[dict[str, Any]]:
    """Choisit 3 questions pour un match.

    `common` = liste de (slug d'intérêt, catégorie). Priorité à une question par intérêt
    distinct ; si l'intersection est trop petite, on complète sans jamais répéter une
    question. Le résultat ne dépend que de `match_id` et des intérêts : deux appels
    donnent la même sélection.
    """
    if not common:
        common = [("decouverte", "Voyage")]

    pool: list[tuple[str, str, dict[str, str]]] = []
    for slug, category in common:
        for entry in catalog().get(category, []):
            pool.append((slug, category, entry))

    pool.sort(key=lambda item: _rank(match_id, item[0], item[2]["fr"]))

    chosen: list[tuple[str, str, dict[str, str]]] = []
    seen_slugs: set[str] = set()
    seen_questions: set[str] = set()

    for slug, category, entry in pool:  # passe 1 : un intérêt distinct par question
        if slug in seen_slugs or entry["fr"] in seen_questions:
            continue
        chosen.append((slug, category, entry))
        seen_slugs.add(slug)
        seen_questions.add(entry["fr"])
        if len(chosen) == 3:
            break

    for slug, category, entry in pool:  # passe 2 : compléter sans doublon de question
        if len(chosen) == 3:
            break
        if entry["fr"] in seen_questions:
            continue
        chosen.append((slug, category, entry))
        seen_questions.add(entry["fr"])

    return [
        {
            "position": index + 1,
            "interest_slug": slug,
            "question_fr": entry["fr"],
            "question_en": entry["en"],
        }
        for index, (slug, _category, entry) in enumerate(chosen)
    ]
