"""Schémas Pydantic de l'identité."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

MIN_PW_LEN = 10


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PW_LEN, max_length=128)
    display_name: str | None = Field(default=None, min_length=2, max_length=40)
    locale: str = Field(default="fr", max_length=8)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    status: str
    email_verified: bool


class OnboardingOut(BaseModel):
    step: int
    discoverable: bool
    missing: list[str]


class MeOut(BaseModel):
    user: UserOut
    onboarding: OnboardingOut


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ResetRequestIn(BaseModel):
    email: EmailStr


class ResetConfirmIn(BaseModel):
    token: str = Field(min_length=16)
    new_password: str = Field(min_length=MIN_PW_LEN, max_length=128)


class VerifyEmailIn(BaseModel):
    token: str = Field(min_length=16)
