"""Schémas de l'enrôlement et du profil."""

from __future__ import annotations

import uuid
from typing import Literal

from app.services.onboarding import CECRL, MAX_INTERESTS, MIN_INTERESTS
from pydantic import BaseModel, Field


class LanguagesIn(BaseModel):
    native_language: str = Field(min_length=2, max_length=16)
    target_language: str = Field(min_length=2, max_length=16)
    target_level: str = Field(pattern="^(A1|A2|B1|B2|C1|C2)$")


class InterestsIn(BaseModel):
    interest_ids: list[int] = Field(min_length=1, max_length=MAX_INTERESTS)


class ProfileIn(BaseModel):
    display_name: str = Field(min_length=2, max_length=40)
    bio: str | None = Field(default=None, max_length=600)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)


class AvailabilityIn(BaseModel):
    discoverable: bool


class ProfileOut(BaseModel):
    user_id: uuid.UUID
    display_name: str
    bio: str | None
    birth_year: int | None
    avatar_key: str | None
    native_language: str | None
    target_language: str | None
    target_level: str | None
    discoverable: bool


class StateOut(BaseModel):
    step: int
    discoverable: bool
    missing: list[str]
    native_language: str | None = None
    target_language: str | None = None
    target_level: str | None = None
    interest_ids: list[int] = []
    display_name: str | None = None
    bio: str | None = None
    has_avatar: bool = False


class InterestOut(BaseModel):
    id: int
    slug: str
    label: str
    label_en: str
    emoji: str
    category: str
    sort_order: int


class InterestGroupOut(BaseModel):
    category: str
    interests: list[InterestOut]


class CompleteOut(BaseModel):
    discoverable: bool
    step: int


SUPPORTED_LEVELS = CECRL
MIN = MIN_INTERESTS


class PreferencesIn(BaseModel):
    """Préférences d'affichage. Clés inconnues refusées : pas de jsonb fourre-tout."""

    model_config = {"extra": "forbid"}

    furigana_auto: bool = False
    word_mode_default: bool = False
    text_size: Literal["normal", "large"] = "normal"
    density: Literal["confort", "compact"] = "confort"
    motion: Literal["system", "reduce", "normal"] = "system"
    hide_correspondence_tip: bool = False
