"""Matching : swipes, matchs, icebreakers."""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ids import uuid7
from app.db.base import Base


class Swipe(Base):
    __tablename__ = "swipes"
    __table_args__ = (
        UniqueConstraint("swiper_id", "target_id", name="uq_swipes_swiper_target"),
        CheckConstraint("swiper_id <> target_id", name="no_self_swipe"),
        CheckConstraint("direction IN ('like','pass')", name="direction_valid"),
        Index("idx_swipes_target_like", "target_id", "direction"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    swiper_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_matches_pair"),
        CheckConstraint("user_a_id < user_b_id", name="canonical_pair_order"),
        CheckConstraint("status IN ('active','unmatched','blocked')", name="status_valid"),
        CheckConstraint("affinity_score BETWEEN 0 AND 100", name="affinity_range"),
        Index("idx_matches_b", "user_b_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    user_a_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user_b_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'active'")
    )
    affinity_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_message_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class Icebreaker(Base):
    __tablename__ = "icebreakers"
    __table_args__ = (
        UniqueConstraint("match_id", "position", name="uq_icebreakers_match_position"),
        CheckConstraint("position BETWEEN 1 AND 3", name="position_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    interest_slug: Mapped[str] = mapped_column(Text, nullable=False)
    question_fr: Mapped[str] = mapped_column(Text, nullable=False)
    question_en: Mapped[str] = mapped_column(Text, nullable=False)
