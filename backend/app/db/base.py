"""Base déclarative SQLAlchemy 2 et conventions de nommage.

Les conventions de nommage sont indispensables : sans elles, une contrainte anonyme reçoit
un nom généré par PostgreSQL, et `alembic downgrade` ne sait plus la supprimer.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from app.core.ids import uuid7
from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base commune à tous les modèles."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    def as_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class UUIDPrimaryKeyMixin:
    """Clé primaire UUID v7 générée côté application."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)


class TimestampMixin:
    """Horodatages gérés par la base (fuseau inclus)."""

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
