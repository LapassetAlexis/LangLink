"""Messagerie asynchrone : envoi, pagination, lecture, édition, suppression."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import Forbidden, NotFound, Unprocessable
from app.services import messaging as messaging_service
from fastapi import APIRouter, Header, Query, Request, Response, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["messaging"])


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    body_lang: str | None = Field(default=None, max_length=16)


class ReadIn(BaseModel):
    last_message_id: uuid.UUID


@router.post(
    "/matches/{match_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Envoyer un message",
)
async def send_message(
    match_id: uuid.UUID,
    payload: MessageIn,
    user: CurrentUser,
    session: SessionDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, object]:
    message = await messaging_service.send(
        session,
        match_id=match_id,
        sender_id=user.id,
        body=payload.body,
        body_lang=payload.body_lang,
        client_key=idempotency_key,
    )
    return {
        "id": message.id,
        "body": message.body,
        "created_at": message.created_at,
        "edited_at": message.edited_at,
    }


@router.get("/matches/{match_id}/messages", summary="Page de messages")
async def list_messages(
    match_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    before: uuid.UUID | None = None,
) -> dict[str, object]:
    items = await messaging_service.page(
        session, match_id, user.id, limit=limit, before=before
    )
    next_cursor = items[-1]["id"] if len(items) == limit else None
    return {"items": items, "next_cursor": next_cursor}


@router.post("/matches/{match_id}/read", summary="Marquer comme lu")
async def mark_read(
    match_id: uuid.UUID, payload: ReadIn, user: CurrentUser, session: SessionDep
) -> dict[str, int]:
    await messaging_service.mark_read(session, match_id, user.id, payload.last_message_id)
    return {"unread_count": 0}


@router.get("/matches/{match_id}/unread-count", summary="Compteur de non-lus (ETag)")
async def unread_count(
    match_id: uuid.UUID, request: Request, user: CurrentUser, session: SessionDep
) -> Response:
    import json

    count = await messaging_service.unread_count(session, match_id, user.id)
    etag = f'W/"{match_id}-{count}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
    return Response(
        content=json.dumps({"unread_count": count}),
        media_type="application/json",
        headers={"ETag": etag, "Cache-Control": "no-cache"},
    )


@router.patch("/messages/{message_id}", summary="Éditer son message (15 min)")
async def edit_message(
    message_id: uuid.UUID, payload: MessageIn, user: CurrentUser, session: SessionDep
) -> dict[str, object]:
    message = await messaging_service.ensure_author(session, message_id, user.id)
    if message.deleted_at is not None:
        raise Unprocessable("Message supprimé.", errors=[{"field": "message_id", "code": "deleted"}])
    if dt.datetime.now(dt.UTC) - message.created_at > messaging_service.EDIT_WINDOW:
        raise Forbidden("Le délai d'édition est dépassé.")

    cleaned = payload.body.strip()
    if not cleaned or len(cleaned) > messaging_service.MAX_BODY:
        raise Unprocessable(
            "Contenu invalide.", errors=[{"field": "body", "code": "invalid_length"}]
        )

    message.body = cleaned
    message.edited_at = dt.datetime.now(dt.UTC)
    await messaging_service.expire_stale_corrections(session, message)
    await session.commit()
    return {"id": message.id, "body": message.body, "edited_at": message.edited_at}


@router.delete(
    "/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer (soft)"
)
async def delete_message(
    message_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> Response:
    message = await messaging_service.ensure_author(session, message_id, user.id)
    message.body = messaging_service.DELETED_BODY
    message.deleted_at = dt.datetime.now(dt.UTC)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/messages/{message_id}", summary="Un message")
async def get_message(
    message_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> dict[str, object]:
    message = await session.get(__import__("app.models.messaging", fromlist=["Message"]).Message, message_id)
    if message is None:
        raise NotFound("Message introuvable.")
    await messaging_service.membership(session, message.match_id, user.id)
    return {
        "id": message.id,
        "body": message.body,
        "created_at": message.created_at,
        "edited_at": message.edited_at,
        "deleted_at": message.deleted_at,
    }
