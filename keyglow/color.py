"""Utilidades de color. Internamente los colores son tuplas RGB en floats 0..1."""

from __future__ import annotations

import colorsys

RGB = tuple[float, float, float]

NAMED = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#00ff00",
    "blue": "#0000ff", "yellow": "#ffff00", "cyan": "#00ffff", "magenta": "#ff00ff",
    "orange": "#ff8000", "purple": "#8000ff", "pink": "#ff40a0", "off": "#000000",
}


def parse(value) -> RGB:
    """Acepta ``"#rrggbb"``, ``"#rgb"``, ``[r, g, b]`` (0-255) o un nombre."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return tuple(max(0.0, min(1.0, float(c) / 255)) for c in value)  # type: ignore[return-value]
    if isinstance(value, str):
        s = NAMED.get(value.strip().lower(), value.strip())
        s = s.lstrip("#")
        if len(s) == 3:
            s = "".join(c * 2 for c in s)
        if len(s) == 6:
            try:
                return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]
            except ValueError:
                pass
    raise ValueError(f"Invalid color: {value!r}")


def to_hex(c: RGB) -> str:
    return "#" + "".join(f"{v:02x}" for v in to_bytes(c))


def to_bytes(c: RGB) -> tuple[int, int, int]:
    return tuple(int(round(max(0.0, min(1.0, v)) * 255)) for v in c)  # type: ignore[return-value]


def hsv(h: float, s: float = 1.0, v: float = 1.0) -> RGB:
    return colorsys.hsv_to_rgb(h % 1.0, s, v)


def lerp(a: RGB, b: RGB, t: float) -> RGB:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def scale(c: RGB, k: float) -> RGB:
    return (c[0] * k, c[1] * k, c[2] * k)


def palette_at(colors: list[RGB], p: float, cyclic: bool = False) -> RGB:
    """Interpola una paleta en la posición ``p`` (0..1)."""
    if len(colors) == 1:
        return colors[0]
    if cyclic:
        p %= 1.0
        n = len(colors)
        f = p * n
        i = int(f) % n
        return lerp(colors[i], colors[(i + 1) % n], f - int(f))
    p = max(0.0, min(1.0, p))
    f = p * (len(colors) - 1)
    i = min(int(f), len(colors) - 2)
    return lerp(colors[i], colors[i + 1], f - i)
