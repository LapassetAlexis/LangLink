"""Référentiel des intérêts : amorçage idempotent et lecture groupée."""

from __future__ import annotations

from collections import OrderedDict

from app.data.interests import CATALOG, CATEGORIES
from app.models.profile import Interest
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_catalog(session: AsyncSession) -> int:
    """Insère le catalogue s'il est absent. Idempotent (ON CONFLICT DO NOTHING)."""
    count = await session.scalar(select(func.count()).select_from(Interest))
    if count and count >= len(CATALOG):
        return 0

    rows = [
        {
            "id": entry[0],
            "slug": entry[1],
            "label_fr": entry[2],
            "label_en": entry[3],
            "emoji": entry[4],
            "category": entry[5],
            "sort_order": entry[6],
            "active": True,
        }
        for entry in CATALOG
    ]
    statement = insert(Interest).values(rows).on_conflict_do_nothing(index_elements=["id"])
    await session.execute(statement)
    await session.commit()
    return len(rows)


async def grouped_catalog(session: AsyncSession) -> list[dict[str, object]]:
    """Catalogue actif, groupé par catégorie dans l'ordre du référentiel."""
    rows = (
        await session.execute(
            select(Interest).where(Interest.active.is_(True)).order_by(Interest.id)
        )
    ).scalars().all()

    groups: OrderedDict[str, list[dict[str, object]]] = OrderedDict((c, []) for c in CATEGORIES)
    for interest in rows:
        groups.setdefault(interest.category, []).append(
            {
                "id": interest.id,
                "slug": interest.slug,
                "label": interest.label_fr,
                "label_en": interest.label_en,
                "emoji": interest.emoji,
                "category": interest.category,
                "sort_order": interest.sort_order,
            }
        )

    return [
        {"category": category, "interests": sorted(items, key=lambda item: int(str(item["sort_order"])))}
        for category, items in groups.items()
        if items
    ]
