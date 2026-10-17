"""Primitives de sécurité : mots de passe, jetons, sessions.

Aucune règle métier ici — seulement de la cryptographie et de l'encodage, testables isolément.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets
import uuid

import jwt
from app.core.config import get_settings
from app.core.errors import TokenExpired, Unauthorized
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

ALGORITHM = "HS256"
ARGON2 = PasswordHasher()  # paramètres par défaut argon2-cffi = recommandation RFC 9106


def hash_password(password: str) -> str:
    """Empreinte Argon2id (sel aléatoire inclus dans la chaîne)."""
    return ARGON2.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Vérification à temps constant ; ne lève jamais sur un hash invalide."""
    try:
        return ARGON2.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    """JWT court (15 min par défaut) signé HS256."""
    settings = get_settings()
    now = dt.datetime.now(dt.UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(seconds=settings.access_token_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, str]:
    """Décode et valide un access token ; lève `TokenExpired` ou `Unauthorized`."""
    settings = get_settings()
    try:
        return jwt.decode(
            token, settings.jwt_secret.get_secret_value(), algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpired("Le jeton d'accès a expiré.") from exc
    except jwt.PyJWTError as exc:
        raise Unauthorized("Jeton d'accès invalide.") from exc


def new_opaque_token() -> tuple[str, str]:
    """Génère un jeton opaque et son empreinte SHA-256 (seule valeur stockée)."""
    raw = secrets.token_urlsafe(32)
    return raw, sha256_hex(raw)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
