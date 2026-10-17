"""Fixtures de base de données pour les tests.

La base de test est un vrai PostgreSQL (jamais SQLite) : le schéma utilise `citext`,
`jsonb` et les types tableau, qu'un moteur de substitution masquerait.

Localement, l'URL est reconstruite depuis `/workspace/.langlink_stack_env.json` si
`DATABASE_URL` n'est pas fourni (la CI la fournit directement).
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import Engine, create_engine, text

REPO_ROOT = Path(__file__).resolve().parents[2]
STACK_ENV = Path(os.environ.get("LANGLLINK_STACK_ENV", "/workspace/.langlink_stack_env.json"))


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


def resolve_database_url() -> str:
    """URL de test : variable d'environnement prioritaire, sinon stack locale."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        if not STACK_ENV.exists():
            pytest.exit(
                "DATABASE_URL absent et fichier de stack introuvable : "
                "impossible de joindre une base de test",
                returncode=1,
            )
        store = json.loads(STACK_ENV.read_text())
        url = (
            "postgresql+psycopg://langlink" + chr(58) + store["POSTGRES_PASSWORD"]
            + chr(64) + "192.168.1.100:5433/langlink_test"
        )
    os.environ["DATABASE_URL"] = url
    return url


@pytest.fixture(scope="session", autouse=True)
def _configure_env() -> None:
    """Renseigne DATABASE_URL et JWT_SECRET avant que l'app ne soit construite."""
    resolve_database_url()
    os.environ.setdefault("JWT_SECRET", "tests-only-not-a-real-secret-0123456789")
    os.environ.setdefault("ENV", "dev")


@pytest.fixture(scope="session")
def db_url() -> str:
    return resolve_database_url()


@pytest.fixture(scope="session")
def engine(db_url: str) -> Iterator[Engine]:
    """Moteur de test, schéma appliqué par les migrations Alembic (pas create_all)."""
    os.environ.setdefault("JWT_SECRET", "tests-only-not-a-real-secret-0123456789")

    from alembic import command
    from alembic.config import Config

    config = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    command.upgrade(config, "head")

    eng = create_engine(db_url, pool_pre_ping=True)
    yield eng
    eng.dispose()


@pytest.fixture()
def clean_engine(engine: Engine) -> Iterator[Engine]:
    """Vide toutes les tables applicatives avant chaque test."""
    from app.db.base import Base

    names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    yield engine
