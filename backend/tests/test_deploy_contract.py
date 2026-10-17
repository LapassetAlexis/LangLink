"""REQ-LNG-01 — non-régression : le moteur de traduction doit être déclaré dans la stack.

Le 17/10/2026, la traduction a renvoyé 503 en production pendant toute une session : le code
appelait `http://libretranslate:5000` alors que `deploy/stack.yml` ne déclarait aucun service
de traduction. Les tests unitaires mockaient le fournisseur, donc le trou n'apparaissait
qu'en déployant.

Ce test lit le fichier de déploiement et vérifie que le contrat « le service existe, l'API le
connaît » est tenu. Il ne remplace pas un test d'intégration réel, mais il empêche la
régression exacte qui a eu lieu.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

STACK = Path(__file__).resolve().parents[2] / "deploy" / "stack.yml"


@pytest.fixture(scope="module")
def stack() -> dict:
    return yaml.safe_load(STACK.read_text(encoding="utf-8"))


def test_translation_service_is_declared(stack: dict) -> None:
    services = stack["services"]

    assert "libretranslate" in services, "aucun service de traduction dans deploy/stack.yml"
    translation = services["libretranslate"]
    assert translation["image"].startswith("libretranslate/")
    assert translation.get("volumes"), "les modèles doivent persister entre déploiements"


def test_api_knows_the_translation_service(stack: dict) -> None:
    environment = stack["services"]["api"]["environment"]

    assert environment["LIBRETRANSLATE_URL"] == "http://libretranslate:5000"
    # Le nom d'hôte doit correspondre à un service réellement déclaré.
    service_name = environment["LIBRETRANSLATE_URL"].split("//")[1].split(":")[0]
    assert service_name in stack["services"]


def test_only_the_useful_languages_are_loaded(stack: dict) -> None:
    """Charger 50 langues coûte plusieurs Go de RAM pour rien."""
    environment = stack["services"]["libretranslate"]["environment"]
    loaded = [code.strip() for code in environment["LT_LOAD_ONLY"].split(",")]

    assert "fr" in loaded and "ja" in loaded
    assert len(loaded) <= 6
