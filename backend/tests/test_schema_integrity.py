"""REQ-PLT-01 — l'intégrité est portée par la base, pas seulement par l'application.

Deux scénarios de la spec : double swipe concurrent (une seule insertion gagne) et match
dupliqué (une seule ligne). On y ajoute les deux CHECK qui rendent ces règles infalsifiables.
"""

from __future__ import annotations

import threading
import uuid
from typing import Any

import pytest
from app.core.ids import uuid7
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

INSERT_SWIPE = (
    "INSERT INTO swipes (id, swiper_id, target_id, direction) "
    "VALUES (:id, :swiper, :target, 'like')"
)
INSERT_MATCH = (
    "INSERT INTO matches (id, user_a_id, user_b_id, affinity_score) "
    "VALUES (:id, :first, :second, :score)"
)


def _user(engine: Engine, email: str) -> uuid.UUID:
    user_id = uuid7()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash) "
                "VALUES (:id, :email, 'argon2-placeholder')"
            ),
            {"id": user_id, "email": email},
        )
    return user_id


def _expect_integrity_error(
    engine: Engine, sql: str, params: dict[str, Any], match: str
) -> None:
    """Exécute une insertion en attendant une violation de contrainte nommée."""
    with pytest.raises(IntegrityError, match=match), engine.begin() as connection:
        connection.execute(text(sql), params)


def test_self_swipe_is_rejected(clean_engine: Engine) -> None:
    """Un utilisateur ne peut pas se liker lui-même (BR-01)."""
    user_id = _user(clean_engine, "self@example.org")

    _expect_integrity_error(
        clean_engine,
        INSERT_SWIPE,
        {"id": uuid7(), "swiper": user_id, "target": user_id},
        "no_self_swipe",
    )


def test_match_pair_order_is_canonical(clean_engine: Engine) -> None:
    """La paire est stockée dans un ordre canonique, sinon l'unicité ne protège rien."""
    first = _user(clean_engine, "low@example.org")
    second = _user(clean_engine, "safe@example.org")

    # Ordre inversé : a > b, ce que la contrainte canonique interdit
    a, b = sorted((first, second), reverse=True)

    _expect_integrity_error(
        clean_engine,
        INSERT_MATCH,
        {"id": uuid7(), "first": a, "second": b, "score": 50},
        "canonical_pair_order",
    )


def test_duplicate_match_is_rejected(clean_engine: Engine) -> None:
    """Deux inserts du même couple : un seul passe (contrainte d'unicité)."""
    a, b = sorted((_user(clean_engine, "m1@example.org"), _user(clean_engine, "m2@example.org")))

    with clean_engine.begin() as connection:
        connection.execute(
            text(INSERT_MATCH), {"id": uuid7(), "first": a, "second": b, "score": 63}
        )

    _expect_integrity_error(
        clean_engine,
        INSERT_MATCH,
        {"id": uuid7(), "first": a, "second": b, "score": 63},
        "uq_matches_pair",
    )


def test_concurrent_swipe_inserts_only_one_wins(clean_engine: Engine) -> None:
    """Deux likes simultanés du même couple : une insertion réussit, l'autre échoue."""
    swiper = _user(clean_engine, "swiper@example.org")
    target = _user(clean_engine, "target@example.org")

    barrier = threading.Barrier(2)
    results: list[str] = []
    lock = threading.Lock()

    def attempt() -> None:
        try:
            barrier.wait(timeout=10)
            with clean_engine.begin() as connection:
                connection.execute(
                    text(INSERT_SWIPE),
                    {"id": uuid7(), "swiper": swiper, "target": target},
                )
            with lock:
                results.append("ok")
        except IntegrityError:
            with lock:
                results.append("integrity")

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)

    assert sorted(results) == ["integrity", "ok"], results
    with clean_engine.connect() as connection:
        count = connection.execute(text("SELECT count(*) FROM swipes")).scalar_one()
    assert count == 1
