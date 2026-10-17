"""Fournisseurs OAuth (Google, GitHub) — Authorization Code + PKCE.

L'échange de code est isolé dans `exchange_code()` pour être remplaçable en test : aucun
appel réseau ne doit avoir lieu dans la suite de tests.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import urllib.parse
from dataclasses import dataclass

import httpx
from app.core.errors import Unprocessable


@dataclass(frozen=True)
class Provider:
    name: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: str


PROVIDERS: dict[str, Provider] = {
    "google": Provider(
        name="google",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
        scope="openid email profile",
    ),
    "github": Provider(
        name="github",
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scope="read:user user:email",
    ),
}


@dataclass(frozen=True)
class Identity:
    provider: str
    subject: str
    email: str
    email_verified: bool


def pkce_pair() -> tuple[str, str]:
    """Renvoie (verifier, challenge S256)."""
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    return verifier, challenge


def authorize_url(provider: Provider, *, client_id: str, redirect_uri: str, state: str, challenge: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": provider.scope,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
    }
    return f"{provider.authorize_url}?{urllib.parse.urlencode(params)}"


async def exchange_code(
    provider: Provider, *, code: str, client_id: str, client_secret: str, redirect_uri: str, verifier: str
) -> Identity:
    """Échange le code contre un jeton puis récupère l'identité. Réseau : uniquement ici."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            provider.token_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
            headers={"Accept": "application/json"},
        )
        if token_response.status_code >= 400:
            raise Unprocessable("Échange OAuth refusé par le fournisseur.")
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise Unprocessable("Jeton OAuth absent.")

        userinfo = await client.get(
            provider.userinfo_url,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        if userinfo.status_code >= 400:
            raise Unprocessable("Profil OAuth inaccessible.")
        data = userinfo.json()

        if provider.name == "github":
            email = data.get("email")
            if not email:
                emails = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                primary = next(
                    (e for e in emails.json() if e.get("primary")), None
                ) if emails.status_code < 400 else None
                email = primary.get("email") if primary else None
            if not email:
                raise Unprocessable("Aucun email vérifié renvoyé par GitHub.")
            return Identity("github", str(data["id"]), email, True)

        email = data.get("email")
        if not email:
            raise Unprocessable("Aucun email renvoyé par Google.")
        return Identity("google", str(data["sub"]), email, bool(data.get("email_verified")))
