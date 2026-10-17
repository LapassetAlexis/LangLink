"""Messagerie et corrections : accès au fil, envoi idempotent, rendu des corrections."""

from __future__ import annotations

import datetime as dt
import uuid

from app.core.errors import Conflict, Forbidden, NotFound, Unprocessable
from app.models.messaging import Message
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DELETED_BODY = "[message supprimé]"
EDIT_WINDOW = dt.timedelta(minutes=15)
MAX_BODY = 4000


async def membership(session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, object]:
    """Vérifie l'appartenance au match. 404 (et non 403) pour ne pas révéler son existence."""
    row = (
        await session.execute(
            text(
                "SELECT id, status, user_a_id, user_b_id FROM matches WHERE id = :mid"
                " AND (user_a_id = :uid OR user_b_id = :uid)"
            ),
            {"mid": match_id, "uid": user_id},
        )
    ).mappings().first()
    if row is None:
        raise NotFound("Match introuvable.")
    return dict(row)


async def send(
    session: AsyncSession,
    *,
    match_id: uuid.UUID,
    sender_id: uuid.UUID,
    body: str,
    body_lang: str | None,
    client_key: str | None,
) -> Message:
    row = await membership(session, match_id, sender_id)
    if row["status"] != "active":
        raise Conflict("Cette conversation est fermée.")

    blocked = await session.scalar(
        text(
            "SELECT 1 FROM blocks b JOIN matches m ON m.id = :mid"
            " WHERE (b.blocker_id = m.user_a_id AND b.blocked_id = m.user_b_id)"
            "    OR (b.blocker_id = m.user_b_id AND b.blocked_id = m.user_a_id) LIMIT 1"
        ),
        {"mid": match_id},
    )
    if blocked:
        raise Forbidden("Interaction bloquée avec ce profil.")

    cleaned = body.strip()
    if not cleaned or len(cleaned) > MAX_BODY:
        raise Unprocessable(
            f"Le message doit contenir entre 1 et {MAX_BODY} caractères.",
            errors=[{"field": "body", "code": "invalid_length"}],
        )

    if client_key:
        existing = (
            await session.execute(
                text(
                    "SELECT * FROM messages WHERE match_id = :mid AND sender_id = :sid"
                    " AND client_key = :key"
                ),
                {"mid": match_id, "sid": sender_id, "key": client_key},
            )
        ).mappings().first()
        if existing is not None:
            return await session.get(Message, existing["id"])  # type: ignore[return-value]

    message = Message(
        match_id=match_id,
        sender_id=sender_id,
        body=cleaned,
        body_lang=body_lang,
        client_key=client_key,
    )
    session.add(message)
    await session.execute(
        text("UPDATE matches SET last_message_at = now() WHERE id = :mid"), {"mid": match_id}
    )
    await session.commit()
    await session.refresh(message)
    return message


async def page(
    session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID, *, limit: int, before: uuid.UUID | None
) -> list[dict[str, object]]:
    await membership(session, match_id, user_id)

    params: dict[str, object] = {"mid": match_id, "limit": limit}
    cursor_clause = ""
    if before is not None:
        cursor_clause = (
            " AND (m.created_at, m.id) < (SELECT created_at, id FROM messages WHERE id = :before)"
        )
        params["before"] = before

    rows = (
        await session.execute(
            text(
                "SELECT m.id, m.sender_id, m.body, m.body_lang, m.created_at, m.edited_at,"
                " m.deleted_at FROM messages m WHERE m.match_id = :mid"
                + cursor_clause
                + " ORDER BY m.created_at DESC, m.id DESC LIMIT :limit"
            ),
            params,
        )
    ).mappings().all()

    ids = [row["id"] for row in rows]
    corrections = (
        await session.execute(
            text(
                "SELECT id, message_id, corrector_id, start_offset, end_offset, original_text,"
                " replacement, explanation, status FROM corrections"
                " WHERE message_id = ANY(:ids) ORDER BY created_at"
            ),
            {"ids": ids},
        )
    ).mappings().all() if ids else []

    by_message: dict[uuid.UUID, list[dict[str, object]]] = {}
    for correction in corrections:
        by_message.setdefault(correction["message_id"], []).append(dict(correction))

    items = []
    for row in rows:
        accepted = [
            c for c in by_message.get(row["id"], []) if c["status"] == "accepted"
        ]
        items.append(
            {
                "id": row["id"],
                "sender_id": row["sender_id"],
                "body": row["body"],
                "body_rendered": apply_corrections(row["body"], accepted),
                "body_lang": row["body_lang"],
                "created_at": row["created_at"],
                "edited_at": row["edited_at"],
                "deleted_at": row["deleted_at"],
                "corrections": by_message.get(row["id"], []),
            }
        )
    return items


def apply_corrections(body: str, accepted: list[dict[str, object]]) -> str:
    """Applique les corrections acceptées, de la fin vers le début (offsets stables)."""
    if not accepted:
        return body
    pieces = list(body)
    for correction in sorted(
        accepted, key=lambda c: int(str(c["start_offset"])), reverse=True
    ):
        start = int(str(correction["start_offset"]))
        end = int(str(correction["end_offset"]))
        pieces[start:end] = list(str(correction["replacement"]))
    return "".join(pieces)


async def mark_read(session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID, last_id: uuid.UUID) -> int:
    await membership(session, match_id, user_id)
    await session.execute(
        text(
            "INSERT INTO message_reads (message_id, user_id, read_at)"
            " SELECT m.id, :uid, now() FROM messages m"
            " WHERE m.match_id = :mid AND m.sender_id <> :uid"
            "   AND (m.created_at, m.id) <= (SELECT created_at, id FROM messages WHERE id = :last)"
            " ON CONFLICT (message_id, user_id) DO NOTHING"
        ),
        {"mid": match_id, "uid": user_id, "last": last_id},
    )
    await session.commit()
    return 0


async def unread_count(session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID) -> int:
    await membership(session, match_id, user_id)
    return int(
        await session.scalar(
            text(
                "SELECT count(*) FROM messages m WHERE m.match_id = :mid"
                " AND m.sender_id <> :uid AND m.deleted_at IS NULL"
                " AND NOT EXISTS (SELECT 1 FROM message_reads r"
                "                 WHERE r.message_id = m.id AND r.user_id = :uid)"
            ),
            {"mid": match_id, "uid": user_id},
        )
        or 0
    )


async def ensure_author(session: AsyncSession, message_id: uuid.UUID, user_id: uuid.UUID) -> Message:
    message = await session.get(Message, message_id)
    if message is None:
        raise NotFound("Message introuvable.")
    if message.sender_id != user_id:
        raise Forbidden("Seul l'auteur peut modifier ce message.")
    return message


async def expire_stale_corrections(session: AsyncSession, message: Message) -> None:
    """Après édition : les corrections dont les offsets ne collent plus passent à `stale`."""
    rows = (
        await session.execute(
            text(
                "SELECT id, start_offset, end_offset, original_text FROM corrections"
                " WHERE message_id = :mid AND status = 'pending'"
            ),
            {"mid": message.id},
        )
    ).mappings().all()
    for row in rows:
        start, end = int(str(row["start_offset"])), int(str(row["end_offset"]))
        if start > len(message.body) or message.body[start:end] != row["original_text"]:
            await session.execute(
                text("UPDATE corrections SET status = 'stale' WHERE id = :id"), {"id": row["id"]}
            )
