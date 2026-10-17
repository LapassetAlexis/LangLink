"""Tâche 1.6 — la matrice de couverture détecte les scénarios orphelins."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import load_script

matrix = load_script("coverage_matrix")

SPEC = """# Spec Delta — demo

## Purpose

Capacité de démonstration.

## ADDED Requirements

### Requirement: [REQ-DEM-01] Première exigence
Le système SHALL faire quelque chose.

#### Scenario: Cas nominal
- **WHEN** on appelle
- **THEN** ça marche

#### Scenario: Cas limite
- **WHEN** on appelle mal
- **THEN** ça échoue

### Requirement: [REQ-DEM-02] Seconde exigence
Le système SHALL faire autre chose.

#### Scenario: Autre cas
- **THEN** autre résultat
"""


def _make_tree(tmp_path: Path) -> Path:
    change = tmp_path / "openspec" / "changes" / "demo"
    (change / "specs" / "demo").mkdir(parents=True)
    (change / "specs" / "demo" / "spec.md").write_text(SPEC, encoding="utf-8")
    (tmp_path / "backend" / "tests").mkdir(parents=True)
    return change


def test_parses_requirements_and_scenarios(tmp_path: Path) -> None:
    change = _make_tree(tmp_path)

    report = matrix.build_report(tmp_path, change)

    assert [r.req_id for r in report.requirements] == ["REQ-DEM-01", "REQ-DEM-02"]
    assert report.scenario_count == 3
    assert report.requirements[0].capability == "demo"
    assert len(report.orphans) == 2


def test_exit_code_is_one_when_orphans_exist(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    (tmp_path / "backend" / "tests" / "test_a.py").write_text(
        'def test_a():\n    """REQ-DEM-01"""\n', encoding="utf-8"
    )

    assert matrix.main(["--root", str(tmp_path), "--change", "demo"]) == 1
    coverage = tmp_path / "openspec" / "changes" / "demo" / "coverage.md"
    assert coverage.is_file()
    assert "REQ-DEM-02" in coverage.read_text(encoding="utf-8")


def test_exit_code_is_zero_when_all_covered(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    (tmp_path / "backend" / "tests" / "test_a.py").write_text(
        'def test_a():\n    """REQ-DEM-01"""\n\ndef test_b():\n    """REQ-DEM-02"""\n',
        encoding="utf-8",
    )

    assert matrix.main(["--root", str(tmp_path), "--change", "demo"]) == 0


def test_report_only_never_fails(tmp_path: Path) -> None:
    _make_tree(tmp_path)

    assert matrix.main(["--root", str(tmp_path), "--change", "demo", "--report-only"]) == 0
