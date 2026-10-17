"""Règles métier de l'identité : inscription, sessions, jetons à usage unique."""

from __future__ import annotations

import datetime as dt
import uuid

from app.core.config import get_settings
from app.core.errors import Conflict, TokenExpired, Unauthorized, Unprocessable
from app.core.security import hash_password, new_opaque_token, sha256_hex, verify_password
from app.models.identity import OneTimeToken, RefreshToken, User
from app.models.profile import Profile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

COMMON_WEAK = {
    "password", "password1", "motdepasse", "123456789", "1234567890", "azertyuiop",
    "qwertyuiop", "langlink", "iloveyou", "admin1234", "changeme", "motdepasse1",
}
MIN_LENGTH = 10


async def register(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    display_name: str | None = None,
    locale: str = "fr",
) -> User:
    """Crée un compte actif + un profil vide. La vérification d'email n'est pas bloquante."""
    normalized = email.lower().strip()
    existing = await session.execute(select(User.id).where(User.email == normalized))
    if existing.scalar_one_or_none() is not None:
        raise Conflict("Cet email est déjà utilisé.", errors=[{"field": "email", "code": "email_taken"}])

    if len(password) < MIN_LENGTH or password.lower() in COMMON_WEAK:
        raise Unprocessable(
            "Mot de passe trop faible.",
            errors=[{"field": "password", "code": "weak_password"}],
        )

    user = User(
        email=normalized,
        password_hash=hash_password(password),
        locale=locale,
    )
    session.add(user)
    await session.flush()

    name = display_name or normalized.split("@")[0][:40] or "Explorateur"
    session.add(Profile(user_id=user.id, display_name=name[:40]))
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User:
    """Vérifie les identifiants. Réponse et coût identiques si le compte n'existe pas."""
    user = (
        await session.execute(select(User).where(User.email == email.lower().strip()))
    ).scalar_one_or_none()

    # Hachage factice : même coût CPU qu'une vérification réelle (anti-énumération).
    if user is None or user.password_hash is None:
        hash_password("mot-de-passe-factice-pour-egaliser-le-temps")
        raise Unauthorized("Email ou mot de passe incorrect.")

    if not verify_password(password, user.password_hash):
        raise Unauthorized("Email ou mot de passe incorrect.")
    if user.status == "deleted":
        raise Unauthorized("Email ou mot de passe incorrect.")
    return user


async def issue_refresh(session: AsyncSession, user: User, *, user_agent: str | None, ip: str | None) -> str:
    """Enregistre un refresh token (empreinte SHA-256) et renvoie la valeur brute."""
    settings = get_settings()
    raw, digest = new_opaque_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=digest,
            expires_at=dt.datetime.now(dt.UTC)
            + dt.timedelta(days=settings.refresh_token_ttl_days),
            user_agent=(user_agent or "")[:500] or None,
            ip_hash=sha256_hex(ip) if ip else None,
        )
    )
    await session.commit()
    return raw


async def rotate_refresh(session: AsyncSession, raw: str, *, user_agent: str | None, ip: str | None) -> tuple[User, str]:
    """Consomme un refresh token et en émet un nouveau (rotation stricte)."""
    digest = sha256_hex(raw)
    token = (
        await session.execute(select(RefreshToken).where(RefreshToken.token_hash == digest))
    ).scalar_one_or_none()

    if token is None:
        raise Unauthorized("Session inconnue.")

    if token.revoked_at is not None:
        # Rejeu d'un jeton déjà consommé : on coupe toutes les sessions de l'utilisateur.
        await revoke_all(session, token.user_id)
        raise TokenExpired("Session révoquée.")

    if token.expires_at <= dt.datetime.now(dt.UTC):
        raise TokenExpired("Session expirée.")

    user = await session.get(User, token.user_id)
    if user is None or user.status != "active":
        raise Unauthorized("Compte indisponible.")

    token.revoked_at = dt.datetime.now(dt.UTC)
    await session.commit()
    return user, await issue_refresh(session, user, user_agent=user_agent, ip=ip)


async def revoke_all(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=dt.datetime.now(dt.UTC))
    )
    await session.commit()


async def revoke_one(session: AsyncSession, raw: str) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == sha256_hex(raw), RefreshToken.revoked_at.is_(None))
        .values(revoked_at=dt.datetime.now(dt.UTC))
    )
    await session.commit()


async def issue_one_time_token(
    session: AsyncSession, user: User, purpose: str, ttl_minutes: int = 60
) -> str:
    raw, digest = new_opaque_token()
    session.add(
        OneTimeToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=digest,
            expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(minutes=ttl_minutes),
        )
    )
    await session.commit()
    return raw


async def consume_one_time_token(session: AsyncSession, raw: str, purpose: str) -> User:
    token = (
        await session.execute(
            select(OneTimeToken).where(
                OneTimeToken.token_hash == sha256_hex(raw),
                OneTimeToken.purpose == purpose,
            )
        )
    ).scalar_one_or_none()

    if token is None:
        raise Unprocessable("Jeton invalide.", errors=[{"field": "token", "code": "invalid"}])
    if token.used_at is not None or token.expires_at <= dt.datetime.now(dt.UTC):
        raise Unprocessable("Jeton expiré.", errors=[{"field": "token", "code": "expired"}])
    token.used_at = dt.datetime.now(dt.UTC)
    await session.commit()
    user = await session.get(User, token.user_id)
    if user is None:
        raise Unprocessable("Jeton invalide.", errors=[{"field": "token", "code": "invalid"}])
    return user
