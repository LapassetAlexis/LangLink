"""Sécurité : blocage, signalement, modération."""

from __future__ import annotations

import uuid

from app.api.deps import AdminUser, CurrentUser, SessionDep
from app.core.errors import Conflict, NotFound, Unprocessable
from app.models.safety import Report
from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text

router = APIRouter(tags=["safety"])


class ReportIn(BaseModel):
    reported_user_id: uuid.UUID
    message_id: uuid.UUID | None = None
    category: str = Field(pattern="^(spam|harassment|hate|sexual|scam|other)$")
    comment: str | None = Field(default=None, max_length=1000)


class ReportUpdateIn(BaseModel):
    status: str = Field(pattern="^(open|reviewing|actioned|dismissed)$")


@router.post("/users/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT, summary="Bloquer")
async def block(user_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    if user_id == user.id:
        raise Unprocessable("Impossible de se bloquer soi-même.")
    if await session.get(__import__("app.models.identity", fromlist=["User"]).User, user_id) is None:
        raise NotFound("Profil introuvable.")

    await session.execute(
        text(
            "INSERT INTO blocks (blocker_id, blocked_id, created_at) VALUES (:a, :b, now())"
            " ON CONFLICT DO NOTHING"
        ),
        {"a": user.id, "b": user_id},
    )
    await session.execute(
        text(
            "UPDATE matches SET status = 'blocked'"
            " WHERE (user_a_id = :a AND user_b_id = :b) OR (user_a_id = :b AND user_b_id = :a)"
        ),
        {"a": user.id, "b": user_id},
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/users/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT, summary="Débloquer")
async def unblock(user_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    await session.execute(
        text("DELETE FROM blocks WHERE blocker_id = :a AND blocked_id = :b"),
        {"a": user.id, "b": user_id},
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/blocks", summary="Mes profils bloqués")
async def list_blocks(user: CurrentUser, session: SessionDep) -> dict[str, object]:
    rows = (
        await session.execute(
            text(
                "SELECT b.blocked_id, p.display_name, b.created_at FROM blocks b"
                " JOIN profiles p ON p.user_id = b.blocked_id WHERE b.blocker_id = :uid"
                " ORDER BY b.created_at DESC"
            ),
            {"uid": user.id},
        )
    ).mappings().all()
    return {"items": [dict(row) for row in rows]}


@router.post("/reports", status_code=status.HTTP_201_CREATED, summary="Signaler")
async def create_report(payload: ReportIn, user: CurrentUser, session: SessionDep) -> dict[str, object]:
    snapshot = None
    if payload.message_id is not None:
        row = (
            await session.execute(
                text("SELECT body FROM messages WHERE id = :mid"), {"mid": payload.message_id}
            )
        ).first()
        if row is None:
            raise NotFound("Message introuvable.")
        snapshot = row[0]

    if payload.reported_user_id == user.id:
        raise Conflict("Impossible de se signaler soi-même.")

    report = Report(
        reporter_id=user.id,
        reported_user_id=payload.reported_user_id,
        message_id=payload.message_id,
        category=payload.category,
        comment=payload.comment,
        content_snapshot=snapshot,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return {"id": report.id, "status": report.status}


@router.patch("/admin/reports/{report_id}", summary="Traiter un signalement (admin)")
async def handle_report(
    report_id: uuid.UUID, payload: ReportUpdateIn, admin: AdminUser, session: SessionDep
) -> dict[str, object]:
    result = await session.execute(
        text(
            "UPDATE reports SET status = :s, handled_at = now(), handled_by = :by WHERE id = :id"
        ),
        {"s": payload.status, "by": admin.id, "id": report_id},
    )
    await session.commit()
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise NotFound("Signalement introuvable.")
    return {"id": report_id, "status": payload.status}


@router.post(
    "/admin/users/{user_id}/suspend",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Suspendre un compte (admin)",
)
async def suspend(user_id: uuid.UUID, admin: AdminUser, session: SessionDep) -> Response:
    result = await session.execute(
        text(
            "UPDATE users SET status = 'suspended' WHERE id = :id AND status = 'active'"
            " AND id <> :admin"
        ),
        {"id": user_id, "admin": admin.id},
    )
    await session.execute(
        text("UPDATE profiles SET discoverable = false WHERE user_id = :id"), {"id": user_id}
    )
    await session.commit()
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise NotFound("Compte introuvable ou déjà suspendu.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
