"""Découverte : feed réciproque, swipes, annulation bornée."""

from __future__ import annotations

import datetime as dt
import time
import uuid
from typing import Annotated

from app.api.deps import CurrentUser, SessionDep
from app.core.config import get_settings
from app.core.errors import Conflict, RateLimited
from app.services import matching as matching_service
from fastapi import APIRouter, Query, status
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter(tags=["discovery"])

# Rewind : une fois par heure et par utilisateur (instance unique, MVP).
_REWINDS: dict[uuid.UUID, float] = {}


class SwipeIn(BaseModel):
    target_id: uuid.UUID
    direction: str


class MatchSummary(BaseModel):
    id: uuid.UUID
    affinity_score: int


class SwipeOut(BaseModel):
    direction: str
    match: MatchSummary | None = None


@router.get("/discovery/feed", summary="Profils compatibles non encore swipés")
async def get_feed(
    user: CurrentUser,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=20)] = 20,
    offset: Annotated[int, Query(ge=0, le=400)] = 0,
) -> dict[str, object]:
    settings = get_settings()
    used = await matching_service.swipes_today(session, user.id)
    if used >= settings.discovery_daily_quota:
        return {"items": [], "next_offset": None, "quota_reached": True}

    day_seed = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    candidates = await matching_service.feed(
        session, user.id, limit=limit, offset=offset, day_seed=day_seed
    )

    items = [
        {
            "user_id": candidate.user_id,
            "display_name": candidate.display_name,
            "birth_year": candidate.birth_year,
            "bio": candidate.bio,
            "avatar_key": candidate.avatar_key,
            "native_language": candidate.native_language,
            "target_language": candidate.target_language,
            "target_level": candidate.target_level,
            "score": candidate.score,
            "common_interest_ids": candidate.common_ids,
        }
        for candidate in candidates
    ]
    next_offset = offset + len(items) if len(items) == limit else None
    return {
        "items": items,
        "next_offset": next_offset,
        "quota_reached": False,
        "remaining_today": max(0, settings.discovery_daily_quota - used),
    }


@router.post(
    "/discovery/swipes",
    status_code=status.HTTP_201_CREATED,
    response_model=SwipeOut,
    summary="Like ou pass",
)
async def create_swipe(payload: SwipeIn, user: CurrentUser, session: SessionDep) -> SwipeOut:
    match = await matching_service.record_swipe(
        session, user.id, payload.target_id, payload.direction
    )
    if match is None:
        return SwipeOut(direction=payload.direction)
    return SwipeOut(
        direction=payload.direction,
        match=MatchSummary(id=match.id, affinity_score=match.affinity_score),
    )


@router.delete("/discovery/swipes/{target_id}", summary="Annuler le dernier swipe (1/h)")
async def rewind(target_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> dict[str, bool]:
    settings = get_settings()
    now = time.monotonic()
    last = _REWINDS.get(user.id)
    if last is not None and now - last < settings.rewind_cooldown_seconds:
        retry = int(settings.rewind_cooldown_seconds - (now - last))
        raise RateLimited(
            "Annulation déjà utilisée récemment.",
            headers={"Retry-After": str(max(1, retry))},
        )

    deleted = await session.execute(
        text(
            "DELETE FROM swipes WHERE swiper_id = :uid AND target_id = :tid"
            " AND NOT EXISTS (SELECT 1 FROM matches m WHERE m.user_a_id = LEAST(:uid, :tid)"
            "   AND m.user_b_id = GREATEST(:uid, :tid))"
        ),
        {"uid": user.id, "tid": target_id},
    )
    await session.commit()

    if deleted.rowcount == 0:  # type: ignore[attr-defined]
        raise Conflict(
            "Aucun swipe annulable pour ce profil.",
            errors=[{"field": "target_id", "code": "no_swipe"}],
        )

    _REWINDS[user.id] = now
    return {"rewound": True}
