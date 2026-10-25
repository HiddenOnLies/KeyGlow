"""Niveles recientes del sonido del PC, para el efecto de música.

Solo se guardan unas pocas cifras (el volumen de cada banda de frecuencia), en memoria y
durante una fracción de segundo; nunca el sonido. Quien las produce es
``keyglow.app.audio`` (Windows); las pruebas pueden llamar a :func:`set_levels` directamente.
"""

from __future__ import annotations

import threading
import time

BANDS = 16  # de graves (0) a agudos (15)
STALE = 0.5  # niveles más viejos que esto cuentan como silencio

_lock = threading.Lock()
_bands: list[float] = [0.0] * BANDS
_at = 0.0


def set_levels(bands: list[float]) -> None:
    """Niveles 0..1 de cada banda, de graves a agudos."""
    global _bands, _at
    with _lock:
        _bands = [max(0.0, min(1.0, float(b))) for b in bands[:BANDS]] + [0.0] * max(0, BANDS - len(bands))
        _at = time.monotonic()


def levels() -> list[float]:
    """Los últimos niveles, o silencio si hace rato que no llegan."""
    with _lock:
        return list(_bands) if time.monotonic() - _at <= STALE else [0.0] * BANDS


def clear() -> None:
    global _bands, _at
    with _lock:
        _bands, _at = [0.0] * BANDS, 0.0
