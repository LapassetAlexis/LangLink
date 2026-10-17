"""Enrôlement progressif, profil et médias."""

from __future__ import annotations

import hashlib
import uuid
from typing import Annotated

from app.api.deps import CurrentUser, SessionDep
from app.core.config import get_settings
from app.core.errors import Conflict, NotFound, Unprocessable
from app.core.security import verify_password
from app.models.identity import RefreshToken
from app.models.profile import Interest, Profile, UserInterest
from app.schemas.onboarding import (
    AvailabilityIn,
    CompleteOut,
    InterestGroupOut,
    InterestsIn,
    LanguagesIn,
    ProfileIn,
    ProfileOut,
    StateOut,
)
from app.services import catalog as catalog_service
from app.services import media as media_service
from app.services.onboarding import MAX_INTERESTS, MIN_INTERESTS, state_of
from fastapi import APIRouter, File, Response, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["onboarding"])

SUPPORTED_LANGUAGES = {
    "fr", "en", "es", "de", "it", "pt", "ja", "ko", "ar", "ru", "tr", "nl", "zh-Hans",
}


async def _profile(session: AsyncSession, user_id: uuid.UUID) -> Profile:
    profile = await session.get(Profile, user_id)
    if profile is None:
        raise NotFound("Profil introuvable.")
    return profile


async def _interest_ids(session: AsyncSession, user_id: uuid.UUID) -> list[int]:
    rows = await session.execute(
        select(UserInterest.interest_id).where(UserInterest.user_id == user_id)
    )
    return sorted(row[0] for row in rows)


@router.get("/interests", response_model=list[InterestGroupOut], summary="Catalogue d'intérêts")
async def list_interests(session: SessionDep) -> list[dict[str, object]]:
    return await catalog_service.grouped_catalog(session)


@router.get("/onboarding/state", response_model=StateOut, summary="État de l'enrôlement")
async def get_state(user: CurrentUser, session: SessionDep) -> StateOut:
    profile = await _profile(session, user.id)
    interests = await _interest_ids(session, user.id)
    state = state_of(profile, len(interests))
    return StateOut(
        **state.as_dict(),
        native_language=profile.native_language,
        target_language=profile.target_language,
        target_level=profile.target_level,
        interest_ids=interests,
        display_name=profile.display_name,
        bio=profile.bio,
        has_avatar=profile.avatar_key is not None,
    )


@router.put("/onboarding/languages", response_model=StateOut, summary="Étape 1 : langues")
async def set_languages(
    payload: LanguagesIn, user: CurrentUser, session: SessionDep
) -> StateOut:
    if payload.native_language == payload.target_language:
        raise Unprocessable(
            "La langue visée doit différer de la langue maternelle.",
            errors=[{"field": "target_language", "code": "same_as_native"}],
        )
    for code in (payload.native_language, payload.target_language):
        if code not in SUPPORTED_LANGUAGES:
            raise Unprocessable(
                f"Langue non supportée : {code}",
                errors=[{"field": "language", "code": "unsupported"}],
            )

    profile = await _profile(session, user.id)
    profile.native_language = payload.native_language
    profile.target_language = payload.target_language
    profile.target_level = payload.target_level
    profile.onboarding_step = max(profile.onboarding_step, 2)
    await session.commit()
    return await get_state(user, session)


@router.put("/onboarding/interests", response_model=StateOut, summary="Étape 2 : intérêts")
async def set_interests(
    payload: InterestsIn, user: CurrentUser, session: SessionDep
) -> StateOut:
    unique_ids = sorted(set(payload.interest_ids))
    if not MIN_INTERESTS <= len(unique_ids) <= MAX_INTERESTS:
        raise Unprocessable(
            f"Sélectionnez entre {MIN_INTERESTS} et {MAX_INTERESTS} centres d'intérêt.",
            errors=[
                {
                    "field": "interest_ids",
                    "code": "out_of_range",
                    "min": MIN_INTERESTS,
                    "max": MAX_INTERESTS,
                }
            ],
        )

    known = set(
        (
            await session.execute(
                select(Interest.id).where(Interest.id.in_(unique_ids), Interest.active.is_(True))
            )
        ).scalars()
    )
    if known != set(unique_ids):
        raise Unprocessable(
            "Certains centres d'intérêt sont inconnus ou inactifs.",
            errors=[{"field": "interest_ids", "code": "unknown_interest"}],
        )

    await session.execute(delete(UserInterest).where(UserInterest.user_id == user.id))
    session.add_all(
        [UserInterest(user_id=user.id, interest_id=interest_id) for interest_id in unique_ids]
    )
    profile = await _profile(session, user.id)
    profile.onboarding_step = max(profile.onboarding_step, 3)
    await session.commit()
    return await get_state(user, session)


@router.put("/onboarding/profile", response_model=ProfileOut, summary="Étape 3 : profil")
async def set_profile(payload: ProfileIn, user: CurrentUser, session: SessionDep) -> ProfileOut:
    profile = await _profile(session, user.id)
    profile.display_name = payload.display_name.strip()
    profile.bio = payload.bio.strip() if payload.bio else None
    profile.birth_year = payload.birth_year
    await session.commit()
    return await get_profile(user, session)


@router.post(
    "/onboarding/avatar",
    status_code=status.HTTP_201_CREATED,
    summary="Photo de profil (JPEG/PNG/WebP, 5 Mo max)",
)
async def upload_avatar(
    user: CurrentUser,
    session: SessionDep,
    file: Annotated[UploadFile, File(description="Image carrée, recadrée côté serveur")],
) -> dict[str, str]:
    data = await file.read()
    key = media_service.store_avatar(data)

    profile = await _profile(session, user.id)
    previous = profile.avatar_key
    profile.avatar_key = key
    await session.commit()

    if previous:
        import contextlib

        with contextlib.suppress(OSError):
            (get_settings().media_root / previous).unlink(missing_ok=True)
    return {"avatar_key": key}


@router.post("/onboarding/complete", response_model=CompleteOut, summary="Finaliser")
async def complete(user: CurrentUser, session: SessionDep) -> CompleteOut:
    profile = await _profile(session, user.id)
    interests = await _interest_ids(session, user.id)
    state = state_of(profile, len(interests))
    if state.missing:
        raise Conflict(
            "L'enrôlement est incomplet.",
            errors=[{"field": field, "code": "missing"} for field in state.missing],
        )

    profile.discoverable = True
    if profile.onboarding_done_at is None:
        import datetime as dt

        profile.onboarding_done_at = dt.datetime.now(dt.UTC)
    await session.commit()
    return CompleteOut(discoverable=True, step=3)


@router.get("/me/profile", response_model=ProfileOut, summary="Mon profil")
async def get_profile(user: CurrentUser, session: SessionDep) -> ProfileOut:
    profile = await _profile(session, user.id)
    return ProfileOut(
        user_id=user.id,
        display_name=profile.display_name,
        bio=profile.bio,
        birth_year=profile.birth_year,
        avatar_key=profile.avatar_key,
        native_language=profile.native_language,
        target_language=profile.target_language,
        target_level=profile.target_level,
        discoverable=profile.discoverable,
    )


@router.patch("/me/profile", response_model=ProfileOut, summary="Modifier mon profil")
async def patch_profile(
    payload: ProfileIn, user: CurrentUser, session: SessionDep
) -> ProfileOut:
    return await set_profile(payload, user, session)


@router.put("/me/availability", summary="Se rendre visible ou invisible")
async def set_availability(
    payload: AvailabilityIn, user: CurrentUser, session: SessionDep
) -> dict[str, bool]:
    profile = await _profile(session, user.id)
    if payload.discoverable:
        interests = await _interest_ids(session, user.id)
        missing = state_of(profile, len(interests)).missing
        if missing:
            raise Conflict(
                "Impossible d'être visible : enrôlement incomplet.",
                errors=[{"field": f, "code": "missing"} for f in missing],
            )
    profile.discoverable = payload.discoverable
    await session.commit()
    return {"discoverable": payload.discoverable}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer mon compte")
async def delete_account(
    payload: dict[str, str], user: CurrentUser, session: SessionDep
) -> Response:
    password = payload.get("password") or ""
    if user.password_hash is None or not verify_password(password, user.password_hash):
        raise Unprocessable(
            "Mot de passe requis pour confirmer la suppression.",
            errors=[{"field": "password", "code": "invalid"}],
        )

    profile = await _profile(session, user.id)
    if profile.avatar_key:
        (get_settings().media_root / profile.avatar_key).unlink(missing_ok=True)
        profile.avatar_key = None

    user.status = "deleted"
    user.email = f"deleted-{hashlib.sha256(str(user.id).encode()).hexdigest()[:24]}@invalid"
    # La contrainte `credential_present` interdit un compte sans credential : on stocke une
    # sentinelle qui n'est pas un hash Argon2 valide (toute vérification échoue).
    user.password_hash = "!deleted"
    user.oauth_provider = None
    user.oauth_subject = None
    profile.display_name = "Compte supprimé"
    profile.bio = None
    profile.discoverable = False
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/interests", summary="Mes centres d'intérêt")
async def my_interests(user: CurrentUser, session: SessionDep) -> dict[str, list[int]]:
    return {"interest_ids": await _interest_ids(session, user.id)}
