"""Correcteur collaboratif : suggestions localisées, décision de l'auteur."""

from __future__ import annotations

import datetime as dt
import uuid

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import Conflict, Forbidden, NotFound, Unprocessable
from app.models.messaging import Correction, Message
from app.services.messaging import membership
from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text

router = APIRouter(tags=["corrections"])


class CorrectionIn(BaseModel):
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)
    replacement: str = Field(min_length=1, max_length=4000)
    explanation: str | None = Field(default=None, max_length=500)


def _visible(message: Message, user_id: uuid.UUID) -> bool:
    return message.sender_id == user_id


@router.post(
    "/messages/{message_id}/corrections",
    status_code=status.HTTP_201_CREATED,
    summary="Suggérer une correction",
)
async def create_correction(
    message_id: uuid.UUID, payload: CorrectionIn, user: CurrentUser, session: SessionDep
) -> dict[str, object]:
    message = await session.get(Message, message_id)
    if message is None:
        raise NotFound("Message introuvable.")
    await membership(session, message.match_id, user.id)

    if message.sender_id == user.id:
        raise Unprocessable(
            "Impossible de corriger son propre message.",
            errors=[{"field": "message_id", "code": "own_message"}],
        )
    if message.deleted_at is not None:
        raise Unprocessable(
            "Message supprimé.", errors=[{"field": "message_id", "code": "deleted"}]
        )
    if payload.end_offset > len(message.body) or payload.end_offset <= payload.start_offset:
        raise Unprocessable(
            "Plage invalide.",
            errors=[{"field": "end_offset", "code": "invalid_range"}],
        )

    fragment = message.body[payload.start_offset : payload.end_offset]
    if not fragment:
        raise Unprocessable(
            "Plage vide.", errors=[{"field": "end_offset", "code": "invalid_range"}]
        )

    overlap = (
        await session.execute(
            text(
                "SELECT id FROM corrections WHERE message_id = :mid AND status = 'pending'"
                " AND start_offset < :end AND end_offset > :start LIMIT 1"
            ),
            {"mid": message_id, "start": payload.start_offset, "end": payload.end_offset},
        )
    ).scalar_one_or_none()
    if overlap is not None:
        raise Conflict(
            "Une suggestion existe déjà sur ce fragment.",
            errors=[{"field": "range", "code": "conflict", "correction_id": str(overlap)}],
        )

    correction = Correction(
        message_id=message_id,
        corrector_id=user.id,
        start_offset=payload.start_offset,
        end_offset=payload.end_offset,
        original_text=fragment,
        replacement=payload.replacement,
        explanation=payload.explanation,
    )
    session.add(correction)
    await session.commit()
    await session.refresh(correction)
    return {
        "id": correction.id,
        "start_offset": correction.start_offset,
        "end_offset": correction.end_offset,
        "original_text": correction.original_text,
        "replacement": correction.replacement,
        "status": correction.status,
    }


@router.get("/messages/{message_id}/corrections", summary="Corrections d'un message")
async def list_corrections(
    message_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> dict[str, object]:
    message = await session.get(Message, message_id)
    if message is None:
        raise NotFound("Message introuvable.")
    await membership(session, message.match_id, user.id)

    rows = (
        await session.execute(
            text(
                "SELECT id, corrector_id, start_offset, end_offset, original_text, replacement,"
                " explanation, status, created_at FROM corrections WHERE message_id = :mid"
                " ORDER BY created_at"
            ),
            {"mid": message_id},
        )
    ).mappings().all()

    items = []
    for row in rows:
        item = dict(row)
        # Le correcteur voit ses propres suggestions ; l'auteur voit celles des autres.
        if not _visible(message, user.id) and row["corrector_id"] != user.id:
            continue
        items.append(item)
    return {"items": items, "can_decide": _visible(message, user.id)}


async def _decide(
    correction_id: uuid.UUID, user: CurrentUser, session: SessionDep, new_status: str
) -> dict[str, object]:
    correction = await session.get(Correction, correction_id)
    if correction is None:
        raise NotFound("Correction introuvable.")
    message = await session.get(Message, correction.message_id)
    if message is None:
        raise NotFound("Message introuvable.")
    await membership(session, message.match_id, user.id)

    if message.sender_id != user.id:
        raise Forbidden("Seul l'auteur du message peut décider.")
    if correction.status != "pending":
        raise Conflict("Cette suggestion a déjà été traitée.")

    correction.status = new_status
    correction.resolved_at = dt.datetime.now(dt.UTC)
    await session.commit()
    return {"id": correction.id, "status": correction.status}


@router.post("/corrections/{correction_id}/accept", summary="Accepter une suggestion")
async def accept(correction_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> dict[str, object]:
    return await _decide(correction_id, user, session, "accepted")


@router.post("/corrections/{correction_id}/reject", summary="Refuser une suggestion")
async def reject(correction_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> dict[str, object]:
    return await _decide(correction_id, user, session, "rejected")


@router.delete(
    "/corrections/{correction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retirer sa suggestion",
)
async def withdraw(correction_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    correction = await session.get(Correction, correction_id)
    if correction is None:
        raise NotFound("Correction introuvable.")
    if correction.corrector_id != user.id:
        raise Forbidden("Seul l'auteur de la suggestion peut la retirer.")
    if correction.status != "pending":
        raise Conflict("Suggestion déjà traitée.")
    await session.delete(correction)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
