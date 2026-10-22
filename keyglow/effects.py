"""Efectos de iluminación.

Todos los efectos se definen sobre la posición física de cada tecla (no sobre su
índice de LED), así que el mismo efecto funciona igual en un 65%, un 60% o un 100%.
Un efecto devuelve ``None`` para "transparente" (deja ver la capa de abajo).
"""

from __future__ import annotations

import math
import time
import zlib
from dataclasses import dataclass

from . import color as C
from .color import RGB
from .layout import Layout

REGISTRY: dict[str, type[Effect]] = {}


@dataclass(frozen=True)
class KeyCtx:
    id: str
    u: float  # centro normalizado 0..1 (horizontal)
    v: float  # centro normalizado 0..1 (vertical)
    x: float  # centro en unidades de tecla
    y: float


def register(name: str):
    def deco(cls):
        cls.name = name
        REGISTRY[name] = cls
        return cls
    return deco


class Effect:
    name = "?"
    #: parámetros por defecto, documentan también qué acepta el efecto
    defaults: dict = {}

    def __init__(self, params: dict, layout: Layout):
        unknown = set(params) - set(self.defaults)
        if unknown:
            raise ValueError(f"Unknown parameters for '{self.name}': {', '.join(sorted(unknown))}")
        self.p = {**self.defaults, **params}
        self.layout = layout
        self.setup()

    def setup(self) -> None:
        pass

    def color(self, k: KeyCtx, t: float) -> RGB | None:
        raise NotImplementedError

    # ayudas comunes
    def colors(self, key: str = "colors") -> list[RGB]:
        return [C.parse(c) for c in self.p[key]]

    def project(self, k: KeyCtx, angle_deg: float) -> float:
        """Proyecta la tecla sobre una dirección; devuelve 0..1 a lo largo del teclado."""
        a = math.radians(angle_deg)
        dx, dy = math.cos(a), math.sin(a)
        return ((k.u - 0.5) * dx + (k.v - 0.5) * dy) / (abs(dx) + abs(dy)) + 0.5


def _rand(*parts) -> float:
    return (zlib.crc32("|".join(map(str, parts)).encode()) & 0xFFFFFFFF) / 0xFFFFFFFF


@register("solid")
class Solid(Effect):
    defaults = {"color": "#ffffff"}

    def setup(self):
        self.c = C.parse(self.p["color"])

    def color(self, k, t):
        return self.c


@register("static")
class Static(Effect):
    """Color fijo por tecla: ``{"keys": {"W": "#ff0000", "Left Control": "#00f"}}``."""
    defaults = {"keys": {}}

    def setup(self):
        from .keynames import normalize
        self.map = {}
        self.unknown = []
        for name, value in self.p["keys"].items():
            kid = normalize(name) or (name if name in self.layout else None)
            if kid is None:
                self.unknown.append(name)
            else:
                self.map[kid] = C.parse(value)

    def color(self, k, t):
        return self.map.get(k.id)


@register("gradient")
class Gradient(Effect):
    defaults = {"colors": ["#ff0080", "#00c0ff"], "angle": 0}

    def setup(self):
        self.cs = self.colors()

    def color(self, k, t):
        return C.palette_at(self.cs, self.project(k, self.p["angle"]))


@register("rainbow_wave")
class RainbowWave(Effect):
    defaults = {"speed": 0.25, "angle": 0, "wavelength": 1.0, "saturation": 1.0}

    def color(self, k, t):
        pos = self.project(k, self.p["angle"]) / max(self.p["wavelength"], 1e-3)
        return C.hsv(pos - t * self.p["speed"], self.p["saturation"])


@register("color_wave")
class ColorWave(Effect):
    """Una paleta propia que se desplaza por el teclado."""
    defaults = {"colors": ["#ff0080", "#7000ff", "#00c0ff"], "speed": 0.2, "angle": 0,
                "wavelength": 1.0}

    def setup(self):
        self.cs = self.colors()

    def color(self, k, t):
        pos = self.project(k, self.p["angle"]) / max(self.p["wavelength"], 1e-3)
        return C.palette_at(self.cs, pos - t * self.p["speed"], cyclic=True)


@register("spectrum")
class Spectrum(Effect):
    defaults = {"speed": 0.1, "saturation": 1.0}

    def color(self, k, t):
        return C.hsv(t * self.p["speed"], self.p["saturation"])


@register("breathing")
class Breathing(Effect):
    defaults = {"colors": ["#00c0ff"], "period": 4.0, "min": 0.0}

    def setup(self):
        self.cs = self.colors()

    def color(self, k, t):
        period = max(self.p["period"], 0.1)
        cycle = int(t // period)
        level = (1 - math.cos(2 * math.pi * (t % period) / period)) / 2
        level = self.p["min"] + (1 - self.p["min"]) * level
        return C.scale(self.cs[cycle % len(self.cs)], level)


@register("ripple")
class Ripple(Effect):
    """Anillos que salen de un punto (u, v) del teclado."""
    defaults = {"center": [0.5, 0.5], "colors": ["#00ffd0", "#0040ff"], "speed": 0.4,
                "thickness": 0.12, "background": None}

    def setup(self):
        self.cs = self.colors()
        self.bg = C.parse(self.p["background"]) if self.p["background"] else None
        aspect = self.layout.width / self.layout.height
        self.aspect = aspect

    def color(self, k, t):
        cu, cv = self.p["center"]
        d = math.hypot(k.u - cu, (k.v - cv) / self.aspect)
        period = 1.0 / max(self.p["speed"], 1e-3)
        radius = (t % period) / period
        ring = math.exp(-((d - radius) / max(self.p["thickness"], 1e-3)) ** 2)
        c = C.palette_at(self.cs, d * 1.5)
        if self.bg is None:
            return C.scale(c, ring) if ring > 0.02 else None
        return C.lerp(self.bg, c, ring)


@register("starlight")
class Starlight(Effect):
    """Destellos aleatorios (deterministas, se repiten igual en cualquier PC)."""
    defaults = {"colors": ["#ffffff", "#80c0ff"], "background": "#000010", "density": 0.15,
                "period": 2.0, "seed": 1}

    def setup(self):
        self.cs = self.colors()
        self.bg = C.parse(self.p["background"])

    def color(self, k, t):
        period = max(self.p["period"], 0.1)
        phase = _rand(self.p["seed"], k.id, "phase") * period
        tt = t + phase
        cycle = int(tt // period)
        if _rand(self.p["seed"], k.id, cycle) >= self.p["density"]:
            return self.bg
        star = self.cs[int(_rand(self.p["seed"], k.id, cycle, "c") * len(self.cs)) % len(self.cs)]
        return C.lerp(self.bg, star, math.sin(math.pi * (tt % period) / period))


@register("points")
class Points(Effect):
    """Colores anclados a posiciones del teclado; cada tecla toma el punto más cercano
    (o una mezcla suave si ``smooth`` > 0). Es el formato que se usa al convertir un
    perfil por tecla de otro teclado en algo independiente de la distribución."""
    defaults = {"points": [], "smooth": 0.0}

    def setup(self):
        self.pts = [(pt["u"], pt["v"], C.parse(pt["color"])) for pt in self.p["points"]]

    def color(self, k, t):
        if not self.pts:
            return None
        if self.p["smooth"] <= 0:
            u, v, c = min(self.pts, key=lambda pt: (pt[0] - k.u) ** 2 + (pt[1] - k.v) ** 2)
            return c
        acc, wsum = [0.0, 0.0, 0.0], 0.0
        for u, v, c in self.pts:
            w = math.exp(-((u - k.u) ** 2 + (v - k.v) ** 2) / self.p["smooth"] ** 2)
            wsum += w
            for i in range(3):
                acc[i] += c[i] * w
        return tuple(a / wsum for a in acc) if wsum > 1e-9 else None  # type: ignore[return-value]


@register("image")
class Image(Effect):
    """Muestrea una imagen (un wallpaper, un logo...) estirada sobre el teclado.
    Con ``scroll`` > 0 la imagen se desplaza horizontalmente."""
    defaults = {"path": "", "scroll": 0.0}

    def setup(self):
        try:
            from PIL import Image as PILImage
        except ImportError as e:
            raise RuntimeError("The 'image' effect needs Pillow: pip install keyglow[image]") from e
        img = PILImage.open(self.p["path"]).convert("RGB")
        img.thumbnail((256, 256))
        self.img = img
        self.px = img.load()

    def color(self, k, t):
        w, h = self.img.size
        u = (k.u + t * self.p["scroll"]) % 1.0
        r, g, b = self.px[min(int(u * w), w - 1), min(int(k.v * h), h - 1)]
        return (r / 255, g / 255, b / 255)


def _noise(x: float, y: float, seed: int = 0) -> float:
    """Ruido de valor suave en 2D (0..1), determinista."""
    xi, yi = math.floor(x), math.floor(y)
    xf, yf = x - xi, y - yi
    sx, sy = xf * xf * (3 - 2 * xf), yf * yf * (3 - 2 * yf)
    a = _rand(seed, xi, yi)
    b = _rand(seed, xi + 1, yi)
    c = _rand(seed, xi, yi + 1)
    d = _rand(seed, xi + 1, yi + 1)
    return (a + (b - a) * sx) + ((c + (d - c) * sx) - (a + (b - a) * sx)) * sy


@register("plasma")
class Plasma(Effect):
    """Manchas de color que fluyen y se mezclan, como una lámpara de lava."""
    defaults = {"colors": ["#ff0080", "#7000ff", "#00c0ff", "#00ff90"], "speed": 0.3, "scale": 1.0}

    def setup(self):
        self.cs = self.colors()

    def color(self, k, t):
        s, tt = max(self.p["scale"], 0.05), t * self.p["speed"]
        x, y = k.u * 3 / s, k.v * 3 / s
        val = (math.sin(x * 1.7 + tt * 2.1) + math.sin(y * 2.3 - tt * 1.3)
               + math.sin((x + y) * 1.1 + tt * 1.7) + math.sin(math.hypot(x - 1.5, y - 1.5) * 2 - tt * 2.5))
        return C.palette_at(self.cs, (val + 4) / 8 + tt * 0.1, cyclic=True)


@register("rain")
class Rain(Effect):
    """Gotas que caen por columnas, con estela."""
    defaults = {"colors": ["#00e5ff", "#ffffff"], "background": "#000814", "speed": 0.6,
                "density": 0.5, "length": 0.35, "seed": 5}

    def setup(self):
        self.cs = self.colors()
        self.bg = C.parse(self.p["background"])

    def color(self, k, t):
        col = round(k.x * 2)  # medias columnas: las teclas anchas no quedan apagadas
        if _rand(self.p["seed"], col, "on") > self.p["density"]:
            return self.bg
        rate = self.p["speed"] * (0.6 + 0.8 * _rand(self.p["seed"], col, "v"))
        head = (t * rate + _rand(self.p["seed"], col, "p")) % 1.0 * 1.6 - 0.3
        d = head - k.v
        if d < 0 or d > max(self.p["length"], 0.02):
            return self.bg
        c = self.cs[int(_rand(self.p["seed"], col, "c") * len(self.cs)) % len(self.cs)]
        return C.lerp(self.bg, c, 1 - d / max(self.p["length"], 0.02))


@register("scanner")
class Scanner(Effect):
    """Una barra de luz que va y vuelve (como el coche fantástico)."""
    defaults = {"color": "#ff0020", "background": "#100000", "speed": 0.5, "width": 0.15, "angle": 0}

    def setup(self):
        self.c = C.parse(self.p["color"])
        self.bg = C.parse(self.p["background"])

    def color(self, k, t):
        phase = (t * self.p["speed"]) % 2.0
        pos = phase if phase < 1 else 2 - phase
        d = abs(self.project(k, self.p["angle"]) - pos)
        return C.lerp(self.bg, self.c, math.exp(-(d / max(self.p["width"], 0.01)) ** 2))


@register("fire")
class Fire(Effect):
    """Llamas que suben desde abajo."""
    defaults = {"colors": ["#000000", "#a00000", "#ff4000", "#ffb000", "#ffff80"],
                "speed": 1.0, "height": 0.7}

    def setup(self):
        self.cs = self.colors()

    def color(self, k, t):
        tt = t * self.p["speed"]
        n = _noise(k.u * 6, k.v * 4 + tt * 3, 1) * 0.65 + _noise(k.u * 13, k.v * 9 + tt * 6, 2) * 0.35
        heat = (k.v - (1 - max(self.p["height"], 0.05))) / max(self.p["height"], 0.05)
        return C.palette_at(self.cs, max(0.0, min(1.0, heat * 0.9 + (n - 0.5) * 0.9)))


@register("heartbeat")
class Heartbeat(Effect):
    """Doble pulso de latido."""
    defaults = {"color": "#ff0030", "bpm": 70, "min": 0.05}

    def setup(self):
        self.c = C.parse(self.p["color"])

    def color(self, k, t):
        beat = (t * max(self.p["bpm"], 10) / 60) % 1.0
        level = max(math.exp(-((beat - 0.1) / 0.05) ** 2), 0.6 * math.exp(-((beat - 0.32) / 0.06) ** 2))
        return C.scale(self.c, self.p["min"] + (1 - self.p["min"]) * level)


@register("reactive")
class Reactive(Effect):
    """Se ilumina al pulsar teclas: la propia tecla, una onda que sale de ella o su fila.
    Las teclas sin pulsar son transparentes (dejan ver las capas de abajo)."""
    defaults = {"colors": ["#ffffff"], "style": "key", "duration": 0.6, "speed": 1.0,
                "background": None}
    STYLES = ("key", "ripple", "row")

    def setup(self):
        if self.p["style"] not in self.STYLES:
            raise ValueError(f"style must be one of {', '.join(self.STYLES)}")
        self.cs = self.colors()
        self.bg = C.parse(self.p["background"]) if self.p["background"] else None
        self.pos = {k.id: (k.cx, k.cy) for k in self.layout.keys}
        self._t = None
        self._events: list[tuple[str, float]] = []

    def color(self, k, t):
        from . import input as keyinput
        now = time.monotonic()
        # una lectura por fotograma, no una por tecla: todas las teclas de un fotograma comparten t
        # (no se usa el reloj: en Windows avanza a saltos de ~15 ms y repetiría lecturas viejas)
        if self._t != t:
            self._t = t
            self._events = keyinput.recent(max(self.p["duration"], 0.05) * 2)
        dur = max(self.p["duration"], 0.05)
        best, best_c = 0.0, None
        for i, (key, age) in enumerate(self._events):
            if age > dur * (2 if self.p["style"] == "ripple" else 1) or key not in self.pos:
                continue
            fade = 1 - age / (dur * (2 if self.p["style"] == "ripple" else 1))
            if self.p["style"] == "key":
                level = fade if key == k.id else 0.0
            elif self.p["style"] == "row":
                level = fade if abs(self.pos[key][1] - k.y) < 0.5 else 0.0
            else:
                d = math.hypot(self.pos[key][0] - k.x, self.pos[key][1] - k.y)
                radius = age * self.p["speed"] * 12
                level = fade * math.exp(-((d - radius) / 0.9) ** 2)
            if level > best:
                best, best_c = level, self.cs[i % len(self.cs)]
        if best_c is None or best < 0.01:
            return self.bg
        if self.bg:
            return C.lerp(self.bg, best_c, best)
        return (*best_c, best)  # color con transparencia: se funde con las capas de abajo


def has_reactive(layers: list[dict]) -> bool:
    return any(layer.get("effect") == "reactive" for layer in layers)


def describe() -> dict[str, dict]:
    return {name: cls.defaults for name, cls in REGISTRY.items()}
