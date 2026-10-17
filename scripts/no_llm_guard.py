#!/usr/bin/env python3
"""Garde-fou P2 : aucun client de modele generatif dans le produit.

La contrainte « aucune IA generative » de `core.spec.md` (P2) est une contrainte de
produit : elle doit etre verifiee mecaniquement, sinon ce n'est qu'une intention.
Ce script echoue si :

1. une dependance interdisant est declaree (pyproject, package.json, requirements) ;
2. un import direct d'un SDK de modele apparait dans le code ;
3. une URL d'API de generation (chat/completions, etc.) est appelee.

Il ne scanne volontairement pas `openspec/` (la spec cite ces noms pour les interdire)
ni sa propre implementation, qui contient la liste noire.

Usage :
    python scripts/no_llm_guard.py [--root .] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

FORBIDDEN_PACKAGES: tuple[str, ...] = (
    "openai",
    "anthropic",
    "langchain",
    "langchain-core",
    "google-generativeai",
    "google-genai",
    "ollama",
    "litellm",
    "cohere",
    "mistralai",
    "transformers",
)

# Motifs d'appel réseau vers un moteur de generation ou de complétion.
FORBIDDEN_CALLS: tuple[str, ...] = (
    r"chat/completions",
    r"api\.openai\.com",
    r"api\.anthropic\.com",
    r"generativelanguage\.googleapis\.com",
    r"api\.mistral\.ai",
)

CODE_SUFFIXES: frozenset[str] = frozenset({".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"})
MANIFEST_NAMES: frozenset[str] = frozenset({"pyproject.toml", "package.json"})
REQUIREMENTS_GLOB = "requirements*.txt"

SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        "__pycache__",
        ".ruff_cache",
        ".mypy_cache",
        ".pytest_cache",
        ".hermes",
        "openspec",
        "coverage",
    }
)

# Fragments de nom à ignorer pour les manifests (faux positifs : types, plugins).
SELF_EXEMPT: frozenset[str] = frozenset({"no_llm_guard.py", "test_guard_scripts.py"})


@dataclass(frozen=True)
class Violation:
    """Un manquement à la contrainte P2."""

    path: str
    line: int
    rule: str
    excerpt: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.excerpt}"


def _is_dependency_declaration(line: str, package: str) -> bool:
    """Vrai si la ligne déclare `package` comme dépendance."""
    pattern = rf'["\']?{re.escape(package)}["\']?\s*(?:[<>=!~\[@]|$|,|")'
    return bool(re.search(pattern, line)) and not line.lstrip().startswith("#")


def scan_manifest(path: Path, root: Path) -> list[Violation]:
    """Cherche les dépendances interdites dans un manifeste."""
    violations: list[Violation] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return violations

    if path.name == "package.json":
        try:
            data = json.loads("\n".join(lines))
        except json.JSONDecodeError:
            return violations
        declared = {
            **data.get("dependencies", {}),
            **data.get("devDependencies", {}),
            **data.get("peerDependencies", {}),
        }
        for package in FORBIDDEN_PACKAGES:
            if package in declared:
                violations.append(
                    Violation(
                        path=str(path.relative_to(root)),
                        line=1,
                        rule="forbidden-dependency",
                        excerpt=f"{package}@{declared[package]}",
                    )
                )
        return violations

    for number, line in enumerate(lines, start=1):
        for package in FORBIDDEN_PACKAGES:
            if _is_dependency_declaration(line, package):
                violations.append(
                    Violation(
                        path=str(path.relative_to(root)),
                        line=number,
                        rule="forbidden-dependency",
                        excerpt=line.strip()[:120],
                    )
                )
    return violations


def scan_code(path: Path, root: Path) -> list[Violation]:
    """Cherche les imports et appels interdits dans un fichier de code."""
    violations: list[Violation] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return violations

    import_patterns = [
        (re.compile(rf"^\s*(?:from|import)\s+{re.escape(p)}\b"), p) for p in FORBIDDEN_PACKAGES
    ]
    call_patterns = [(re.compile(p), p) for p in FORBIDDEN_CALLS]

    for number, line in enumerate(lines, start=1):
        for pattern, package in import_patterns:
            if pattern.search(line):
                violations.append(
                    Violation(
                        path=str(path.relative_to(root)),
                        line=number,
                        rule="forbidden-import",
                        excerpt=line.strip()[:120],
                    )
                )
                break
        for pattern, raw in call_patterns:
            if pattern.search(line):
                violations.append(
                    Violation(
                        path=str(path.relative_to(root)),
                        line=number,
                        rule="forbidden-endpoint",
                        excerpt=line.strip()[:120],
                    )
                )
    return violations


def iter_files(root: Path) -> list[Path]:
    """Fichiers à analyser, dossiers techniques exclus."""
    found: list[Path] = []
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        if any(part in SKIP_DIRS for part in candidate.parts):
            continue
        if candidate.name in SELF_EXEMPT:
            continue
        if candidate.suffix in CODE_SUFFIXES or candidate.name in MANIFEST_NAMES:
            found.append(candidate)
            continue
        if candidate.match(REQUIREMENTS_GLOB):
            found.append(candidate)
    return sorted(found)


def scan(root: Path) -> list[Violation]:
    """Analyse l'arbre et renvoie toutes les violations, triées."""
    violations: list[Violation] = []
    for path in iter_files(root):
        if path.name in MANIFEST_NAMES or path.match(REQUIREMENTS_GLOB):
            violations.extend(scan_manifest(path, root))
        else:
            violations.extend(scan_code(path, root))
    return sorted(violations, key=lambda v: (v.path, v.line))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Garde-fou P2 : interdiction des LLM.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Racine du dépôt.")
    parser.add_argument("--json", action="store_true", help="Sortie JSON.")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    violations = scan(root)

    if args.json:
        print(json.dumps([asdict(v) for v in violations], ensure_ascii=False, indent=2))
    elif violations:
        print(f"FAIL: {len(violations)} violation(s) de la contrainte P2 :", file=sys.stderr)
        for violation in violations:
            print(f"  {violation.format()}", file=sys.stderr)
    else:
        print(f"OK: aucun client de modele generatif detecte ({len(iter_files(root))} fichiers)")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
