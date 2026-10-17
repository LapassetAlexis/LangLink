#!/usr/bin/env python3
"""Exporte le contrat OpenAPI dans `openapi.json` à la racine du dépôt.

Aucune base de données n'est contactée : `create_app()` ne crée pas de connexion (le moteur
est paresseux). Le fichier produit sert de source aux types TypeScript du frontend et de
référence versionnée pour la CI.

Usage : python scripts/export_openapi.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

# Valeurs de substitution : la validation de configuration exige qu'elles existent, mais
# aucune connexion n'est ouverte.
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/langlink")
os.environ.setdefault("JWT_SECRET", "openapi-export-not-a-real-secret-0123456789")

from app.main import create_app  # noqa: E402


def main() -> int:
    spec = create_app().openapi()
    target = ROOT / "openapi.json"
    target.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths = len(spec.get("paths", {}))
    print(f"{target.name} : {paths} chemin(s), {len(spec.get('components', {}).get('schemas', {}))} schéma(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
