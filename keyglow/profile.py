"""Formato de perfil portable y motor que lo renderiza sobre un teclado concreto.

Un perfil es JSON puro (nunca código), así que es seguro descargarlo de una
comunidad. Ejemplo mínimo::

    {
      "format": "keyglow/1",
      "name": "Aurora",
      "author": "alguien",
      "designed_for": "ansi_full",
      "layers": [
        {"effect": "color_wave", "params": {"colors": ["#0ff", "#80f"]}},
        {"effect": "solid", "params": {"color": "#ff0040"}, "keys": ["@wasd"]}
      ]
    }

Cada capa admite ``keys`` (filtro de teclas o grupos), ``opacity`` (0..1) y
``blend`` (normal, add, multiply, screen).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import color as C
from .effects import REGISTRY, Effect, KeyCtx
from .layout import Layout, resolve_keys

FORMAT = "keyglow/1"
BLENDS = ("normal", "add", "multiply", "screen")
# cómo se ven los atajos al mantener Ctrl, Alt o Win (opcional en cada perfil)
HINT_EFFECTS = ("solid", "pulse", "blink", "sparkle", "gradient", "wave", "rainbow", "profile")
# parámetros numéricos de los atajos: (mínimo, máximo)
HINT_RANGES = {"speed": (0.2, 3.0), "dim": (0.0, 0.8), "delay": (0.0, 1.5)}


def _hints_config(h) -> dict | None:
    """Valida ``{"enabled", "effect", "color", "colors", "speed", "dim", "delay"}`` (todo opcional)."""
    if h is None:
        return None
    if not isinstance(h, dict):
        raise ValueError("'shortcut_hints' must be an object")
    out = {"enabled": bool(h.get("enabled", True)), "effect": h.get("effect", "solid")}
    if out["effect"] not in HINT_EFFECTS:
        raise ValueError(f"'shortcut_hints.effect' must be one of {', '.join(HINT_EFFECTS)}")
    from . import color as C
    if "color" in h:
        out["color"] = C.to_hex(C.parse(h["color"]))
    if "colors" in h:
        cs = h["colors"]
        if not isinstance(cs, list) or not 1 <= len(cs) <= 8:
            raise ValueError("'shortcut_hints.colors' must be a list of 1 to 8 colors")
        out["colors"] = [C.to_hex(C.parse(c)) for c in cs]
    for name, (lo, hi) in HINT_RANGES.items():
        if name in h:
            try:
                v = float(h[name])
            except (TypeError, ValueError):
                raise ValueError(f"'shortcut_hints.{name}' must be a number") from None
            out[name] = min(hi, max(lo, v))
    return out


@dataclass
class Profile:
    name: str
    layers: list[dict]
    author: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    designed_for: str = ""
    brightness: float = 1.0
    shortcut_hints: dict | None = None

    @classmethod
    def from_dict(cls, d: dict) -> Profile:
        if d.get("format", FORMAT) != FORMAT:
            raise ValueError(f"Unsupported format: {d.get('format')}")
        layers = d.get("layers")
        if not isinstance(layers, list) or not layers:
            raise ValueError("A profile needs at least one layer in 'layers'")
        for i, layer in enumerate(layers):
            if layer.get("effect") not in REGISTRY:
                raise ValueError(f"Layer {i}: unknown effect {layer.get('effect')!r}. "
                                 f"Available: {', '.join(REGISTRY)}")
            if layer.get("blend", "normal") not in BLENDS:
                raise ValueError(f"Layer {i}: blend must be one of {BLENDS}")
        return cls(
            name=d.get("name", "Untitled"),
            layers=layers,
            author=d.get("author", ""),
            description=d.get("description", ""),
            tags=list(d.get("tags", [])),
            designed_for=d.get("designed_for", ""),
            brightness=float(d.get("brightness", 1.0)),
            shortcut_hints=_hints_config(d.get("shortcut_hints")),
        )

    def to_dict(self) -> dict:
        d = {"format": FORMAT, "name": self.name}
        for attr in ("author", "description", "tags", "designed_for"):
            if getattr(self, attr):
                d[attr] = getattr(self, attr)
        if self.brightness != 1.0:
            d["brightness"] = self.brightness
        if self.shortcut_hints is not None:
            d["shortcut_hints"] = self.shortcut_hints
        d["layers"] = self.layers
        return d

    @classmethod
    def load(cls, path: str | Path) -> Profile:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")


class Renderer:
    """Calcula el color de cada tecla de ``layout`` en el instante ``t``."""

    def __init__(self, profile: Profile, layout: Layout):
        self.profile = profile
        self.layout = layout
        self.ctx = []
        for k in layout.keys:
            u, v = layout.norm(k)
            self.ctx.append(KeyCtx(k.id, u, v, k.cx, k.cy))
        self.layers: list[tuple[Effect, set[str] | None, float, str]] = []
        for layer in profile.layers:
            eff = REGISTRY[layer["effect"]](layer.get("params", {}), layout)
            keys = resolve_keys(layer["keys"], layout) if "keys" in layer else None
            self.layers.append((eff, keys, float(layer.get("opacity", 1.0)),
                                layer.get("blend", "normal")))

    def frame(self, t: float) -> dict[str, tuple[int, int, int]]:
        out = {}
        bright = self.profile.brightness
        for k in self.ctx:
            acc = (0.0, 0.0, 0.0)
            for eff, keys, a, blend in self.layers:
                if keys is not None and k.id not in keys:
                    continue
                c = eff.color(k, t)
                if c is None:
                    continue
                alpha = a
                if len(c) == 4:  # algunos efectos devuelven (r, g, b, transparencia)
                    alpha, c = a * c[3], c[:3]
                acc = _blend(acc, c, alpha, blend)
            out[k.id] = C.to_bytes(C.scale(acc, bright))
        return out


def _blend(base, c, a, mode):
    if mode == "add":
        mixed = tuple(min(1.0, b + x) for b, x in zip(base, c))
    elif mode == "multiply":
        mixed = tuple(b * x for b, x in zip(base, c))
    elif mode == "screen":
        mixed = tuple(1 - (1 - b) * (1 - x) for b, x in zip(base, c))
    else:
        mixed = c
    return C.lerp(base, mixed, a)
