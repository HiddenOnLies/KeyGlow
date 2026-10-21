"""Pulsaciones recientes de teclas, para los efectos reactivos.

Solo se guarda qué tecla se pulsó y cuándo, durante unos segundos y en memoria; nada
se escribe en disco ni sale del PC. Quien produce las pulsaciones es
``keyglow.app.keyhook`` (Windows); las pruebas pueden llamar a :func:`press` directamente.
"""

from __future__ import annotations

import threading
import time
from collections import deque

_events: deque[tuple[str, float]] = deque(maxlen=128)
_lock = threading.Lock()


def press(key_id: str, when: float | None = None) -> None:
    with _lock:
        _events.append((key_id, time.monotonic() if when is None else when))


def recent(window: float) -> list[tuple[str, float]]:
    """Pulsaciones de los últimos ``window`` segundos como ``(tecla, antigüedad)``."""
    now = time.monotonic()
    with _lock:
        return [(k, now - t) for k, t in _events if 0 <= now - t <= window]


def clear() -> None:
    with _lock:
        _events.clear()
