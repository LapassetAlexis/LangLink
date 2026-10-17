"""Tâche 1.5 — le garde-fou P2 détecte réellement une dépendance ou un import interdit."""

from __future__ import annotations

import json
from pathlib import Path

from tests.conftest import load_script

guard = load_script("no_llm_guard")

# Construits dynamiquement pour que ce fichier de test ne se déclenche pas lui-même
# lorsque le garde-fou scanne le dépôt.
FORBIDDEN_MODULE = "open" + "ai"
FORBIDDEN_ENDPOINT = "chat/" + "completions"


def test_clean_tree_passes(tmp_path: Path) -> None:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "ok.py").write_text("import json\n", encoding="utf-8")

    assert guard.scan(tmp_path) == []
    assert guard.main(["--root", str(tmp_path)]) == 0


def test_forbidden_import_is_detected(tmp_path: Path) -> None:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "bad.py").write_text(
        f"from {FORBIDDEN_MODULE} import OpenAI\n", encoding="utf-8"
    )

    violations = guard.scan(tmp_path)
    assert len(violations) == 1
    assert violations[0].rule == "forbidden-import"
    assert guard.main(["--root", str(tmp_path)]) == 1


def test_forbidden_endpoint_is_detected(tmp_path: Path) -> None:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "client.ts").write_text(
        f'const url = "https://api.example.com/v1/{FORBIDDEN_ENDPOINT}";\n', encoding="utf-8"
    )

    violations = guard.scan(tmp_path)
    assert [v.rule for v in violations] == ["forbidden-endpoint"]


def test_forbidden_dependency_is_detected(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = [\n    "fastapi>=0.115",\n'
        f'    "{FORBIDDEN_MODULE}>=1.0",\n]\n',
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {FORBIDDEN_MODULE: "^4.0.0"}}), encoding="utf-8"
    )

    violations = guard.scan(tmp_path)
    rules = [v.rule for v in violations]
    assert rules.count("forbidden-dependency") == 2


def test_openspec_directory_is_ignored(tmp_path: Path) -> None:
    """La spec cite les noms interdits pour les proscrire : elle ne doit pas être scannée."""
    (tmp_path / "openspec").mkdir()
    (tmp_path / "openspec" / "spec.md").write_text(
        f"Interdiction de {FORBIDDEN_MODULE} et de transformers.\n", encoding="utf-8"
    )

    assert guard.scan(tmp_path) == []
