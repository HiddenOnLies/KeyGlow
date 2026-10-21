"""Geometría física de los teclados.

Las posiciones se miden en "u" (1u = ancho de una tecla normal). Con la geometría
podemos aplicar cualquier efecto espacial (ondas, degradados, imágenes) a cualquier
teclado, y rellenar teclas que no existían en el teclado original por proximidad.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import keynames
from .keynames import DIGITS, LETTERS


@dataclass(frozen=True)
class Key:
    id: str
    x: float
    y: float
    w: float = 1.0
    h: float = 1.0

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def label(self) -> str:
        return keynames.label(self.id)


class Layout:
    def __init__(self, name: str, title: str, keys: list[Key]):
        self.name = name
        self.title = title
        self.keys = keys
        self._by_id = {k.id: k for k in keys}
        self.width = max(k.x + k.w for k in keys)
        self.height = max(k.y + k.h for k in keys)

    def __contains__(self, key_id: str) -> bool:
        return key_id in self._by_id

    def __len__(self) -> int:
        return len(self.keys)

    def get(self, key_id: str) -> Key | None:
        return self._by_id.get(key_id)

    @property
    def ids(self) -> list[str]:
        return [k.id for k in self.keys]

    def norm(self, key: Key) -> tuple[float, float]:
        """Centro de la tecla normalizado a [0, 1] en ambos ejes."""
        return key.cx / self.width, key.cy / self.height

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "keys": [{"id": k.id, "x": k.x, "y": k.y, "w": k.w, "h": k.h} for k in self.keys],
        }

    @classmethod
    def from_dict(cls, d: dict) -> Layout:
        keys = [Key(k["id"], k["x"], k["y"], k.get("w", 1.0), k.get("h", 1.0)) for k in d["keys"]]
        return cls(d["name"], d.get("title", d["name"]), keys)


def _build(rows: list[tuple[float, list]]) -> list[Key]:
    """Construye teclas a partir de filas ``(y, items)``.

    Cada item es ``"ID"`` (1u), ``("ID", ancho)``, ``("ID", ancho, alto)`` o un
    número, que representa un hueco de ese ancho.
    """
    keys = []
    for y, items in rows:
        x = 0.0
        for item in items:
            if isinstance(item, (int, float)):
                x += item
                continue
            if isinstance(item, str):
                item = (item,)
            key_id, w, h = (*item, 1.0, 1.0)[:3]
            keys.append(Key(key_id, x, y, w, h))
            x += w
    return keys


_NUM_ROW = ["GRAVE", *DIGITS, "MINUS", "EQUAL", ("BACKSPACE", 2)]
_TOP_ROW = [("TAB", 1.5), *"QWERTYUIOP", "LBRACKET", "RBRACKET", ("BACKSLASH", 1.5)]
_HOME_ROW = [("CAPSLOCK", 1.75), *"ASDFGHJKL", "SEMICOLON", "QUOTE", ("ENTER", 2.25)]
_BOTTOM_ROW = ["Z", "X", "C", "V", "B", "N", "M", "COMMA", "PERIOD", "SLASH"]


def _ansi_full() -> Layout:
    rows = [
        (0, ["ESC", 1, "F1", "F2", "F3", "F4", 0.5, "F5", "F6", "F7", "F8", 0.5,
             "F9", "F10", "F11", "F12", 0.25, "PRINTSCREEN", "SCROLLLOCK", "PAUSE"]),
        (1.25, [*_NUM_ROW, 0.25, "INSERT", "HOME", "PAGE_UP", 0.25,
                "NUMLOCK", "NUM_SLASH", "NUM_ASTERISK", "NUM_MINUS"]),
        (2.25, [*_TOP_ROW, 0.25, "DELETE", "END", "PAGE_DOWN", 0.25,
                "NUM_7", "NUM_8", "NUM_9", ("NUM_PLUS", 1, 2)]),
        (3.25, [*_HOME_ROW, 3.5, "NUM_4", "NUM_5", "NUM_6"]),
        (4.25, [("LSHIFT", 2.25), *_BOTTOM_ROW, ("RSHIFT", 2.75), 1.25, "UP", 1.25,
                "NUM_1", "NUM_2", "NUM_3", ("NUM_ENTER", 1, 2)]),
        (5.25, [("LCTRL", 1.25), ("LWIN", 1.25), ("LALT", 1.25), ("SPACE", 6.25),
                ("RALT", 1.25), ("RWIN", 1.25), ("MENU", 1.25), ("RCTRL", 1.25), 0.25,
                "LEFT", "DOWN", "RIGHT", 0.25, ("NUM_0", 2), "NUM_PERIOD"]),
    ]
    return Layout("ansi_full", "ANSI 100% (104 keys)", _build(rows))


def _ansi_60() -> Layout:
    rows = [
        (0, ["ESC", *_NUM_ROW[1:]]),
        (1, _TOP_ROW),
        (2, _HOME_ROW),
        (3, [("LSHIFT", 2.25), *_BOTTOM_ROW, ("RSHIFT", 2.75)]),
        (4, [("LCTRL", 1.25), ("LWIN", 1.25), ("LALT", 1.25), ("SPACE", 6.25),
             ("RALT", 1.25), ("FN", 1.25), ("MENU", 1.25), ("RCTRL", 1.25)]),
    ]
    return Layout("ansi_60", "ANSI 60% (61 keys)", _build(rows))


def _alloy_origins_65() -> Layout:
    # Columna derecha según la matriz que OpenRGB 1.1 reporta para la unidad real
    # (03f0:038f): Home, Delete, PgUp, PgDn. Si tu unidad difiere, exporta el layout
    # con `keyglow layout alloy_origins_65 --json`, corrígelo y cárgalo con --layout.
    rows = [
        (0, ["ESC", *_NUM_ROW[1:], "HOME"]),
        (1, [*_TOP_ROW, "DELETE"]),
        (2, [*_HOME_ROW, "PAGE_UP"]),
        (3, [("LSHIFT", 2.25), *_BOTTOM_ROW, ("RSHIFT", 1.75), "UP", "PAGE_DOWN"]),
        (4, [("LCTRL", 1.25), ("LWIN", 1.25), ("LALT", 1.25), ("SPACE", 6.25),
             "RALT", "FN", "RCTRL", "LEFT", "DOWN", "RIGHT"]),
    ]
    return Layout("alloy_origins_65", "HyperX Alloy Origins 65 (ANSI, 68 keys)", _build(rows))


BUILTIN = {f.__name__.lstrip("_"): f for f in (_alloy_origins_65, _ansi_60, _ansi_full)}

# Grupos portables: un perfil puede decir "@wasd" y funciona en cualquier teclado.
GROUPS = {
    "wasd": ["W", "A", "S", "D"],
    "arrows": ["UP", "DOWN", "LEFT", "RIGHT"],
    "fn_row": [f"F{i}" for i in range(1, 13)],
    "letters": LETTERS,
    "numbers": DIGITS,
    "numpad": [f"NUM_{d}" for d in DIGITS] + [
        "NUMLOCK", "NUM_SLASH", "NUM_ASTERISK", "NUM_MINUS", "NUM_PLUS", "NUM_ENTER", "NUM_PERIOD"],
    "modifiers": ["LSHIFT", "RSHIFT", "LCTRL", "RCTRL", "LALT", "RALT", "LWIN", "RWIN",
                  "FN", "MENU", "CAPSLOCK", "TAB"],
    "nav": ["INSERT", "HOME", "PAGE_UP", "DELETE", "END", "PAGE_DOWN",
            "PRINTSCREEN", "SCROLLLOCK", "PAUSE"],
}


def resolve_keys(selectors: list[str], layout: Layout) -> set[str]:
    """Convierte ``["@wasd", "SPACE", "Left Control"]`` en ids presentes en el layout."""
    out: set[str] = set()
    for sel in selectors:
        if sel == "@all":
            out.update(layout.ids)
        elif sel.startswith("@"):
            if sel[1:] not in GROUPS:
                raise ValueError(f"Unknown group: {sel}. Available: @all, "
                                 + ", ".join("@" + g for g in GROUPS))
            out.update(GROUPS[sel[1:]])
        else:
            out.add(keynames.normalize(sel) or sel)
    return {k for k in out if k in layout}


def load_layout(name_or_path: str) -> Layout:
    if name_or_path in BUILTIN:
        return BUILTIN[name_or_path]()
    p = Path(name_or_path)
    if p.suffix == ".json" and p.exists():
        return Layout.from_dict(json.loads(p.read_text(encoding="utf-8")))
    raise ValueError(f"Unknown layout: {name_or_path}. Available: {', '.join(BUILTIN)}")
