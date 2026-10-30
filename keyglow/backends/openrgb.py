"""Control del hardware real a través del servidor SDK de OpenRGB.

OpenRGB ya implementa los protocolos USB de cientos de dispositivos; KeyGlow se
limita a mandarle colores por tecla. Requisitos:
  1. Instalar OpenRGB (https://openrgb.org) y abrirlo.
  2. Pestaña "SDK Server" -> "Start Server" (puerto 6742 por defecto).
  3. ``pip install keyglow[openrgb]``
"""

from __future__ import annotations

import re
import socket
import struct
import time

from .. import onboard
from ..keynames import normalize
from ..layout import Layout, from_device
from ..profile import Profile, Renderer


class NoKeyboard(RuntimeError):
    """OpenRGB responde pero no tiene ningún teclado (``devices``: lo que sí ve)."""

    def __init__(self, message: str, devices: list[str]):
        super().__init__(message)
        self.devices = devices


def _identity(device) -> tuple:
    """Lo que distingue a un dispositivo aunque cambie su posición en la lista de OpenRGB."""
    meta = device.data.metadata
    return (device.name, meta.location or "", meta.serial or "", len(device.leds))


def rescan(host: str = "127.0.0.1", port: int = 6742, timeout: float = 3.0) -> bool:
    """Pide a OpenRGB que vuelva a buscar dispositivos (p. ej. al pasar del cable al receptor).

    Usa una conexión aparte, así no se mezcla con la que manda los colores. Devuelve False si
    el OpenRGB es anterior a la 1.0 (protocolo < 5), que no tiene esta orden.
    """
    def header(packet: int, size: int) -> bytes:
        return struct.pack("<4sIII", b"ORGB", 0, packet, size)

    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall(header(40, 4) + struct.pack("<I", 5))  # versión de protocolo: 5 es la de la orden
        reply = s.recv(16 + 4)
        if len(reply) < 20 or reply[:4] != b"ORGB":
            return False
        version = struct.unpack("<I", reply[16:20])[0]
        if version < 5:
            return False
        s.sendall(header(140, 0))
        return True


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
            seen = [f"{d.name} ({d.type.name.lower()})" for d in self.client.devices if d is not None]
            self.client.disconnect()
            if match:
                raise NoKeyboard(f"No keyboard matches '{match}'. OpenRGB sees: {', '.join(seen) or 'nothing'}", seen)
            raise NoKeyboard(f"OpenRGB doesn't see any keyboard. It sees: {', '.join(seen) or 'nothing'}", seen)
        self.device = candidates[0]
        self.index = self.device.id
        self.identity = _identity(self.device)
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

    def still_there(self) -> bool:
        """Pregunta a OpenRGB cuántos dispositivos tiene, lo que de paso le hace leer sus avisos
        de "la lista cambió", y comprueba que en nuestra posición sigue estando este teclado.

        Si no (se desconectó, se pasó del cable al receptor, OpenRGB volvió a buscar...), hay
        que reconectar: OpenRGB identifica los dispositivos por su posición y los colores
        podrían acabar en otro.
        """
        self.client.comms.requestDeviceNum()
        devices = self.client.devices
        here = devices[self.index] if self.index < len(devices) else None
        # si OpenRGB rehízo la lista, openrgb-python crea objetos nuevos: aunque sea el mismo
        # teclado, puede haber vuelto a su modo propio y hay que volver a ponerlo en "direct"
        return here is self.device and _identity(here) == self.identity

    def close(self) -> None:
        try:
            self.client.disconnect()
        except Exception:  # noqa: BLE001 - ya estaba cerrada
            pass

    # --- memoria del teclado --------------------------------------------------
    def modes(self) -> list[onboard.Mode]:
        return [onboard.Mode(m.name, int(m.flags), int(m.color_mode), m.colors_min or 0,
                             m.colors_max or 0) for m in self.device.modes]

    def save_to_memory(self, plan: onboard.Plan, frame: dict[str, tuple[int, int, int]]) -> None:
        """Pone el modo de hardware de ``plan`` y lo guarda en la memoria del teclado."""
        RGB = self._RGBColor
        mode = self.device.modes[plan.mode]
        if plan.colors:
            mode.colors = [RGB(*c) for c in plan.colors]
        self.device.set_mode(mode)
        if plan.per_led:
            self.write(frame)
        if plan.manual_save:
            self.device.save_mode()

    def layout(self) -> Layout:
        """Distribución de este teclado según sus LEDs y la matriz que informa OpenRGB."""
        matrix: list[list[int | None]] = []
        start = 0
        for zone in self.device.zones:
            # los índices de la matriz son relativos a la zona; se pasan a índices globales
            for row in zone.matrix_map or []:
                matrix.append([None if i is None else start + i for i in row])
            start += len(zone.leds)
        return from_device(self.device.name, [led.name for led in self.device.leds], matrix,
                           self.usb_id)

    @property
    def usb_id(self) -> str:
        """``"vvvv:pppp"`` sacado de la ubicación que da OpenRGB (``HID: ...VID_xxxx&PID_yyyy...``)."""
        m = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", self.device.data.metadata.location or "", re.I)
        return f"{m.group(1)}:{m.group(2)}".lower() if m else ""

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
