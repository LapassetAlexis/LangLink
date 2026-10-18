"""Routes d'authentification et de session."""

from __future__ import annotations

import asyncio
import datetime as dt
import time

import jwt
from app.api.deps import CurrentUser, SessionDep, client_ip, user_by_email
from app.core.config import get_settings
from app.core.errors import Unauthorized, Unprocessable
from app.core.security import create_access_token
from app.models.identity import User
from app.models.profile import Profile, UserInterest
from app.schemas.identity import (
    LoginIn,
    MeOut,
    OnboardingOut,
    RegisterIn,
    ResetConfirmIn,
    ResetRequestIn,
    TokenOut,
    UserOut,
    VerifyEmailIn,
)
from app.services import identity as identity_service
from app.services import oauth as oauth_service
from app.services.onboarding import state_of
from fastapi import APIRouter, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["identity"])

REFRESH_COOKIE = "refresh_token"
REFRESH_PATH = "/api/v1/auth"
ANTI_ENUMERATION_FLOOR_SECONDS = 0.25


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        role=user.role,
        status=user.status,
        email_verified=user.email_verified_at is not None,
    )


def _set_refresh_cookie(response: Response, raw: str) -> None:
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        raw,
        max_age=settings.refresh_token_ttl_days * 86_400,
        httponly=True,
        secure=settings.env == "prod",
        samesite="lax",
        path=REFRESH_PATH,
    )


async def _token_response(
    session: AsyncSession, user: User, request: Request, response: Response
) -> TokenOut:
    raw_refresh = await identity_service.issue_refresh(
        session,
        user,
        user_agent=request.headers.get("user-agent"),
        ip=client_ip(request),
    )
    _set_refresh_cookie(response, raw_refresh)
    settings = get_settings()
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        expires_in=settings.access_token_ttl_seconds,
        user=_user_out(user),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Créer un compte")
async def register(
    payload: RegisterIn, request: Request, response: Response, session: SessionDep
) -> TokenOut:
    user = await identity_service.register(
        session,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        locale=payload.locale,
        timezone=payload.timezone,
    )
    return await _token_response(session, user, request, response)


@router.post("/login", summary="Se connecter")
async def login(
    payload: LoginIn, request: Request, response: Response, session: SessionDep
) -> TokenOut:
    started = time.perf_counter()
    try:
        user = await identity_service.authenticate(
            session, email=payload.email, password=payload.password
        )
    except Unauthorized:
        # Plancher de latence : un email inconnu ne doit pas répondre plus vite qu'un
        # mot de passe erroné (anti-énumération, REQ-SAF-03).
        elapsed = time.perf_counter() - started
        if elapsed < ANTI_ENUMERATION_FLOOR_SECONDS:
            await asyncio.sleep(ANTI_ENUMERATION_FLOOR_SECONDS - elapsed)
        raise
    return await _token_response(session, user, request, response)


@router.post("/refresh", summary="Rotation du jeton de session")
async def refresh(request: Request, response: Response, session: SessionDep) -> TokenOut:
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise Unauthorized("Session absente.")
    user, new_raw = await identity_service.rotate_refresh(
        session, raw, user_agent=request.headers.get("user-agent"), ip=client_ip(request)
    )
    _set_refresh_cookie(response, new_raw)
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        expires_in=get_settings().access_token_ttl_seconds,
        user=_user_out(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Fermer la session")
async def logout(request: Request, response: Response, session: SessionDep) -> Response:
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        await identity_service.revoke_one(session, raw)
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT, summary="Fermer toutes les sessions")
async def logout_all(response: Response, user: CurrentUser, session: SessionDep) -> Response:
    await identity_service.revoke_all(session, user.id)
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", summary="Utilisateur courant et état d'enrôlement")
async def me(user: CurrentUser, session: SessionDep) -> MeOut:
    profile = await session.get(Profile, user.id)
    count = await session.scalar(
        select(func.count()).select_from(UserInterest).where(UserInterest.user_id == user.id)
    )
    if profile is None:
        raise Unauthorized("Profil introuvable.")
    state = state_of(profile, count or 0)
    return MeOut(user=_user_out(user), onboarding=OnboardingOut(**state.as_dict()))


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED, summary="Demander une réinitialisation")
async def forgot_password(payload: ResetRequestIn, session: SessionDep) -> dict[str, str]:
    """Réponse identique que l'email existe ou non (anti-énumération)."""
    user = await user_by_email(session, payload.email)
    if user is not None and user.status == "active":
        await identity_service.issue_one_time_token(session, user, "reset_password", ttl_minutes=60)
        # En V1 l'envoi d'email est hors périmètre : le jeton est journalisé côté serveur.
    return {"status": "accepted"}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT, summary="Réinitialiser le mot de passe")
async def reset_password(payload: ResetConfirmIn, session: SessionDep) -> Response:
    user = await identity_service.consume_one_time_token(session, payload.token, "reset_password")
    from app.core.security import hash_password

    user.password_hash = hash_password(payload.new_password)
    await session.commit()
    await identity_service.revoke_all(session, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT, summary="Vérifier l'email")
async def verify_email(payload: VerifyEmailIn, session: SessionDep) -> Response:
    user = await identity_service.consume_one_time_token(session, payload.token, "verify_email")
    user.email_verified_at = dt.datetime.now(dt.UTC)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- OAuth -------------------------------------------------------------------


def _signed_state(provider: str, verifier: str) -> str:
    settings = get_settings()
    now = dt.datetime.now(dt.UTC)
    return jwt.encode(
        {
            "provider": provider,
            "verifier": verifier,
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(minutes=5)).timestamp()),
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def _read_state(state: str, provider: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(
            state, settings.jwt_secret.get_secret_value(), algorithms=["HS256"]
        )
    except jwt.PyJWTError as exc:
        raise Unprocessable("État OAuth invalide.", errors=[{"field": "state", "code": "invalid"}]) from exc
    if payload.get("provider") != provider:
        raise Unprocessable("État OAuth incohérent.", errors=[{"field": "state", "code": "mismatch"}])
    return str(payload["verifier"])


@router.get("/oauth/{provider}/start", summary="Démarrer le flux OAuth")
async def oauth_start(provider: str, request: Request) -> Response:
    definition = oauth_service.PROVIDERS.get(provider)
    if definition is None:
        raise Unprocessable("Fournisseur inconnu.", errors=[{"field": "provider", "code": "unknown"}])
    settings = get_settings()
    client_id = (
        settings.google_client_id if provider == "google" else settings.github_client_id
    )
    if not client_id:
        raise Unprocessable("Fournisseur non configuré.", errors=[{"field": "provider", "code": "disabled"}])

    verifier, challenge = oauth_service.pkce_pair()
    redirect_uri = f"{settings.public_base_url}/api/v1/auth/oauth/{provider}/callback"
    url = oauth_service.authorize_url(
        definition,
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=_signed_state(provider, verifier),
        challenge=challenge,
    )
    return Response(status_code=status.HTTP_302_FOUND, headers={"Location": url})


@router.get("/oauth/{provider}/callback", summary="Retour du fournisseur OAuth")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    session: SessionDep,
    request: Request,
) -> Response:
    definition = oauth_service.PROVIDERS.get(provider)
    if definition is None:
        raise Unprocessable("Fournisseur inconnu.", errors=[{"field": "provider", "code": "unknown"}])

    verifier = _read_state(state, provider)
    settings = get_settings()
    if provider == "google":
        client_id, secret = settings.google_client_id, settings.google_client_secret
    else:
        client_id, secret = settings.github_client_id, settings.github_client_secret
    if not client_id or secret is None:
        raise Unprocessable("Fournisseur non configuré.", errors=[{"field": "provider", "code": "disabled"}])

    identity = await oauth_service.exchange_code(
        definition,
        code=code,
        client_id=client_id,
        client_secret=secret.get_secret_value(),
        redirect_uri=f"{settings.public_base_url}/api/v1/auth/oauth/{provider}/callback",
        verifier=verifier,
    )

    user = (
        await session.execute(
            select(User).where(
                User.oauth_provider == identity.provider,
                User.oauth_subject == identity.subject,
            )
        )
    ).scalar_one_or_none()

    if user is None:
        user = await user_by_email(session, identity.email)
        if user is None:
            user = User(
                email=identity.email.lower(),
                oauth_provider=identity.provider,
                oauth_subject=identity.subject,
                email_verified_at=dt.datetime.now(dt.UTC) if identity.email_verified else None,
            )
            session.add(user)
            await session.flush()
            session.add(
                Profile(user_id=user.id, display_name=identity.email.split("@")[0][:40])
            )
        else:
            # Rapprochement : le mot de passe existant n'est jamais écrasé.
            user.oauth_provider = identity.provider
            user.oauth_subject = identity.subject
        await session.commit()
        await session.refresh(user)

    raw = await identity_service.issue_refresh(
        session, user, user_agent=request.headers.get("user-agent"), ip=client_ip(request)
    )
    redirect = Response(status_code=status.HTTP_302_FOUND, headers={"Location": "/onboarding"})
    _set_refresh_cookie(redirect, raw)
    return redirect
