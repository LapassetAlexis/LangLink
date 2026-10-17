#!/usr/bin/env python3
"""Matrice de couverture spec -> tests.

Extrait chaque exigence (`### Requirement: [REQ-...]`) et ses scénarios des deltas
OpenSpec, puis cherche l'identifiant dans le corpus de tests. Une exigence dont l'ID
n'apparaît nulle part est un scénario orphelin : le script sort en code 1 (sauf
`--report-only`, utilisé tant que l'implémentation est en cours).

Le rapport est écrit dans le dossier du change (`coverage.md`) pour voyager avec l'archive.

Usage :
    python scripts/coverage_matrix.py [--change mvp-v1] [--root .] [--report-only] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REQUIREMENT_RE = re.compile(r"^###\s+Requirement:\s*\[(REQ-[A-Z]+-\d+)\]\s*(.+?)\s*$")
SCENARIO_RE = re.compile(r"^####\s+Scenario:\s*(.+?)\s*$")
REQ_ID_RE = re.compile(r"REQ-[A-Z]+-\d+")

TEST_SUFFIXES: frozenset[str] = frozenset({".py", ".ts", ".tsx", ".js", ".jsx", ".mjs"})
TEST_DIRS: tuple[str, ...] = ("backend/tests", "frontend/src")
SKIP_DIRS: frozenset[str] = frozenset(
    {"node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".git", ".pytest_cache"}
)


@dataclass
class Requirement:
    """Une exigence de spec et ses scénarios."""

    req_id: str
    title: str
    capability: str
    scenarios: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)

    @property
    def covered(self) -> bool:
        return bool(self.refs)


@dataclass
class Report:
    """État de couverture d'un change."""

    change: str
    requirements: list[Requirement]

    @property
    def orphans(self) -> list[Requirement]:
        return [r for r in self.requirements if not r.covered]

    @property
    def scenario_count(self) -> int:
        return sum(len(r.scenarios) for r in self.requirements)


def parse_spec(path: Path) -> list[Requirement]:
    """Extrait les exigences d'un fichier delta OpenSpec."""
    capability = path.parent.name
    requirements: list[Requirement] = []
    current: Requirement | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        match_req = REQUIREMENT_RE.match(line)
        if match_req:
            current = Requirement(
                req_id=match_req.group(1), title=match_req.group(2), capability=capability
            )
            requirements.append(current)
            continue
        match_scen = SCENARIO_RE.match(line)
        if match_scen and current is not None:
            current.scenarios.append(match_scen.group(1))
        elif line.startswith("## ") and current is not None:
            current = None

    return requirements


def iter_test_files(root: Path) -> list[Path]:
    """Fichiers de test candidats."""
    files: list[Path] = []
    for base in TEST_DIRS:
        directory = root / base
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in TEST_SUFFIXES:
                if not any(part in SKIP_DIRS for part in path.parts):
                    files.append(path)
    return sorted(files)


def build_report(root: Path, change_dir: Path) -> Report:
    """Construit la matrice pour un change."""
    requirements: list[Requirement] = []
    for spec_path in sorted((change_dir / "specs").glob("*/spec.md")):
        requirements.extend(parse_spec(spec_path))

    by_id = {req.req_id: req for req in requirements}
    for test_path in iter_test_files(root):
        relative = str(test_path.relative_to(root))
        text = test_path.read_text(encoding="utf-8", errors="replace")
        for req_id in sorted(set(REQ_ID_RE.findall(text))):
            if req_id in by_id:
                by_id[req_id].refs.append(relative)

    return Report(change=change_dir.name, requirements=requirements)


def render_markdown(report: Report) -> str:
    """Rapport lisible, rangé dans le dossier du change."""
    total = len(report.requirements)
    covered = total - len(report.orphans)
    lines = [
        f"# Matrice de couverture — {report.change}",
        "",
        f"- Exigences : **{total}**",
        f"- Couvertes par au moins un test : **{covered}**",
        f"- Scénarios : **{report.scenario_count}**",
        f"- Orphelines : **{len(report.orphans)}**",
        "",
        "| Exigence | Capacité | Scénarios | Tests |",
        "|---|---|---|---|",
    ]
    for req in report.requirements:
        refs = ", ".join(f"`{r}`" for r in req.refs) if req.refs else "— **orpheline**"
        lines.append(f"| `{req.req_id}` — {req.title} | {req.capability} | {len(req.scenarios)} | {refs} |")

    if report.orphans:
        lines += ["", "## Scénarios orphelins", ""]
        for req in report.orphans:
            for scenario in req.scenarios:
                lines.append(f"- `{req.req_id}` — {scenario}")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Matrice de couverture spec -> tests.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--change", help="Nom du change ; sinon tous les changes actifs.")
    parser.add_argument("--report-only", action="store_true", help="Ne jamais sortir en erreur.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    changes_dir = root / "openspec" / "changes"
    if args.change:
        candidates = [changes_dir / args.change]
    else:
        candidates = sorted(
            p for p in changes_dir.iterdir() if p.is_dir() and p.name != "archive"
        )

    reports = [build_report(root, c) for c in candidates if (c / "specs").is_dir()]
    if not reports:
        print("Aucun change avec des deltas de spec.", file=sys.stderr)
        return 0 if args.report_only else 1

    exit_code = 0
    for report in reports:
        (changes_dir / report.change / "coverage.md").write_text(
            render_markdown(report), encoding="utf-8"
        )
        if args.json:
            print(
                json.dumps(
                    {
                        "change": report.change,
                        "requirements": len(report.requirements),
                        "scenarios": report.scenario_count,
                        "orphans": [r.req_id for r in report.orphans],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(
                f"{report.change}: {len(report.requirements)} exigences, "
                f"{report.scenario_count} scenarios, {len(report.orphans)} orphelines"
            )
        if report.orphans:
            exit_code = 1

    return 0 if args.report_only else exit_code


if __name__ == "__main__":
    raise SystemExit(main())
