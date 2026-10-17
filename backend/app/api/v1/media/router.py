"""Service des images (avatars). Clés opaques et immuables."""

from __future__ import annotations

from app.core.errors import NotFound
from app.services import media as media_service
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["media"])


@router.get("/media/{key}", summary="Image de profil")
async def get_media(key: str) -> FileResponse:
    path = media_service.avatar_path(key)
    if not path.is_file():
        raise NotFound("Média introuvable.")
    return FileResponse(
        path,
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
