"""Fixtures partagées : chargement des scripts de garde-fou sans packaging."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str) -> ModuleType:
    """Charge `scripts/<name>.py` comme module importable."""
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_langlink_{name}", path)
    if spec is None or spec.loader is None:  # pragma: no cover - garde-fou
        raise RuntimeError(f"impossible de charger {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
