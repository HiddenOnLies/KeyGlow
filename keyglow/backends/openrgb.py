"""Control del hardware real a través del servidor SDK de OpenRGB.

OpenRGB ya implementa los protocolos USB de cientos de dispositivos; KeyGlow se
limita a mandarle colores por tecla. Requisitos:
  1. Instalar OpenRGB (https://openrgb.org) y abrirlo.
  2. Pestaña "SDK Server" -> "Start Server" (puerto 6742 por defecto).
  3. ``pip install keyglow[openrgb]``
"""

from __future__ import annotations

import time

from ..keynames import normalize
from ..layout import Layout, from_device
from ..profile import Profile, Renderer


class OpenRGBKeyboard:
    def __init__(self, host: str = "127.0.0.1", port: int = 6742, match: str = ""):
        try:
            from openrgb import OpenRGBClient
            from openrgb.utils import DeviceType, RGBColor
        except ImportError as e:
            raise RuntimeError("openrgb-python is missing: pip install keyglow[openrgb]") from e
        self._RGBColor = RGBColor
        try:
            self.client = OpenRGBClient(host, port, name="KeyGlow")
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            raise RuntimeError(
                f"Couldn't reach OpenRGB at {host}:{port}. "
                "Is it open with the SDK Server started?") from e
        candidates = [d for d in self.client.devices if d.type == DeviceType.KEYBOARD]
        if match:
            candidates = [d for d in candidates if match.lower() in d.name.lower()]
        if not candidates:
            names = ", ".join(f"{d.name} ({d.type.name})" for d in self.client.devices) or "none"
            raise RuntimeError(f"No keyboard matches '{match}'. Devices: {names}")
        self.device = candidates[0]
        self.led_ids = [normalize(led.name) for led in self.device.leds]
        # Los LEDs sin nombre son huecos de la matriz, no teclas: no se avisa de ellos.
        self.unmapped = [led.name for led, kid in zip(self.device.leds, self.led_ids)
                         if kid is None and led.name.strip()]
        try:
            self.device.set_mode("direct")
        except Exception:
            pass  # algunos dispositivos no tienen modo "direct"; set_colors suele bastar

    @property
    def name(self) -> str:
        return self.device.name

    def layout(self) -> Layout:
        """Distribución de este teclado según sus LEDs y la matriz que informa OpenRGB."""
        matrix: list[list[int | None]] = []
        start = 0
        for zone in self.device.zones:
            # los índices de la matriz son relativos a la zona; se pasan a índices globales
            for row in zone.matrix_map or []:
                matrix.append([None if i is None else start + i for i in row])
            start += len(zone.leds)
        return from_device(self.device.name, [led.name for led in self.device.leds], matrix)

    def describe(self) -> dict:
        """Descripción del teclado en el formato de los perfiles .json de OpenRGB."""
        d, meta = self.device.data, self.device.data.metadata
        none = 0xFFFFFFFF

        def num(v):
            return int(v) if v is not None else 0

        return {
            "name": d.name, "vendor": meta.vendor or "", "description": meta.description,
            "version": meta.version, "serial": meta.serial, "location": meta.location,
            "type": int(d.device_type), "active_mode": d.active_mode,
            "modes": [{"name": m.name, "flags": int(m.flags), "speed_min": num(m.speed_min),
                       "speed_max": num(m.speed_max), "brightness_min": num(m.brightness_min),
                       "brightness_max": num(m.brightness_max), "colors_min": num(m.colors_min),
                       "colors_max": num(m.colors_max), "speed": num(m.speed),
                       "brightness": num(m.brightness), "direction": num(m.direction),
                       "color_mode": int(m.color_mode), "colors": []} for m in d.modes],
            "zones": [{"name": z.name, "type": int(z.zone_type), "leds_count": z.num_leds,
                       "leds_min": z.leds_min, "leds_max": z.leds_max,
                       "matrix_map": {"height": z.mat_height or 0, "width": z.mat_width or 0,
                                      "map": [none if v is None else v
                                              for row in (z.matrix_map or []) for v in row]}}
                      for z in d.zones],
            "leds": [{"name": led.name} for led in d.leds],
        }

    def write(self, frame: dict[str, tuple[int, int, int]]) -> None:
        RGB = self._RGBColor
        colors = [RGB(*frame.get(kid, (0, 0, 0))) if kid else RGB(0, 0, 0) for kid in self.led_ids]
        self.device.set_colors(colors, fast=True)

    def capture(self) -> dict[str, str]:
        """Lee los colores actuales del teclado (útil para rescatar perfiles de OpenRGB)."""
        self.device.update()
        out = {}
        for kid, c in zip(self.led_ids, self.device.colors):
            if kid:
                out[kid] = f"#{c.red:02x}{c.green:02x}{c.blue:02x}"
        return out


def run(profile: Profile, layout: Layout, kb: OpenRGBKeyboard, fps: float = 30,
        seconds: float = 0) -> None:
    """Reproduce el perfil en el teclado. ``seconds=0`` = hasta Ctrl+C."""
    renderer = Renderer(profile, layout)
    start = time.monotonic()
    period = 1 / fps
    try:
        while True:
            t = time.monotonic() - start
            if seconds and t >= seconds:
                break
            kb.write(renderer.frame(t))
            time.sleep(max(0.0, period - (time.monotonic() - start - t)))
    except KeyboardInterrupt:
        pass
