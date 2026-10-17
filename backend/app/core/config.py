"""Configuration applicative, validée au démarrage.

Toute la configuration vient de l'environnement (douze-factor) : aucun secret par défaut,
aucune valeur de production en dur. Les variables manquantes sont signalées en une seule
erreur, avec la liste complète — c'est le critère de vérification de la tâche 1.4.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_JWT_SECRET_LENGTH = 32
MIN_PROD_JWT_SECRET_LENGTH = 48


class Settings(BaseSettings):
    """Réglages lus depuis l'environnement, typés et validés."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Obligatoires : aucune valeur par défaut, sinon on démarre sur un secret partagé.
    database_url: str = Field(description="DSN PostgreSQL")
    jwt_secret: SecretStr = Field(description="Secret de signature des access tokens")

    # --- Environnement
    env: Literal["dev", "test", "prod"] = "dev"
    public_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:5173"

    # --- Médias
    media_root: Path = Path("/data/uploads")
    media_max_bytes: int = 5 * 1024 * 1024

    # --- Jetons
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_days: int = 30

    # --- Produit
    discovery_daily_quota: int = 20
    rewind_cooldown_seconds: int = 3600
    message_max_length: int = 4000

    # --- Traduction
    libretranslate_url: str = "http://libretranslate:5000"
    libretranslate_timeout_seconds: float = 5.0
    deepl_api_key: SecretStr | None = None

    @field_validator("database_url")
    @classmethod
    def _require_postgres(cls, value: str) -> str:
        if not value.startswith("postgresql"):
            msg = "DATABASE_URL doit etre un DSN PostgreSQL"
            raise ValueError(msg)
        return value

    @field_validator("jwt_secret")
    @classmethod
    def _require_long_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_JWT_SECRET_LENGTH:
            msg = f"JWT_SECRET doit contenir au moins {MIN_JWT_SECRET_LENGTH} caractères"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _production_hardening(self) -> Settings:
        if self.env != "prod":
            return self
        if len(self.jwt_secret.get_secret_value()) < MIN_PROD_JWT_SECRET_LENGTH:
            msg = (
                f"En production, JWT_SECRET doit contenir au moins "
                f"{MIN_PROD_JWT_SECRET_LENGTH} caractères"
            )
            raise ValueError(msg)
        if not self.public_base_url.startswith("https://"):
            msg = "En production, PUBLIC_BASE_URL doit être en https://"
            raise ValueError(msg)
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        """Origines CORS sous forme de liste, séparées par des virgules."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Instance unique des réglages, construite au premier accès."""
    return Settings()
