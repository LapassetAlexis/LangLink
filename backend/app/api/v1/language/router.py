"""Outils d'assistance linguistique : traduction à la demande et aide à la lecture."""

from __future__ import annotations

import uuid

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import NotFound, Unprocessable
from app.services import language as language_service
from app.services import lexicon as lexicon_service
from app.services.messaging import membership
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

router = APIRouter(prefix="/language", tags=["language-tools"])


class TranslateIn(BaseModel):
    text: str | None = Field(default=None, max_length=4000)
    message_id: uuid.UUID | None = None
    source_lang: str | None = Field(default=None, max_length=16)
    target_lang: str | None = Field(default=None, max_length=16)


class ReadingAidIn(BaseModel):
    text: str | None = Field(default=None, max_length=4000)
    message_id: uuid.UUID | None = None
    lang: str = Field(default="ja", max_length=16)


async def _resolve_text(
    session: SessionDep, user_id: uuid.UUID, text_value: str | None, message_id: uuid.UUID | None
) -> tuple[str, str | None, str | None]:
    """Renvoie (texte brut, langue source, langue cible implicite) à partir d'un message."""
    if message_id is None:
        if not text_value:
            raise Unprocessable(
                "Fournir un texte ou un message.",
                errors=[{"field": "text", "code": "required"}],
            )
        return text_value, None, None

    row = (
        await session.execute(
            text(
                "SELECT m.body, m.body_lang, m.match_id FROM messages m WHERE m.id = :mid"
                " AND m.deleted_at IS NULL"
            ),
            {"mid": message_id},
        )
    ).mappings().first()
    if row is None:
        raise NotFound("Message introuvable.")
    await membership(session, row["match_id"], user_id)

    body = row["body"]
    # La traduction porte sur le texte brut, jamais sur les corrections acceptées :
    # on ne propage pas une réécriture dans le cache.
    return body, row["body_lang"], None


@router.post("/translate", summary="Traduire un message ou un texte")
async def translate(payload: TranslateIn, user: CurrentUser, session: SessionDep) -> dict[str, object]:
    body, source_lang, _ = await _resolve_text(session, user.id, payload.text, payload.message_id)
    source = payload.source_lang or source_lang or "fr"
    target = payload.target_lang
    if not target:
        row = (
            await session.execute(
                text("SELECT native_language FROM profiles WHERE user_id = :uid"), {"uid": user.id}
            )
        ).scalar_one_or_none()
        target = row or "fr"

    result = await language_service.translate(session, body, source, target)
    return {
        "translated": result.translated,
        "provider": result.provider,
        "cached": result.cached,
        "source_lang": source,
        "target_lang": target,
    }


@router.post("/reading-aid", summary="Annotation furigana/romaji (japonais)")
async def reading_aid(payload: ReadingAidIn, user: CurrentUser, session: SessionDep) -> dict[str, object]:
    body, _, _ = await _resolve_text(session, user.id, payload.text, payload.message_id)
    return await language_service.reading_aid(session, body, payload.lang)


class LexiconIn(BaseModel):
    text: str = Field(min_length=1, max_length=64)
    lang: str = Field(default="fr", max_length=16)


@router.post("/lexicon", summary="Sens possibles d'un mot (Wiktionnaire)")
async def lexicon(payload: LexiconIn, user: CurrentUser, session: SessionDep) -> dict[str, object]:
    """Aide au mot : plusieurs sens, avec catégorie grammaticale.

    Pour le japonais, la lecture kana et le romaji sont ajoutés via le tokenizer local —
    aucune information supplémentaire n'est demandée à la source.
    """
    word = payload.text.strip()
    senses = await lexicon_service.lookup(word)

    reading = None
    if payload.lang == "ja":
        try:
            tokens = language_service.annotate_japanese(word)
            reading = {
                "kana": "".join(token["reading"] for token in tokens),
                "romaji": "".join(token["romaji"] for token in tokens),
            }
        except Exception:  # noqa: BLE001 - l'annotation ne doit pas bloquer l'aide
            reading = None

    return {
        "word": word,
        "lang": payload.lang,
        "senses": senses,
        "source": "wiktionnaire" if senses else "aucune",
        "reading": reading,
    }


@router.get("/capabilities", summary="Langues supportées par chaque outil")
async def capabilities() -> dict[str, object]:
    return {
        "translation": sorted(language_service.SUPPORTED_TRANSLATION),
        "reading_aid": sorted(language_service.READING_ENGINES),
    }
