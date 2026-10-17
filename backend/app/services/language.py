"""Outils linguistiques déterministes : traduction avec cache, aide à la lecture japonaise.

Aucune génération de texte : le moteur de traduction est un service externe configuré, et
l'annotation japonaises est produite localement par un tokenizer + un dictionnaire.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import httpx
from app.core.config import get_settings
from app.core.errors import ProviderUnavailable, Unprocessable
from app.models.language import ReadingAid, Translation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ENGINE_VERSION = "fugashi-2/unidic-lite+pykakasi-2"
SUPPORTED_TRANSLATION = {"fr", "en", "es", "de", "it", "pt", "ja", "ko", "ar", "ru", "tr", "nl"}
READING_ENGINES = {"ja"}


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TranslationResult:
    translated: str
    provider: str
    cached: bool


async def _libretranslate(text: str, source: str, target: str) -> str:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=settings.libretranslate_timeout_seconds) as client:
        response = await client.post(
            f"{settings.libretranslate_url.rstrip('/')}/translate",
            json={"q": text, "source": source, "target": target, "format": "text"},
        )
        if response.status_code >= 400:
            raise ProviderUnavailable("LibreTranslate indisponible.")
        return str(response.json()["translatedText"])


async def _deepl(text: str, source: str, target: str) -> str:
    settings = get_settings()
    if settings.deepl_api_key is None:
        raise ProviderUnavailable("DeepL non configuré.")
    async with httpx.AsyncClient(timeout=settings.libretranslate_timeout_seconds) as client:
        response = await client.post(
            "https://api-free.deepl.com/v2/translate",
            headers={"Authorization": f"DeepL-Auth-Key {settings.deepl_api_key.get_secret_value()}"},
            data={"text": text, "source_lang": source.upper(), "target_lang": target.upper()},
        )
        if response.status_code >= 400:
            raise ProviderUnavailable("DeepL indisponible.")
        return str(response.json()["translations"][0]["text"])


PROVIDERS = {"libretranslate": _libretranslate, "deepl": _deepl}


async def translate(
    session: AsyncSession, text: str, source: str, target: str
) -> TranslationResult:
    if source not in SUPPORTED_TRANSLATION or target not in SUPPORTED_TRANSLATION:
        raise Unprocessable(
            "Paire de langues non supportée.",
            errors=[{"field": "target_lang", "code": "unsupported"}],
        )

    digest = text_hash(text)
    cached = (
        await session.execute(
            select(Translation).where(
                Translation.text_hash == digest,
                Translation.source_lang == source,
                Translation.target_lang == target,
            )
        )
    ).scalars().first()
    if cached is not None:
        return TranslationResult(cached.translated, cached.provider, True)

    errors: list[str] = []
    for name, provider in PROVIDERS.items():
        try:
            translated = await provider(text, source, target)
        except (ProviderUnavailable, httpx.HTTPError, KeyError) as exc:
            errors.append(f"{name}:{type(exc).__name__}")
            continue
        session.add(
            Translation(
                text_hash=digest,
                source_lang=source,
                target_lang=target,
                provider=name,
                translated=translated,
            )
        )
        await session.commit()
        return TranslationResult(translated, name, False)

    raise ProviderUnavailable(
        "Aucun moteur de traduction disponible.", errors=[{"field": "provider", "code": "down"}]
    )


def _tagger() -> Any:
    """Tokenizer chargé paresseusement (coût d'import et ~200 Mo de RSS)."""
    global _TAGGER
    if _TAGGER is None:
        import fugashi  # type: ignore[import-untyped]

        _TAGGER = fugashi.Tagger()
    return _TAGGER


_TAGGER: Any = None


def annotate_japanese(text: str) -> list[dict[str, Any]]:
    """Tokens avec lecture kana et romaji ; les offsets sont en points de code."""
    import pykakasi

    tagger = _tagger()
    kks = pykakasi.kakasi()  # type: ignore[no-untyped-call]

    tokens: list[dict[str, Any]] = []
    offset = 0
    for word in tagger(text):
        surface = word.surface
        converted = kks.convert(surface)
        reading = "".join(item["hira"] for item in converted)
        romaji = "".join(item["hepburn"] for item in converted)
        tokens.append(
            {
                "surface": surface,
                "reading": reading,
                "romaji": romaji,
                "start": offset,
                "end": offset + len(surface),
            }
        )
        offset += len(surface)

    if "".join(token["surface"] for token in tokens) != text:
        raise Unprocessable(
            "Annotation impossible : le tokenizer ne restitue pas le texte.",
            errors=[{"field": "text", "code": "tokenizer_mismatch"}],
        )
    return tokens


async def reading_aid(session: AsyncSession, text: str, lang: str = "ja") -> dict[str, Any]:
    if lang not in READING_ENGINES:
        raise Unprocessable(
            "Aide à la lecture indisponible pour cette langue.",
            errors=[{"field": "lang", "code": "unsupported"}],
        )

    digest = text_hash(text)
    cached = (
        await session.execute(
            select(ReadingAid).where(
                ReadingAid.text_hash == digest,
                ReadingAid.lang == lang,
                ReadingAid.engine == ENGINE_VERSION,
            )
        )
    ).scalars().first()
    if cached is not None:
        return {"lang": lang, "engine": ENGINE_VERSION, "tokens": cached.payload, "cached": True}

    tokens = annotate_japanese(text)
    session.add(
        ReadingAid(
            text_hash=digest, lang=lang, engine=ENGINE_VERSION, payload=tokens
        )
    )
    await session.commit()
    return {"lang": lang, "engine": ENGINE_VERSION, "tokens": tokens, "cached": False}
