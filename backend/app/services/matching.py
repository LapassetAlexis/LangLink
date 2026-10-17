"""Moteur de matching : score d'affinité, feed réciproque, création de match."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.core.errors import Conflict, Forbidden, Unprocessable
from app.models.matching import Icebreaker, Match
from app.services import icebreakers as icebreakers_service
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

LEVELS = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


def affinity_score(
    candidate_interests: list[int],
    viewer_interests: list[int],
    candidate_level: str,
    viewer_level: str,
) -> int:
    """Formule normative de REQ-MAT-02 (0–100), identique à celle du SQL du feed."""
    common = len(set(candidate_interests) & set(viewer_interests))
    n_candidate = len(candidate_interests)
    n_viewer = len(viewer_interests)
    if n_candidate == 0 or n_viewer == 0:
        return 0
    overlap = common / max(min(n_candidate, n_viewer), 1)
    jaccard = common / max(n_candidate + n_viewer - common, 1)
    level_fit = 1 - abs(LEVELS[candidate_level] - LEVELS[viewer_level]) / 5
    return round(100 * (0.5 * overlap + 0.3 * jaccard + 0.2 * level_fit))


FEED_SQL = """
WITH me AS (
    SELECT u.id AS uid, p.native_language AS nat, p.target_language AS tgt,
           CASE p.target_level WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 WHEN 'B1' THEN 3
                               WHEN 'B2' THEN 4 WHEN 'C1' THEN 5 WHEN 'C2' THEN 6 END AS lvl,
           ARRAY(SELECT ui.interest_id FROM user_interests ui WHERE ui.user_id = u.id) AS ints
    FROM users u JOIN profiles p ON p.user_id = u.id
    WHERE u.id = :uid
), cand AS (
    SELECT p.user_id, p.display_name, p.birth_year, p.bio, p.avatar_key,
           p.native_language, p.target_language, p.target_level,
           CASE p.target_level WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 WHEN 'B1' THEN 3
                               WHEN 'B2' THEN 4 WHEN 'C1' THEN 5 WHEN 'C2' THEN 6 END AS lvl,
           ARRAY(SELECT ui.interest_id FROM user_interests ui WHERE ui.user_id = p.user_id) AS ints
    FROM profiles p CROSS JOIN me
    WHERE p.discoverable
      AND p.user_id <> me.uid
      AND p.native_language = me.tgt
      AND p.target_language = me.nat
      AND NOT EXISTS (SELECT 1 FROM swipes s WHERE s.swiper_id = me.uid AND s.target_id = p.user_id)
      AND NOT EXISTS (SELECT 1 FROM blocks b
                      WHERE (b.blocker_id = me.uid AND b.blocked_id = p.user_id)
                         OR (b.blocker_id = p.user_id AND b.blocked_id = me.uid))
      AND NOT EXISTS (SELECT 1 FROM matches m
                      WHERE m.user_a_id = LEAST(me.uid, p.user_id)
                        AND m.user_b_id = GREATEST(me.uid, p.user_id))
), scored AS (
    SELECT c.*, (SELECT count(*) FROM unnest(c.ints) i WHERE i = ANY(me.ints)) AS common,
           cardinality(c.ints) AS n_cand, cardinality(me.ints) AS n_me,
           (1 - abs(c.lvl - me.lvl) / 5.0) AS level_fit,
           (SELECT ARRAY(SELECT i FROM unnest(c.ints) i WHERE i = ANY(me.ints))) AS common_ids
    FROM cand c CROSS JOIN me
), final AS (
    SELECT s.*, round(100 * (
               0.5 * (s.common::numeric / GREATEST(LEAST(s.n_cand, s.n_me), 1))
             + 0.3 * (s.common::numeric / GREATEST(s.n_cand + s.n_me - s.common, 1))
             + 0.2 * s.level_fit))::int AS score
    FROM scored s
)
SELECT user_id, display_name, birth_year, bio, avatar_key, native_language,
       target_language, target_level, score, common_ids
FROM final
ORDER BY score DESC, md5(user_id::text || :day_seed)
LIMIT :limit OFFSET :offset
"""


@dataclass(frozen=True)
class Candidate:
    user_id: uuid.UUID
    display_name: str
    birth_year: int | None
    bio: str | None
    avatar_key: str | None
    native_language: str
    target_language: str
    target_level: str
    score: int
    common_ids: list[int]


async def feed(
    session: AsyncSession, viewer_id: uuid.UUID, *, limit: int, offset: int, day_seed: str
) -> list[Candidate]:
    rows = (
        await session.execute(
            text(FEED_SQL),
            {"uid": viewer_id, "limit": limit, "offset": offset, "day_seed": day_seed},
        )
    ).mappings()
    return [
        Candidate(
            user_id=row["user_id"],
            display_name=row["display_name"],
            birth_year=row["birth_year"],
            bio=row["bio"],
            avatar_key=row["avatar_key"],
            native_language=row["native_language"],
            target_language=row["target_language"],
            target_level=row["target_level"],
            score=row["score"],
            common_ids=list(row["common_ids"] or []),
        )
        for row in rows
    ]


async def swipes_today(session: AsyncSession, user_id: uuid.UUID) -> int:
    return int(
        await session.scalar(
            text(
                "SELECT count(*) FROM swipes WHERE swiper_id = :uid "
                "AND created_at >= date_trunc('day', now())"
            ),
            {"uid": user_id},
        )
        or 0
    )


async def record_swipe(
    session: AsyncSession, swiper_id: uuid.UUID, target_id: uuid.UUID, direction: str
) -> Match | None:
    """Enregistre un swipe et crée le match s'il y a réciprocité. Atomique."""
    if swiper_id == target_id:
        raise Unprocessable(
            "Impossible de se liker soi-même.",
            errors=[{"field": "target_id", "code": "self_swipe"}],
        )
    if direction not in ("like", "pass"):
        raise Unprocessable(
            "Direction invalide.",
            errors=[{"field": "direction", "code": "invalid"}],
        )

    blocked = await session.scalar(
        text(
            "SELECT 1 FROM blocks WHERE (blocker_id = :a AND blocked_id = :b) "
            "OR (blocker_id = :b AND blocked_id = :a) LIMIT 1"
        ),
        {"a": swiper_id, "b": target_id},
    )
    if blocked:
        raise Forbidden("Interaction impossible avec ce profil.")

    existing = await session.scalar(
        text("SELECT direction FROM swipes WHERE swiper_id = :a AND target_id = :b"),
        {"a": swiper_id, "b": target_id},
    )
    if existing is not None:
        raise Conflict("Swipe déjà enregistré.")

    await session.execute(
        text(
            "INSERT INTO swipes (id, swiper_id, target_id, direction, created_at) "
            "VALUES (gen_random_uuid(), :a, :b, :d, now())"
        ),
        {"a": swiper_id, "b": target_id, "d": direction},
    )

    if direction != "like":
        await session.commit()
        return None

    reciprocal = await session.scalar(
        text(
            "SELECT 1 FROM swipes WHERE swiper_id = :b AND target_id = :a "
            "AND direction = 'like'"
        ),
        {"a": swiper_id, "b": target_id},
    )
    if not reciprocal:
        await session.commit()
        return None

    first, second = sorted((swiper_id, target_id))
    row = (
        await session.execute(
            text(
                "INSERT INTO matches (id, user_a_id, user_b_id, status, affinity_score, created_at) "
                "VALUES (gen_random_uuid(), :a, :b, 'active', :score, now()) "
                "ON CONFLICT (user_a_id, user_b_id) DO UPDATE SET id = matches.id "
                "RETURNING id"
            ),
            {"a": first, "b": second, "score": await _score_between(session, first, second)},
        )
    ).scalar_one()

    match = await session.get(Match, row)
    if match is not None:
        await _seed_icebreakers(session, match.id, first, second)
    await session.commit()
    return match


async def _score_between(session: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> int:
    rows = (
        await session.execute(
            text(
                "SELECT p.user_id, p.target_level,"
                " ARRAY(SELECT ui.interest_id FROM user_interests ui WHERE ui.user_id = p.user_id)"
                " AS ints FROM profiles p WHERE p.user_id IN (:a, :b)"
            ),
            {"a": a, "b": b},
        )
    ).mappings().all()
    data = {row["user_id"]: row for row in rows}
    left, right = data[a], data[b]
    return affinity_score(list(left["ints"]), list(right["ints"]), left["target_level"],
                          right["target_level"])


async def _seed_icebreakers(
    session: AsyncSession, match_id: uuid.UUID, a: uuid.UUID, b: uuid.UUID
) -> None:
    rows = (
        await session.execute(
            text(
                "SELECT i.slug, i.category FROM interests i WHERE i.id IN ("
                "  SELECT interest_id FROM user_interests WHERE user_id = :a"
                "  INTERSECT"
                "  SELECT interest_id FROM user_interests WHERE user_id = :b)"
            ),
            {"a": a, "b": b},
        )
    ).all()
    common = [(row[0], row[1]) for row in rows]

    for entry in icebreakers_service.select(match_id, common):
        session.add(
            Icebreaker(
                match_id=match_id,
                position=entry["position"],
                interest_slug=entry["interest_slug"],
                question_fr=entry["question_fr"],
                question_en=entry["question_en"],
            )
        )


async def canonical_pair(a: uuid.UUID, b: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    return (a, b) if a < b else (b, a)


async def match_for_user(session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
    row = (
        await session.execute(
            text(
                "SELECT m.*, CASE WHEN m.user_a_id = :uid THEN m.user_b_id ELSE m.user_a_id END"
                " AS other_id FROM matches m WHERE m.id = :mid"
                " AND (m.user_a_id = :uid OR m.user_b_id = :uid)"
            ),
            {"mid": match_id, "uid": user_id},
        )
    ).mappings().first()
    if row is None:
        from app.core.errors import NotFound

        raise NotFound("Match introuvable.")
    return dict(row)
