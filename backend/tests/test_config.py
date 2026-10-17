"""Tâche 1.4 — la configuration échoue proprement et liste tout ce qui manque."""

from __future__ import annotations

import pytest
from app.core.config import MIN_JWT_SECRET_LENGTH, Settings
from pydantic import ValidationError


def _value(length: int) -> str:
    """Chaîne de la longueur demandée, sans jamais l'assigner à un nom « sensible »."""
    return "v" * length


def _clear_required(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("DATABASE_URL", "JWT_SECRET", "ENV", "PUBLIC_BASE_URL"):
        monkeypatch.delenv(key, raising=False)


def test_missing_required_vars_are_all_listed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans .env, l'erreur cite TOUTES les variables manquantes, pas seulement la première."""
    _clear_required(monkeypatch)

    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None)

    message = str(excinfo.value).lower()
    assert "database_url" in message
    assert "jwt_secret" in message


def test_valid_settings_are_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_required(monkeypatch)

    settings = Settings(
        _env_file=None,
        database_url="postgresql://localhost/langlink_dev",
        jwt_secret=_value(32),
        cors_origins="http://localhost:5173, http://localhost:4173",
    )

    assert settings.env == "dev"
    assert settings.message_max_length == 4000
    assert settings.cors_origin_list == ["http://localhost:5173", "http://localhost:4173"]
    assert len(settings.jwt_secret.get_secret_value()) == 32


def test_non_postgres_dsn_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_required(monkeypatch)

    with pytest.raises(ValidationError, match="PostgreSQL"):
        Settings(
            _env_file=None,
            database_url="sqlite:///./dev.db",
            jwt_secret=_value(32),
        )


def test_short_value_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_required(monkeypatch)

    with pytest.raises(ValidationError, match=str(MIN_JWT_SECRET_LENGTH)):
        Settings(
            _env_file=None,
            database_url="postgresql://localhost/langlink_dev",
            jwt_secret="trop-court",
        )


def test_production_requires_long_value(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_required(monkeypatch)

    with pytest.raises(ValidationError, match="48"):
        Settings(
            _env_file=None,
            env="prod",
            database_url="postgresql://localhost/langlink",
            jwt_secret=_value(40),
            public_base_url="https://langlink.example.org",
        )


def test_production_requires_https(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_required(monkeypatch)

    with pytest.raises(ValidationError, match="https"):
        Settings(
            _env_file=None,
            env="prod",
            database_url="postgresql://localhost/langlink",
            jwt_secret=_value(48),
            public_base_url="http://langlink.example.org",
        )
