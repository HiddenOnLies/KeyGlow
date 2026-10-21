"""Perfiles de OpenRGB.

OpenRGB guarda en un perfil la descripción de cada dispositivo con sus LEDs y el
color de cada uno. Hay dos formatos, ambos documentados en su código fuente
(``ProfileManager.cpp`` y ``RGBController.cpp``):

- ``.json`` (OpenRGB 1.0 en adelante)::

      {"profile_version": 5, "profile_name": "...", "controllers": [
          {"name": "...", "type": 5, "leds": [{"name": "Key: A"}, ...],
           "colors": [<0x00BBGGRR>, ...],
           "zones": [{"name": "...", "matrix_map": {"height": 5, "width": 15, "map": [...]}}],
           ...}]}

- ``.orp`` (binario, versiones anteriores): cabecera ``OPENRGB_PROFILE``, versión y,
  por dispositivo, su descripción en el mismo formato que el protocolo del SDK.

Aquí solo interesan los teclados: nombres de LED, colores y la matriz de posiciones.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field

from ..keynames import external_name, normalize
from ..layout import Layout, from_device
from ..profile import Profile

KEYBOARD = 5  # DEVICE_TYPE_KEYBOARD
_NO_LED = 0xFFFFFFFF
_HEADER = b"OPENRGB_PROFILE"


@dataclass
class Controller:
    name: str
    type: int
    leds: list[str]
    colors: list[tuple[int, int, int]]
    matrix: list[list[int | None]] = field(default_factory=list)

    @property
    def is_keyboard(self) -> bool:
        return self.type == KEYBOARD or sum(1 for n in self.leds if normalize(n)) >= 20

    def keys(self) -> dict[str, str]:
        """``{id: "#rrggbb"}`` de las teclas reconocidas (la primera aparición manda)."""
        out: dict[str, str] = {}
        for name, (r, g, b) in zip(self.leds, self.colors):
            kid = normalize(name) if name.strip() else None
            if kid and kid not in out:
                out[kid] = f"#{r:02x}{g:02x}{b:02x}"
        return out

    def layout(self) -> Layout | None:
        try:
            return from_device(self.name, self.leds, self.matrix or None)
        except ValueError:
            return None


def _rgb(value: int) -> tuple[int, int, int]:
    return value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF


def _value(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return r | (g << 8) | (b << 16)


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------
def parse(data: bytes) -> tuple[str, list[Controller]]:
    """Lee un perfil (JSON o ``.orp``). Devuelve ``(nombre, dispositivos)``."""
    if data.startswith(_HEADER):
        return "", _parse_orp(data)
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise ValueError("This is not an OpenRGB profile") from e
    if not isinstance(doc, dict) or "controllers" not in doc:
        raise ValueError("This JSON is not an OpenRGB profile (no 'controllers')")
    return doc.get("profile_name", ""), [_controller_from_json(c) for c in doc["controllers"]]


def _controller_from_json(c: dict) -> Controller:
    matrix: list[list[int | None]] = []
    start = 0
    for zone in c.get("zones", []):
        mm = zone.get("matrix_map") or {}
        h, w, cells = mm.get("height", 0), mm.get("width", 0), mm.get("map") or []
        for r in range(h):
            matrix.append([None if v in (None, _NO_LED) else start + v for v in cells[r * w:(r + 1) * w]])
        start += zone.get("leds_count", 0)
    return Controller(
        name=c.get("name", ""),
        type=int(c.get("type", -1)),
        leds=[led.get("name", "") for led in c.get("leds", [])],
        colors=[_rgb(int(v)) for v in c.get("colors", [])],
        matrix=matrix,
    )


class _Reader:
    def __init__(self, data: bytes, pos: int = 0):
        self.data, self.pos = data, pos

    def take(self, fmt: str):
        size = struct.calcsize(fmt)
        if self.pos + size > len(self.data):
            raise ValueError("The OpenRGB profile is truncated")
        out = struct.unpack_from("<" + fmt, self.data, self.pos)
        self.pos += size
        return out if len(out) > 1 else out[0]

    def string(self, len_fmt: str = "H") -> str:
        n = self.take(len_fmt)
        raw = self.data[self.pos:self.pos + n]
        self.pos += n
        return raw.split(b"\0", 1)[0].decode("utf-8", "replace")


def _parse_orp(data: bytes) -> list[Controller]:
    version = struct.unpack_from("<I", data, 16)[0]
    if version == 1:  # así lo trata OpenRGB
        version = 0
    pos, out = 20, []
    while pos + 4 <= len(data):
        size = struct.unpack_from("<I", data, pos)[0]
        if size < 4:
            break
        out.append(_parse_controller(_Reader(data[pos + 4:pos + size]), version))
        pos += size
    return out


def _parse_mode(rd: _Reader, v: int) -> None:
    rd.string()
    if v < 6:
        rd.take("i")                                   # value
    rd.take("III")                                     # flags, speed_min, speed_max
    if v >= 3:
        rd.take("II")                                  # brightness_min/max
    rd.take("III")                                     # colors_min, colors_max, speed
    if v >= 3:
        rd.take("I")                                   # brightness
    rd.take("II")                                      # direction, color_mode
    n = rd.take("H")
    if n:
        rd.take("I" * n)                               # colores del modo


def _parse_matrix(rd: _Reader) -> list[list[int | None]]:
    h, w = rd.take("II")
    cells = [rd.take("I") for _ in range(h * w)]
    return [[None if v == _NO_LED else v for v in cells[r * w:(r + 1) * w]] for r in range(h)]


def _parse_controller(rd: _Reader, v: int) -> Controller:
    ctype = rd.take("i")
    name = rd.string()
    if v >= 1:
        rd.string()                                    # vendor
    for _ in range(4):
        rd.string()                                    # description, version, serial, location
    num_modes = rd.take("H")
    rd.take("i")                                       # active_mode
    for _ in range(num_modes):
        _parse_mode(rd, v)
    zones = []
    for _ in range(rd.take("H")):
        rd.string()
        rd.take("i")                                   # type
        _, _, count = rd.take("III")                   # leds_min, leds_max, leds_count
        matrix = _parse_matrix(rd) if rd.take("H") > 0 else []
        if v >= 4:
            for _ in range(rd.take("H")):              # segmentos
                rd.string()
                rd.take("iII")
                if v >= 6:
                    if rd.take("H") > 0:
                        _parse_matrix(rd)
                    rd.take("I")
        if v >= 5:
            rd.take("I")                               # flags
        if v >= 6:
            rd.take("i")
            for _ in range(rd.take("H")):
                _parse_mode(rd, v)
            rd.string()
        zones.append((count, matrix))
    leds = []
    for _ in range(rd.take("H")):
        leds.append(rd.string())
        if v < 6:
            rd.take("I")                               # value
    colors = [_rgb(rd.take("I")) for _ in range(rd.take("H"))]
    matrix, start = [], 0
    for count, zm in zones:
        matrix += [[None if c is None else start + c for c in row] for row in zm]
        start += count
    return Controller(name, ctype, leds, colors, matrix)


def to_profile(data: bytes, name: str = "OpenRGB profile") -> Profile:
    """Convierte el teclado de un perfil de OpenRGB en un perfil KeyGlow."""
    profile_name, controllers = parse(data)
    keyboards = [c for c in controllers if c.is_keyboard and c.keys()]
    if not keyboards:
        found = ", ".join(c.name for c in controllers) or "none"
        raise ValueError(f"No keyboard in this OpenRGB profile (devices: {found})")
    kb = keyboards[0]
    return Profile(
        name=profile_name or name,
        description=f"Imported from an OpenRGB profile ({kb.name}).",
        layers=[{"effect": "static", "params": {"keys": kb.keys()}}],
    )


# ---------------------------------------------------------------------------
# Escritura (OpenRGB 1.0, .json)
# ---------------------------------------------------------------------------
def export(name: str, frame: dict[str, tuple[int, int, int]], device: dict) -> dict:
    """Perfil de OpenRGB con los colores de ``frame`` para el teclado ``device``.

    ``device`` es la descripción del teclado tal como la guarda OpenRGB (``name``,
    ``vendor``, ``location``, ``serial``, ``leds``, ``zones``, ``modes``...): OpenRGB
    solo carga un perfil en el dispositivo cuya descripción coincide.
    """
    controller = dict(device)
    leds = [led.get("name", "") for led in controller.get("leds", [])]
    colors = []
    for led_name in leds:
        kid = normalize(led_name) if led_name.strip() else None
        colors.append(_value(frame.get(kid, (0, 0, 0))) if kid else 0)
    controller["colors"] = colors
    modes = [m.get("name", "").lower() for m in controller.get("modes", [])]
    for wanted in ("direct", "static", "custom"):
        if wanted in modes:
            controller["active_mode"] = modes.index(wanted)
            break
    return {"profile_version": 5, "profile_name": name, "controllers": [controller]}


def generic_device(layout: Layout, name: str = "KeyGlow keyboard") -> dict:
    """Descripción mínima de un teclado para cuando no hay uno real conectado."""
    return {
        "name": name, "vendor": "", "description": "", "version": "", "serial": "",
        "location": "", "type": KEYBOARD, "active_mode": 0,
        "modes": [{"name": "Direct", "flags": 0, "color_mode": 1, "speed": 0, "direction": 0}],
        "leds": [{"name": external_name(k, "openrgb")} for k in layout.ids],
        "zones": [{"name": "Keyboard", "type": 2, "leds_count": len(layout),
                   "leds_min": len(layout), "leds_max": len(layout)}],
    }
