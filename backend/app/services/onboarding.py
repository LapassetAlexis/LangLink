"""État d'avancement de l'enrôlement (partagé par /auth/me et /onboarding/*)."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.profile import Profile

CECRL = ("A1", "A2", "B1", "B2", "C1", "C2")
MIN_INTERESTS = 3
MAX_INTERESTS = 12


@dataclass(frozen=True)
class OnboardingState:
    step: int
    discoverable: bool
    missing: list[str]

    def as_dict(self) -> dict[str, object]:
        return {"step": self.step, "discoverable": self.discoverable, "missing": self.missing}


def missing_fields(profile: Profile, interest_count: int) -> list[str]:
    """Liste ordonnée des prérequis manquants pour être découvrable."""
    missing: list[str] = []
    if not profile.native_language or not profile.target_language or not profile.target_level:
        missing.append("languages")
    if interest_count < MIN_INTERESTS:
        missing.append("interests")
    return missing


def state_of(profile: Profile, interest_count: int) -> OnboardingState:
    missing = missing_fields(profile, interest_count)
    step = 1
    if profile.native_language and profile.target_language and profile.target_level:
        step = 2
    if interest_count >= MIN_INTERESTS:
        step = 3
    return OnboardingState(step=step, discoverable=profile.discoverable, missing=missing)
