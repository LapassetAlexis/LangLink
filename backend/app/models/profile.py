"""Profil, référentiel d'intérêts et sélection."""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint(
            "char_length(display_name) BETWEEN 2 AND 40", name="display_name_length"
        ),
        CheckConstraint("birth_year BETWEEN 1900 AND 2100", name="birth_year_range"),
        CheckConstraint("char_length(bio) <= 600", name="bio_length"),
        CheckConstraint(
            "target_level IN ('A1','A2','B1','B2','C1','C2')", name="target_level_valid"
        ),
        CheckConstraint("onboarding_step BETWEEN 1 AND 3", name="onboarding_step_range"),
        CheckConstraint(
            "native_language IS NULL OR target_language IS NULL "
            "OR native_language <> target_language",
            name="languages_differ",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(40), nullable=False)
    birth_year: Mapped[int | None] = mapped_column(SmallInteger)
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_key: Mapped[str | None] = mapped_column(Text)
    native_language: Mapped[str | None] = mapped_column(String(16))
    target_language: Mapped[str | None] = mapped_column(String(16))
    target_level: Mapped[str | None] = mapped_column(String(2))
    onboarding_step: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("1")
    )
    onboarding_done_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    discoverable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    preferences: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb"), default=dict
    )
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=text("'Europe/Paris'")
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    label_fr: Mapped[str] = mapped_column(Text, nullable=False)
    label_en: Mapped[str] = mapped_column(Text, nullable=False)
    emoji: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )


class UserInterest(Base):
    __tablename__ = "user_interests"
    __table_args__ = (Index("idx_user_interests_interest", "interest_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    interest_id: Mapped[int] = mapped_column(
        ForeignKey("interests.id"), primary_key=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
