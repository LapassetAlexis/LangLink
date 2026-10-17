"""Modèles SQLAlchemy — l'import de ce module peuple `Base.metadata`.

Alembic s'appuie sur cet import : tout nouveau modèle doit être ajouté ici, sinon il est
invisible pour l'autogénération de migration.
"""

from app.models.identity import RefreshToken, User
from app.models.language import ReadingAid, Translation
from app.models.matching import Icebreaker, Match, Swipe
from app.models.messaging import Correction, Message, MessageRead
from app.models.profile import Interest, Profile, UserInterest
from app.models.safety import Block, Report

__all__ = [
    "Block",
    "Correction",
    "Icebreaker",
    "Interest",
    "Match",
    "Message",
    "MessageRead",
    "Profile",
    "ReadingAid",
    "RefreshToken",
    "Report",
    "Swipe",
    "Translation",
    "User",
    "UserInterest",
]
