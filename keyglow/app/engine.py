"""Motor de iluminación de la aplicación.

Mantiene un hilo que pinta el perfil activo en el teclado vía OpenRGB y permite
cambiar de perfil en caliente (el editor manda cada cambio y se ve al instante).
Si OpenRGB se cierra o el teclado se desconecta, reintenta solo.
"""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict

from .. import color as C
from .. import onboard
from ..effects import has_reactive
from ..layout import Layout, load_layout
from ..profile import Profile, Renderer
from ..retarget import Report, retarget
from .keyhook import KeyHook, caps_lock_on

DEFAULT_LAYOUT = "alloy_origins_65"
AUTO = "auto"  # distribución detectada a partir de lo que informa OpenRGB
RECONNECT_EVERY = 3.0
CAPS_KEY = "CAPSLOCK"
PEEK_TIMEOUT = 12.0  # una vista previa sin renovar se apaga sola (p. ej. si se cierra la ventana)


def prepare(data: dict, layout: Layout) -> tuple[Profile, Report]:
    """Valida un perfil (dict) y lo adapta al teclado ``layout``."""
    profile = Profile.from_dict(data)
    source = None
    if profile.designed_for and profile.designed_for != layout.name:
        try:
            source = load_layout(profile.designed_for)
        except (ValueError, OSError):
            source = None
    return retarget(profile, layout, source)


class LightEngine:
    def __init__(self, layout_name: str = DEFAULT_LAYOUT, host: str = "127.0.0.1",
                 port: int = 6742, device: str = "", cached_layout: dict | None = None,
                 on_layout=None):
        self.layout_mode = layout_name
        if layout_name != AUTO:
            try:
                self.layout = load_layout(layout_name)
            except ValueError:  # p. ej. una distribución del workshop que ya no existe
                self.layout_mode = AUTO
        if self.layout_mode == AUTO:
            # hasta conectar se usa la última distribución detectada (o la predeterminada)
            self.layout = Layout.from_dict(cached_layout) if cached_layout else load_layout(DEFAULT_LAYOUT)
        self.layout_rev = 0
        self.on_layout = on_layout  # se llama con la distribución nueva para recordarla
        self.host, self.port, self.device_match = host, port, device
        self.brightness = 1.0
        self.fps = 30.0
        # Bloq Mayús: "auto" = encender la tecla si el teclado no tiene piloto propio
        # (o no se sabe), "on" = siempre, "off" = nunca
        self.caps_lock = "auto"
        self.caps_color = (255, 255, 255)
        self.caps_state = caps_lock_on
        self._lock = threading.RLock()
        self._renderer: Renderer | None = None
        self._base_renderer: Renderer | None = None
        self.override: dict | None = None  # perfil temporal de un juego
        self._peek: tuple[Renderer, float] | None = None  # vista previa al pasar el ratón
        self._profile: dict | None = None
        self._t0 = time.monotonic()
        self._kb = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_attempt = -RECONNECT_EVERY
        self.error = ""
        self._previews: OrderedDict[str, tuple[Renderer, list[str]]] = OrderedDict()
        self._plock = threading.Lock()
        # detección de pulsaciones: solo mientras un perfil en uso tenga capa reactiva
        self.keyhook = KeyHook()
        self._reactive_live = False
        self._reactive_preview_until = 0.0

    # --- conexión ----------------------------------------------------------
    def _connect(self):
        from ..backends.openrgb import OpenRGBKeyboard
        self._last_attempt = time.monotonic()
        try:
            self._kb = OpenRGBKeyboard(self.host, self.port, self.device_match)
            self.error = ""
        except RuntimeError as e:
            self._kb = None
            self.error = str(e)
        if self._kb is not None and self.layout_mode == AUTO:
            try:
                self._set_layout(self._kb.layout())
            except ValueError:
                pass  # teclado sin teclas reconocibles: se queda la distribución actual
        return self._kb

    # --- distribución -----------------------------------------------------
    def _set_layout(self, layout: Layout) -> None:
        if layout.to_dict() == self.layout.to_dict():
            return
        with self._lock:
            self.layout = layout
            self.layout_rev += 1
            with self._plock:
                self._previews.clear()
            self._peek = None
            if self._profile is not None:
                profile, _ = prepare(self._profile, layout)
                self._renderer = self._base_renderer = Renderer(profile, layout)
                self.override = None  # el vigilante de juegos lo vuelve a poner
        if self.on_layout:
            self.on_layout(layout)

    def refresh_layout(self) -> None:
        """Vuelve a elegir la distribución (p. ej. al llegar distribuciones nuevas del workshop)."""
        with self._lock:
            if self.layout_mode == AUTO and self._kb is not None:
                try:
                    self._set_layout(self._kb.layout())
                except ValueError:
                    pass

    def set_layout_mode(self, mode: str, device: str | None = None) -> None:
        """Cambia la distribución: ``"auto"`` (la que informa OpenRGB) o un nombre/ruta."""
        changed_device = device is not None and device != self.device_match
        if changed_device:
            self.device_match = device
        if mode == self.layout_mode and not changed_device:
            return
        self.layout_mode = mode
        if mode != AUTO:
            self._set_layout(load_layout(mode))
        with self._lock:
            if changed_device:
                self._kb = None
                self._connect()
            elif mode == AUTO and self._kb is not None:
                try:
                    self._set_layout(self._kb.layout())
                except ValueError:
                    pass

    def connect(self) -> bool:
        with self._lock:
            if self._kb is None:
                self._connect()
            return self._kb is not None

    def maybe_reconnect(self) -> None:
        """Si no hay conexión, la reintenta en segundo plano (como mucho cada pocos segundos)."""
        if self._kb is not None or time.monotonic() - self._last_attempt < RECONNECT_EVERY:
            return
        self._last_attempt = time.monotonic()
        threading.Thread(target=self.connect, name="keyglow-conectar", daemon=True).start()

    @property
    def device_name(self) -> str:
        return self._kb.name if self._kb else ""

    # --- reproducción ------------------------------------------------------
    def apply(self, data: dict) -> list[str]:
        """Pone ``data`` como perfil activo. Devuelve el informe de adaptación."""
        profile, report = prepare(data, self.layout)
        renderer = Renderer(profile, self.layout)
        renderer.frame(0)  # falla aquí, no dentro del hilo, si algo está mal
        with self._lock:
            self._renderer = renderer
            self._profile = data
            self._base_renderer = renderer
            self.override = None
            self._reactive_live = has_reactive(data.get("layers", []))
            if self._kb is None:
                self._connect()
            if self._thread is None or not self._thread.is_alive():
                self._stop.clear()
                self._t0 = time.monotonic()
                self._thread = threading.Thread(target=self._loop, name="keyglow-luces",
                                                daemon=True)
                self._thread.start()
        self.housekeeping()
        return report.lines() if (report.dropped or report.unknown or report.filled) else []

    def apply_override(self, data: dict, reason: str) -> None:
        """Muestra ``data`` temporalmente (p. ej. mientras un juego está en primer plano)
        sin olvidar el perfil normal, que vuelve con :meth:`clear_override`."""
        profile, _ = prepare(data, self.layout)
        renderer = Renderer(profile, self.layout)
        renderer.frame(0)
        with self._lock:
            if not self.running:
                return
            self._renderer = renderer
            self.override = {"reason": reason, "profile": data.get("name", ""),
                             "reactive": has_reactive(data.get("layers", []))}
        self.housekeeping()

    def peek(self, data: dict | None) -> None:
        """Muestra ``data`` un momento en el teclado sin cambiar el perfil activo (al pasar el
        ratón por la biblioteca). ``None`` vuelve al perfil activo. Caduca sola si no se renueva."""
        if data is None:
            self._peek = None
            return
        profile, _ = prepare(data, self.layout)
        renderer = Renderer(profile, self.layout)
        renderer.frame(0)
        with self._lock:
            self._peek = (renderer, time.monotonic() + PEEK_TIMEOUT)
        if has_reactive(data.get("layers", [])):
            self._reactive_preview_until = time.monotonic() + PEEK_TIMEOUT
            self.housekeeping()

    @property
    def peeking(self) -> bool:
        peek = self._peek
        return peek is not None and time.monotonic() < peek[1]

    def housekeeping(self) -> None:
        """Enciende o apaga la detección de pulsaciones según haga falta."""
        override_reactive = bool(self.override and self.override.get("reactive"))
        need = (self.running and (override_reactive or (self._reactive_live and not self.override)))             or time.monotonic() < self._reactive_preview_until
        if need and not self.keyhook.active:
            self.keyhook.start()
        elif not need and self.keyhook.active:
            self.keyhook.stop()

    def clear_override(self) -> None:
        with self._lock:
            if self.override is not None and self._base_renderer is not None:
                self._renderer = self._base_renderer
            self.override = None

    def stop(self) -> None:
        """Detiene la animación (el teclado conserva el último fotograma)."""
        self._stop.set()
        t = self._thread
        if t is not None:
            t.join(timeout=2)
        with self._lock:
            self._thread = None
            self._renderer = None
            self._base_renderer = None
            self._profile = None
            self.override = None
            self._peek = None
            self._reactive_live = False
        self.housekeeping()

    def off(self) -> None:
        """Detiene la animación y apaga todas las teclas."""
        self.stop()
        with self._lock:
            if self._kb is None:
                self._connect()
            if self._kb is not None:
                try:
                    self._kb.write({})
                except Exception as e:  # noqa: BLE001 - cualquier fallo de red/USB
                    self._kb = None
                    self.error = f"Lost the connection to OpenRGB: {e}"

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _loop(self) -> None:
        period = 1.0 / max(self.fps, 1.0)
        while not self._stop.is_set():
            start = time.monotonic()
            with self._lock:
                renderer, kb = self._renderer, self._kb
                if self._peek is not None:
                    if start < self._peek[1]:
                        renderer = self._peek[0]
                    else:
                        self._peek = None
                if kb is None and start - self._last_attempt > RECONNECT_EVERY:
                    kb = self._connect()
            if renderer is not None and kb is not None:
                frame = renderer.frame(start - self._t0)
                if self.brightness < 0.999:
                    frame = {k: C.to_bytes(C.scale(tuple(v / 255 for v in c), self.brightness))
                             for k, c in frame.items()}
                frame = self.with_caps_lock(frame)
                try:
                    kb.write(frame)
                except Exception as e:  # noqa: BLE001
                    with self._lock:
                        self._kb = None
                        self.error = f"Lost the connection to OpenRGB: {e}"
            self._stop.wait(max(0.0, period - (time.monotonic() - start)))

    # --- Bloq Mayús -----------------------------------------------------------
    def caps_light(self) -> bool:
        """Si KeyGlow debe hacer de piloto de Bloq Mayús en este teclado."""
        if self.caps_lock == "off" or CAPS_KEY not in self.layout:
            return False
        return self.caps_lock == "on" or self.layout.caps_indicator is not True

    def with_caps_lock(self, frame: dict) -> dict:
        """Pinta la tecla Bloq Mayús con su color mientras esté activado."""
        if self.caps_light() and self.caps_state():
            frame = {**frame, CAPS_KEY: self.caps_color}
        return frame

    def capture(self) -> dict:
        with self._lock:
            if self._kb is None and self._connect() is None:
                raise RuntimeError(self.error)
            keys = self._kb.capture()
            name = f"Captured from {self._kb.name}"
        return Profile(name=name, designed_for=self.layout.name,
                       layers=[{"effect": "static", "params": {"keys": keys}}]).to_dict()

    # --- memoria del teclado -------------------------------------------------
    def onboard_plan(self, data: dict) -> onboard.Plan:
        with self._lock:
            if self._kb is None and self._connect() is None:
                raise RuntimeError(self.error)
            return onboard.plan(data, self._kb.modes())

    def save_to_memory(self, data: dict) -> str:
        """Guarda ``data`` en la memoria del teclado y deja de pintarlo desde KeyGlow."""
        plan = self.onboard_plan(data)
        profile, _ = prepare(data, self.layout)
        frame = Renderer(profile, self.layout).frame(0)
        self.stop()  # si KeyGlow siguiera pintando, taparía lo guardado
        with self._lock:
            self._kb.save_to_memory(plan, frame)
        return plan.summary

    def device_description(self) -> dict | None:
        """Descripción del teclado conectado al estilo de OpenRGB (para exportar perfiles)."""
        with self._lock:
            if self._kb is None:
                self._connect()
            return self._kb.describe() if self._kb is not None else None

    def status(self) -> dict:
        with self._lock:
            return {
                "connected": self._kb is not None,
                "device": self.device_name,
                "running": self.running,
                "profile": (self._profile or {}).get("name", ""),
                "error": self.error,
                "brightness": self.brightness,
                "override": self.override,
                "layout": self.layout.name,
                "can_save": bool(self._kb is not None and onboard.can_save(self._kb.modes())),
                "layout_rev": self.layout_rev,
                "caps_indicator": self.layout.caps_indicator,
            }

    # --- vista previa -------------------------------------------------------
    def frames(self, data: dict, start: float, count: int, fps: float) -> dict:
        """Calcula ``count`` fotogramas desde ``start`` para la vista previa del navegador."""
        if has_reactive(data.get("layers", [])):
            self._reactive_preview_until = time.monotonic() + 6
            self.housekeeping()
        key = json.dumps(data, sort_keys=True)
        report: list[str] = []
        with self._plock:
            entry = self._previews.get(key)
            if entry is None:
                profile, rep = prepare(data, self.layout)
                entry = (Renderer(profile, self.layout),
                         rep.lines() if (rep.dropped or rep.unknown or rep.filled) else [])
                self._previews[key] = entry
                if len(self._previews) > 32:
                    self._previews.popitem(last=False)
            else:
                self._previews.move_to_end(key)
            renderer, report = entry
            ids = self.layout.ids
            out = []
            for i in range(max(1, min(count, 240))):
                f = renderer.frame(start + i / fps)
                out.append(["%02x%02x%02x" % f[k] for k in ids])
        return {"keys": ids, "frames": out, "report": report}
