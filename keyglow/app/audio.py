"""Escucha lo que suena en el PC para el efecto de música (solo Windows).

Lee la salida de audio predeterminada con WASAPI en modo *loopback* (lo mismo que graban
OBS o Discord al compartir sonido), la divide en bandas de frecuencia y deja el volumen de
cada una en :mod:`keyglow.sound`. No graba nada, no escribe en disco y solo está activo
mientras un perfil en uso tenga una capa de música.

Necesita ``soundcard`` y ``numpy``; sin ellos el efecto simplemente no se mueve.
"""

from __future__ import annotations

import sys
import threading
import time
import warnings

from .. import sound

RATE = 48000
BLOCK = 1024  # ~21 ms por bloque
LOW, HIGH = 40.0, 16000.0  # Hz que se reparten en bandas


def band_levels(block, rate: int = RATE, state: dict | None = None):
    """Volumen 0..1 de cada banda para un bloque de audio (``numpy``, mono o estéreo).

    ``state`` guarda entre bloques el máximo reciente de cada banda (ganancia automática,
    para que funcione igual a volumen bajo o alto) y el suavizado (sube rápido, baja despacio).
    """
    import numpy as np
    state = state if state is not None else {}
    mono = block.mean(axis=1) if block.ndim > 1 else block
    n = len(mono)
    spec = np.abs(np.fft.rfft(mono * np.hanning(n)))
    freqs = np.fft.rfftfreq(n, 1.0 / rate)
    edges = np.geomspace(LOW, HIGH, sound.BANDS + 1)
    raw = np.array([spec[(freqs >= lo) & (freqs < hi)].mean() if ((freqs >= lo) & (freqs < hi)).any() else 0.0
                    for lo, hi in zip(edges[:-1], edges[1:])])
    raw = np.log1p(raw * 10)
    peak = np.maximum(state.get("peak", raw), raw)
    state["peak"] = np.maximum(peak * 0.997, 0.4)  # el máximo baja poco a poco; no amplifica el silencio
    norm = np.clip(raw / state["peak"], 0, 1) ** 1.6  # más contraste entre lo que suena y lo que no
    prev = state.get("smooth", np.zeros_like(norm))
    smooth = np.where(norm > prev, prev + (norm - prev) * 0.65, prev + (norm - prev) * 0.18)
    state["smooth"] = smooth
    return [float(v) for v in smooth]


class AudioMeter:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.error = ""

    @property
    def active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if sys.platform != "win32" or self.active:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="keyglow-audio", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._thread = None
        sound.clear()

    def _run(self) -> None:
        try:
            import numpy  # noqa: F401
            import soundcard as sc
        except ImportError as e:
            self.error = f"Music effects need soundcard and numpy ({e})"
            return
        warnings.simplefilter("ignore")  # soundcard avisa de discontinuidades con cada pausa del audio
        state: dict = {}
        while not self._stop.is_set():
            try:
                speaker = sc.default_speaker()
                mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
                checked = time.monotonic()
                with mic.recorder(samplerate=RATE, channels=2, blocksize=BLOCK) as rec:
                    self.error = ""
                    while not self._stop.is_set():
                        sound.set_levels(band_levels(rec.record(numframes=BLOCK), RATE, state))
                        if time.monotonic() - checked > 5:  # ¿se cambió la salida (auriculares, altavoces)?
                            checked = time.monotonic()
                            if sc.default_speaker().name != speaker.name:
                                break  # se abre la nueva
            except Exception as e:  # noqa: BLE001 - sin salida de audio, dispositivo ocupado...
                self.error = f"Couldn't listen to the PC's sound: {e}"
                sound.clear()
                self._stop.wait(3)
