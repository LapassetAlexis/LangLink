"""Matchs : liste, détail avec icebreakers, dématch."""

from __future__ import annotations

import uuid

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import NotFound
from app.services import matching as matching_service
from fastapi import APIRouter, Response, status
from sqlalchemy import text

router = APIRouter(tags=["matching"])

LIST_SQL = """
SELECT m.id, m.status, m.affinity_score, m.last_message_at, m.created_at,
       CASE WHEN m.user_a_id = :uid THEN m.user_b_id ELSE m.user_a_id END AS other_id,
       p.display_name, p.avatar_key, p.native_language, p.target_language,
       (SELECT msg.body FROM messages msg WHERE msg.match_id = m.id
          AND msg.deleted_at IS NULL ORDER BY msg.created_at DESC, msg.id DESC LIMIT 1) AS last_body,
       (SELECT count(*) FROM messages msg WHERE msg.match_id = m.id
          AND msg.sender_id <> :uid AND msg.deleted_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM message_reads r
                          WHERE r.message_id = msg.id AND r.user_id = :uid)) AS unread
FROM matches m
JOIN profiles p ON p.user_id = CASE WHEN m.user_a_id = :uid THEN m.user_b_id ELSE m.user_a_id END
WHERE (m.user_a_id = :uid OR m.user_b_id = :uid) AND m.status = 'active'
ORDER BY m.last_message_at DESC NULLS LAST, m.created_at DESC
LIMIT 100
"""


@router.get("/matches", summary="Mes conversations")
async def list_matches(user: CurrentUser, session: SessionDep) -> dict[str, object]:
    rows = (
        await session.execute(text(LIST_SQL), {"uid": user.id})
    ).mappings().all()

    items = [
        {
            "id": row["id"],
            "status": row["status"],
            "affinity_score": row["affinity_score"],
            "other_user_id": row["other_id"],
            "display_name": row["display_name"],
            "avatar_key": row["avatar_key"],
            "languages": f"{row['native_language']} → {row['target_language']}",
            "last_message": (row["last_body"] or "")[:80] or None,
            "last_message_at": row["last_message_at"],
            "unread_count": int(row["unread"] or 0),
        }
        for row in rows
    ]
    return {"items": items}


@router.get("/matches/{match_id}", summary="Détail d'un match")
async def get_match(match_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> dict[str, object]:
    row = await matching_service.match_for_user(session, match_id, user.id)

    other = (
        await session.execute(
            text(
                "SELECT p.user_id, p.display_name, p.avatar_key, p.bio, p.birth_year,"
                " p.native_language, p.target_language, p.target_level"
                " FROM profiles p WHERE p.user_id = :oid"
            ),
            {"oid": row["other_id"]},
        )
    ).mappings().first()

    icebreakers = (
        await session.execute(
            text(
                "SELECT position, interest_slug, question_fr, question_en"
                " FROM icebreakers WHERE match_id = :mid ORDER BY position"
            ),
            {"mid": match_id},
        )
    ).mappings().all()

    return {
        "id": row["id"],
        "status": row["status"],
        "affinity_score": row["affinity_score"],
        "created_at": row["created_at"],
        "other": dict(other) if other else None,
        "icebreakers": [dict(entry) for entry in icebreakers],
    }


@router.delete(
    "/matches/{match_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Dématch (définitif)",
)
async def unmatch(match_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    result = await session.execute(
        text(
            "UPDATE matches SET status = 'unmatched'"
            " WHERE id = :mid AND (user_a_id = :uid OR user_b_id = :uid)"
            " AND status = 'active'"
        ),
        {"mid": match_id, "uid": user.id},
    )
    await session.commit()
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise NotFound("Match introuvable ou déjà fermé.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
