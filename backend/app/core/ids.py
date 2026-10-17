"""Identifiants UUID v7 (triable par temps) — Python 3.12 n'en fournit pas.

UUID v7 = 48 bits de timestamp Unix en millisecondes, version 7, puis aléa. L'ordre
lexicographique suit donc l'ordre de création, ce qui donne des index B-tree bien plus
amicaux qu'un UUID v4 pour `messages(id)`.

Une garde de monotonie assure que deux appels dans la même milliseconde restent ordonnés
(rand_a sert de compteur), sans jamais réutiliser un identifiant.
"""

from __future__ import annotations

import os
import threading
import time
import uuid

_VERSION = 0x7
_VARIANT = 0b10
_LOCK = threading.Lock()
_last_ms = 0
_counter = 0
_COUNTER_MAX = 0x0FFF


def uuid7() -> uuid.UUID:
    """Renvoie un UUID v7 monotone."""
    global _last_ms, _counter

    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    with _LOCK:
        if ms == _last_ms and _counter < _COUNTER_MAX:
            _counter += 1
        else:
            _last_ms = ms
            _counter = int.from_bytes(os.urandom(2), "big") & 0x03FF

    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
    value = (ms << 80) | (_VERSION << 76) | (_counter << 64) | (_VARIANT << 62) | rand_b
    return uuid.UUID(int=value)
