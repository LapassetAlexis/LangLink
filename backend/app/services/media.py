"""Pipeline média : validation par signature, recompression WebP, clé opaque."""

from __future__ import annotations

import io
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import PayloadTooLarge, UnsupportedMedia
from PIL import Image, ImageOps

SIGNATURES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"RIFF": "webp",  # vérifié plus finement ci-dessous (RIFF....WEBP)
}
AVATAR_SIZE = 512
QUALITY = 82


def _detect(data: bytes) -> str:
    for signature, kind in SIGNATURES.items():
        if data.startswith(signature):
            if kind == "webp" and data[8:12] != b"WEBP":
                continue
            return kind
    raise UnsupportedMedia(
        "Format non supporté (JPEG, PNG ou WebP attendu).",
        errors=[{"field": "avatar", "code": "unsupported_media"}],
    )


def store_avatar(data: bytes, media_root: Path | None = None) -> str:
    """Redimensionne, supprime les métadonnées et écrit le fichier. Renvoie la clé."""
    settings = get_settings()
    if len(data) > settings.media_max_bytes:
        raise PayloadTooLarge(
            f"Image trop volumineuse (max {settings.media_max_bytes // (1024 * 1024)} Mo).",
            errors=[{"field": "avatar", "code": "too_large"}],
        )

    _detect(data)  # lève 415 si ce n'est pas une image acceptée

    try:
        with Image.open(io.BytesIO(data)) as source:
            upright: Image.Image = ImageOps.exif_transpose(source)
            rgb: Image.Image = upright.convert("RGB")
            side = min(rgb.size)
            left = (rgb.width - side) // 2
            top = (rgb.height - side) // 2
            squared: Image.Image = rgb.crop((left, top, left + side, top + side))
            resized: Image.Image = squared.resize(
                (AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS
            )
            output = io.BytesIO()
            resized.save(output, format="WEBP", quality=QUALITY, method=6)
    except UnsupportedMedia:
        raise
    except Exception as exc:  # noqa: BLE001 - image corrompue
        raise UnsupportedMedia(
            "Image illisible.",
            errors=[{"field": "avatar", "code": "corrupt"}],
        ) from exc

    key = f"{uuid.uuid4().hex}.webp"
    root = media_root or settings.media_root
    root.mkdir(parents=True, exist_ok=True)
    (root / key).write_bytes(output.getvalue())
    return key


def avatar_path(key: str) -> Path:
    """Chemin disque d'un avatar, en refusant toute traversée de répertoire."""
    if "/" in key or ".." in key or not key.endswith(".webp"):
        raise UnsupportedMedia("Clé de média invalide.")
    root = get_settings().media_root
    return root / key
