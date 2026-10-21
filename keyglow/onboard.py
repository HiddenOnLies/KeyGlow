"""Guardar la iluminación en la memoria del propio teclado.

Así el teclado la conserva sin KeyGlow (ni OpenRGB) en marcha, incluso tras apagar
el PC. Solo es posible si el controlador de OpenRGB de ese teclado sabe guardar:
sus modos llevan la marca ``MANUAL_SAVE`` (hay que pedir el guardado) o
``AUTOMATIC_SAVE`` (se guarda al cambiar de modo).

El teclado solo entiende sus propios modos (estático, respiración, arcoíris...), no las
capas de KeyGlow, así que :func:`plan` elige el modo de hardware que mejor reproduce
el perfil: un modo equivalente si el perfil es un único efecto sencillo, o los colores
tecla a tecla (una foto del perfil) si el teclado tiene un modo por tecla guardable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MANUAL_SAVE = 1 << 8
AUTOMATIC_SAVE = 1 << 9
PER_LED = 1  # MODE_COLORS_PER_LED
MODE_SPECIFIC = 2  # MODE_COLORS_MODE_SPECIFIC

# efecto KeyGlow -> palabras que suelen aparecer en el nombre del modo equivalente
_EQUIVALENT = {
    "solid": ("static", "fixed", "solid", "direct"),
    "breathing": ("breath", "pulse"),
    "spectrum": ("spectrum", "color cycle", "colour cycle", "cycle"),
    "rainbow_wave": ("rainbow wave", "rainbow", "wave"),
    "color_wave": ("wave",),
    "ripple": ("ripple", "ring"),
    "starlight": ("starlight", "star", "twinkle", "random"),
    "reactive": ("reactive", "keypress", "key press"),
}


@dataclass
class Mode:
    name: str
    flags: int
    color_mode: int = 0
    colors_min: int = 0
    colors_max: int = 0


@dataclass
class Plan:
    mode: int                      # índice del modo de hardware
    per_led: bool                  # True: se guardan los colores de cada tecla
    colors: list[tuple[int, int, int]] = field(default_factory=list)  # colores del modo
    manual_save: bool = True       # hay que pedir el guardado (si no, es automático)
    summary: str = ""


def can_save(modes: list[Mode]) -> bool:
    return any(m.flags & (MANUAL_SAVE | AUTOMATIC_SAVE) for m in modes)


def _rgb(value) -> tuple[int, int, int]:
    s = str(value).lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def plan(profile: dict, modes: list[Mode]) -> Plan:
    """Decide qué modo de hardware guardar para ``profile``. ``ValueError`` si no se puede."""
    savable = [(i, m) for i, m in enumerate(modes) if m.flags & (MANUAL_SAVE | AUTOMATIC_SAVE)]
    if not savable:
        raise ValueError("This keyboard can't store lighting in its memory through OpenRGB. "
                         "KeyGlow has to stay open to keep the colors.")
    layers = profile.get("layers", [])
    simple = len(layers) == 1 and not layers[0].get("keys")
    if simple:
        effect = layers[0].get("effect")
        params = layers[0].get("params", {})
        words = _EQUIVALENT.get(effect, ())
        for i, m in savable:
            name = m.name.lower()
            if m.color_mode == PER_LED or not any(w in name for w in words):
                continue
            raw = params.get("colors") or ([params["color"]] if "color" in params else [])
            colors = [_rgb(c) for c in raw][: max(m.colors_max, 0)] if m.color_mode == MODE_SPECIFIC else []
            if m.color_mode == MODE_SPECIFIC and len(colors) < m.colors_min:
                continue
            return Plan(i, False, colors, bool(m.flags & MANUAL_SAVE),
                        f"the keyboard's own “{m.name}” mode")
    for i, m in savable:
        if m.color_mode == PER_LED:
            note = "" if all(l.get("effect") in ("solid", "static", "gradient", "points", "image")
                             for l in layers) else " (animations become a still picture)"
            return Plan(i, True, [], bool(m.flags & MANUAL_SAVE),
                        f"each key's color, in the “{m.name}” mode{note}")
    names = ", ".join(m.name for _, m in savable)
    raise ValueError(f"This keyboard can only store its own modes ({names}), and none of them "
                     "matches this profile. Try a single simple effect (static, breathing, rainbow…).")
