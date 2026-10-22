"""Geometría física de los teclados.

Las posiciones se miden en "u" (1u = ancho de una tecla normal). Con la geometría
podemos aplicar cualquier efecto espacial (ondas, degradados, imágenes) a cualquier
teclado, y rellenar teclas que no existían en el teclado original por proximidad.
"""

from __future__ import annotations

import json
import re
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
    def __init__(self, name: str, title: str, keys: list[Key], source: str = "", usb: str = ""):
        self.name = name
        self.title = title
        self.keys = keys
        # de dónde sale: "model" (exacta para ese modelo), "standard:<n>", "adapted:<n>", "matrix"
        self.source = source
        self.usb = usb  # VID:PID del teclado del que se obtuvo, si se sabe
        self.verified: bool | None = None  # para distribuciones de modelo: probada en hardware
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
        out = {
            "name": self.name,
            "title": self.title,
            "keys": [{"id": k.id, "x": k.x, "y": k.y, "w": k.w, "h": k.h} for k in self.keys],
        }
        if self.source:
            out["source"] = self.source
        if self.usb:
            out["usb"] = self.usb
        if self.verified is not None:
            out["verified"] = self.verified
        return out

    @classmethod
    def from_dict(cls, d: dict) -> Layout:
        keys = [Key(k["id"], k["x"], k["y"], k.get("w", 1.0), k.get("h", 1.0)) for k in d["keys"]]
        return cls(d["name"], d.get("title", d["name"]), keys, d.get("source", ""), d.get("usb", ""))


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


# ISO: Enter alto de dos filas, tecla "#" junto a él y "\" junto a Shift izquierdo
_ISO_TOP_ROW = [("TAB", 1.5), *"QWERTYUIOP", "LBRACKET", "RBRACKET", 0.25, ("ENTER", 1.25, 2)]
_ISO_HOME_ROW = [("CAPSLOCK", 1.75), *"ASDFGHJKL", "SEMICOLON", "QUOTE", "NONUS_HASH"]
_ISO_SHIFT = [("LSHIFT", 1.25), "NONUS_BACKSLASH"]
_F_ROW = ["ESC", 1, "F1", "F2", "F3", "F4", 0.5, "F5", "F6", "F7", "F8", 0.5,
          "F9", "F10", "F11", "F12"]
_MODS_ROW = [("LCTRL", 1.25), ("LWIN", 1.25), ("LALT", 1.25), ("SPACE", 6.25),
             ("RALT", 1.25), ("RWIN", 1.25), ("MENU", 1.25), ("RCTRL", 1.25)]


def _full(iso: bool, numpad: bool) -> list[Key]:
    """Teclado completo (con o sin numpad) en ANSI o ISO."""
    top, home = (_ISO_TOP_ROW, _ISO_HOME_ROW) if iso else (_TOP_ROW, _HOME_ROW)
    shift = _ISO_SHIFT if iso else [("LSHIFT", 2.25)]

    def pad(*items):
        return [0.25, *items] if numpad else []

    # la fila central ISO acaba antes (el Enter viene de la fila de arriba)
    home_gap = 3.5 + (1.25 if iso else 0)
    rows = [
        (0, [*_F_ROW, 0.25, "PRINTSCREEN", "SCROLLLOCK", "PAUSE"]),
        (1.25, [*_NUM_ROW, 0.25, "INSERT", "HOME", "PAGE_UP",
                *pad("NUMLOCK", "NUM_SLASH", "NUM_ASTERISK", "NUM_MINUS")]),
        (2.25, [*top, 0.25, "DELETE", "END", "PAGE_DOWN",
                *pad("NUM_7", "NUM_8", "NUM_9", ("NUM_PLUS", 1, 2))]),
        (3.25, [*home, *([home_gap, "NUM_4", "NUM_5", "NUM_6"] if numpad else [])]),
        (4.25, [*shift, *_BOTTOM_ROW, ("RSHIFT", 2.75), 1.25, "UP",
                *([1.25, "NUM_1", "NUM_2", "NUM_3", ("NUM_ENTER", 1, 2)] if numpad else [])]),
        (5.25, [*_MODS_ROW, 0.25, "LEFT", "DOWN", "RIGHT", *pad(("NUM_0", 2), "NUM_PERIOD")]),
    ]
    return _build(rows)


def _ansi_full() -> Layout:
    return Layout("ansi_full", "ANSI 100% (104 keys)", _full(iso=False, numpad=True))


def _ansi_tkl() -> Layout:
    return Layout("ansi_tkl", "ANSI TKL 80% (87 keys)", _full(iso=False, numpad=False))


def _iso_full() -> Layout:
    return Layout("iso_full", "ISO 100% (105 keys)", _full(iso=True, numpad=True))


def _iso_tkl() -> Layout:
    return Layout("iso_tkl", "ISO TKL 80% (88 keys)", _full(iso=True, numpad=False))


def _ansi_75() -> Layout:
    rows = [
        (0, ["ESC", *[f"F{i}" for i in range(1, 13)], "PRINTSCREEN", "DELETE"]),
        (1, [*_NUM_ROW, "HOME"]),
        (2, [*_TOP_ROW, "PAGE_UP"]),
        (3, [*_HOME_ROW, "PAGE_DOWN"]),
        (4, [("LSHIFT", 2.25), *_BOTTOM_ROW, ("RSHIFT", 1.75), "UP", "END"]),
        (5, [("LCTRL", 1.25), ("LWIN", 1.25), ("LALT", 1.25), ("SPACE", 6.25),
             "RALT", "FN", "RCTRL", "LEFT", "DOWN", "RIGHT"]),
    ]
    return Layout("ansi_75", "ANSI 75% (83 keys)", _build(rows))


def _ansi_65() -> Layout:
    rows = [
        (0, ["ESC", *_NUM_ROW[1:], "DELETE"]),
        (1, [*_TOP_ROW, "PAGE_UP"]),
        (2, [*_HOME_ROW, "PAGE_DOWN"]),
        (3, [("LSHIFT", 2.25), *_BOTTOM_ROW, ("RSHIFT", 1.75), "UP", "END"]),
        (4, [("LCTRL", 1.25), ("LWIN", 1.25), ("LALT", 1.25), ("SPACE", 6.25),
             "RALT", "FN", "RCTRL", "LEFT", "DOWN", "RIGHT"]),
    ]
    return Layout("ansi_65", "ANSI 65% (68 keys)", _build(rows))


def _sixty(iso: bool) -> list[Key]:
    rows = [
        (0, ["ESC", *_NUM_ROW[1:]]),
        (1, _ISO_TOP_ROW if iso else _TOP_ROW),
        (2, _ISO_HOME_ROW if iso else _HOME_ROW),
        (3, [*(_ISO_SHIFT if iso else [("LSHIFT", 2.25)]), *_BOTTOM_ROW, ("RSHIFT", 2.75)]),
        (4, [("LCTRL", 1.25), ("LWIN", 1.25), ("LALT", 1.25), ("SPACE", 6.25),
             ("RALT", 1.25), ("FN", 1.25), ("MENU", 1.25), ("RCTRL", 1.25)]),
    ]
    return _build(rows)


def _ansi_60() -> Layout:
    return Layout("ansi_60", "ANSI 60% (61 keys)", _sixty(iso=False))


def _iso_60() -> Layout:
    return Layout("iso_60", "ISO 60% (62 keys)", _sixty(iso=True))


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


BUILTIN = {f.__name__.lstrip("_"): f for f in (
    _alloy_origins_65, _ansi_60, _ansi_65, _ansi_75, _ansi_tkl, _ansi_full,
    _iso_60, _iso_tkl, _iso_full)}

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


# ---------------------------------------------------------------------------
# Distribución automática a partir de lo que informa el dispositivo (OpenRGB)
# ---------------------------------------------------------------------------
# Distribuciones exactas de modelos concretos. Vienen de dos sitios:
# - keyglow/layouts/*.json, incluidas en la app;
# - el workshop (repositorio KeyGlow-layouts), que la app descarga y guarda en caché
#   (keyglow.app.layout_sync pone aquí lo descargado).
# Formato: {"title", "usb": ["vvvv:pppp"], "names": [...], "verified": bool,
#           "builtin": "<nombre>" o "keys": [{"id", "x", "y", "w", "h"}, ...]}
MODELS_DIR = Path(__file__).resolve().parent / "layouts"
WORKSHOP_MODELS: list[dict] = []

_USB_RE = re.compile(r"^[0-9a-f]{4}:[0-9a-f]{4}$")
_KEY_ID_RE = re.compile(r"^[A-Z0-9_]{1,24}$")


def validate_model(d: dict) -> dict:
    """Comprueba una distribución de modelo (solo datos) y la devuelve normalizada.

    Lanza ``ValueError`` con el motivo si algo no encaja: así una distribución mal hecha
    del workshop se descarta en vez de romper el dibujo del teclado.
    """
    if not isinstance(d, dict):
        raise ValueError("a layout must be a JSON object")
    title = d.get("title")
    if not isinstance(title, str) or not 0 < len(title) <= 100:
        raise ValueError("'title' must be a short text")
    usb = d.get("usb", [])
    names = d.get("names", [])
    if not isinstance(usb, list) or not all(isinstance(u, str) and _USB_RE.match(u.lower()) for u in usb):
        raise ValueError("'usb' must be a list like [\"03f0:038f\"]")
    if not isinstance(names, list) or len(names) > 10 or             not all(isinstance(n, str) and 0 < len(n) <= 100 for n in names):
        raise ValueError("'names' must be a list of short texts")
    if not usb and not names:
        raise ValueError("a layout needs 'usb' or 'names' to recognize the keyboard")
    out = {"title": title, "usb": [u.lower() for u in usb], "names": names,
           "verified": bool(d.get("verified", False))}
    if "name" in d:
        out["name"] = str(d["name"])[:64]
    if "builtin" in d:
        if d["builtin"] not in BUILTIN:
            raise ValueError(f"unknown built-in layout {d['builtin']!r}")
        out["builtin"] = d["builtin"]
        return out
    keys = d.get("keys")
    if not isinstance(keys, list) or not 1 <= len(keys) <= 300:
        raise ValueError("'keys' must be a list of 1 to 300 keys")
    seen, clean = set(), []
    for k in keys:
        if not isinstance(k, dict) or not isinstance(k.get("id"), str) or not _KEY_ID_RE.match(k["id"]):
            raise ValueError(f"bad key: {k!r}")
        if k["id"] in seen:
            raise ValueError(f"key {k['id']} appears twice")
        seen.add(k["id"])
        try:
            x, y = float(k["x"]), float(k["y"])
            w, h = float(k.get("w", 1)), float(k.get("h", 1))
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"key {k['id']} needs numeric x and y") from None
        if not (0 <= x <= 60 and 0 <= y <= 20 and 0.25 <= w <= 12 and 0.25 <= h <= 6):
            raise ValueError(f"key {k['id']} is out of range")
        clean.append({"id": k["id"], "x": x, "y": y, "w": w, "h": h})
    out["keys"] = clean
    return out


def _models() -> list[dict]:
    out = []
    for f in sorted(MODELS_DIR.glob("*.json")):
        try:
            d = validate_model(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
        d.setdefault("name", f.stem)
        out.append({**d, "origin": "bundled"})
    for d in WORKSHOP_MODELS:
        try:
            out.append({**validate_model(d), "name": d.get("name", ""), "origin": "workshop"})
        except ValueError:
            continue
    return out


def model_layout(usb: str = "", name: str = "") -> Layout | None:
    """La distribución exacta de ese modelo, si está en la base de datos (incluida o workshop).

    El identificador USB manda sobre el nombre. Si dos distribuciones encajan igual, gana la
    verificada en hardware real y, después, la del workshop (más reciente que la incluida).
    """
    usb, name = usb.lower(), name.lower()
    best, best_rank = None, None
    for d in _models():
        score = 1000 if usb and usb in d["usb"] else             max((len(n) for n in d["names"] if name and n.lower() in name), default=0)
        rank = (score, d["verified"], d["origin"] == "workshop")
        if score and (best_rank is None or rank > best_rank):
            best, best_rank = d, rank
    if best is None:
        return None
    source = "model:workshop" if best["origin"] == "workshop" else "model"
    if "builtin" in best:
        base = BUILTIN[best["builtin"]]()
        lay = Layout(base.name, best["title"], base.keys, source, usb)
    else:
        keys = [Key(k["id"], k["x"], k["y"], k["w"], k["h"]) for k in best["keys"]]
        lay = Layout(best.get("name") or "model", best["title"], keys, source, usb)
    lay.verified = best["verified"]
    return lay


def from_device(title: str, led_names: list[str],
                matrix: list[list[int | None]] | None = None, usb: str = "") -> Layout:
    """Construye la distribución de un teclado concreto.

    ``led_names`` son los nombres de sus LEDs (``"Key: Left Control"``...) y ``matrix``
    la cuadrícula filas x columnas con el índice de LED de cada celda (o ``None``),
    tal como la da OpenRGB. Por orden de preferencia:

    1. La distribución exacta del modelo (``usb`` = ``"vvvv:pppp"`` o por nombre).
    2. La distribución estándar que mejor encaja, recortada a sus teclas; las teclas que
       la matriz pone en otra fila se recolocan, y las que no existen en ella (multimedia,
       macros...) se colocan según la matriz.
    3. La cuadrícula de la matriz tal cual, si el teclado no se parece a ninguna.
    """
    exact = model_layout(usb, title)
    if exact is not None:
        return exact
    ids = [keynames.normalize(n) if n.strip() else None for n in led_names]
    have = {k for k in ids if k}
    if not have:
        raise ValueError(f"{title}: no LED looks like a key")
    cells = _matrix_cells(ids, matrix)

    def score(lay: Layout) -> tuple:
        lay_ids = set(lay.ids)
        return (3 * len(have - lay_ids) + len(lay_ids - have), lay.name != "alloy_origins_65")

    best = min((f() for f in BUILTIN.values()), key=score)
    common = have & set(best.ids)
    if len(common) < 0.6 * len(have):
        if not cells:
            raise ValueError(f"{title}: unknown key arrangement and no matrix to build it from")
        return Layout("device", title, _grid_keys(cells), "matrix", usb)
    keys = [k for k in best.keys if k.id in have]
    moved = _fix_rows(keys, cells)
    missing = have - common
    # Si solo faltan un par de teclas (p. ej. una sin LED propio), se deja la distribución
    # completa: esas teclas se ven apagadas, pero el dibujo sigue siendo el del teclado.
    if not missing and not moved and len(best) - len(keys) <= 3:
        return Layout(best.name, best.title, best.keys, f"standard:{best.name}", usb)
    keys += _place_extras(best, keys, cells, missing)
    return Layout("device", title, _shift_to_origin(keys), f"adapted:{best.name}", usb)


def _fix_rows(keys: list[Key], cells) -> int:
    """Recoloca (en ``keys``) las teclas que la matriz pone en otra fila que la distribución
    estándar, junto a sus vecinas de esa fila. Devuelve cuántas ha movido."""
    if not cells:
        return 0
    row_of = {k.id: min(r for r, _ in cells[k.id]) for k in keys if k.id in cells}
    col_of = {k.id: min(c for r, c in cells[k.id] if r == row_of[k.id]) for k in keys if k.id in cells}
    # altura (y) de cada fila de la matriz: la que tienen la mayoría de sus teclas
    row_y: dict[int, float] = {}
    for r in set(row_of.values()):
        ys = [k.y for k in keys if row_of.get(k.id) == r]
        if len(ys) >= 3:
            row_y[r] = max(set(ys), key=ys.count)
    wrong = [k for k in keys if k.id in row_of and row_of[k.id] in row_y
             and abs(k.y - row_y[row_of[k.id]]) > 0.3 and k.h <= 1]
    # todas a la vez: dos teclas intercambiadas no deben estorbarse en su sitio antiguo
    fixed = [o for o in keys if o not in wrong]
    placed: dict[str, Key] = {}
    for k in wrong:
        r = row_of[k.id]
        same = sorted((o for o in fixed if row_of.get(o.id) == r), key=lambda o: col_of[o.id])
        left = [o for o in same if col_of[o.id] < col_of[k.id]]
        right = [o for o in same if col_of[o.id] > col_of[k.id]]
        candidates = ([left[-1].x + left[-1].w] if left else []) + ([right[0].x - 1] if right else [])
        for x in candidates:
            new = Key(k.id, x, row_y[r])
            if not any(_overlaps(new, o) for o in [*fixed, *placed.values()]):
                placed[k.id] = new
                break
    for i, k in enumerate(keys):
        keys[i] = placed.get(k.id, k)
    return len(placed)


def _matrix_cells(ids: list[str | None], matrix) -> dict[str, list[tuple[int, int]]]:
    """``{id: [(fila, columna), ...]}`` según la matriz (una tecla puede ocupar varias)."""
    cells: dict[str, list[tuple[int, int]]] = {}
    for r, row in enumerate(matrix or []):
        for c, led in enumerate(row):
            if led is not None and 0 <= led < len(ids) and ids[led]:
                cells.setdefault(ids[led], []).append((r, c))
    return cells


def _fit(pairs: list[tuple[float, float]]) -> tuple[float, float]:
    """Recta ``y = a*x + b`` por mínimos cuadrados (con al menos dos puntos distintos)."""
    n = len(pairs)
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    var = sum((p[0] - mx) ** 2 for p in pairs)
    a = sum((p[0] - mx) * (p[1] - my) for p in pairs) / var if var else 1.0
    return a, my - a * mx


def _place_extras(base: Layout, keys: list[Key], cells, missing: set[str]) -> list[Key]:
    known = [(k, cells[k.id]) for k in keys if k.id in cells]
    if len(known) < 2:
        return []
    ax, bx = _fit([(sum(c for _, c in cs) / len(cs), k.cx) for k, cs in known])
    ay, by = _fit([(sum(r for r, _ in cs) / len(cs), k.cy) for k, cs in known])
    placed: list[Key] = []
    taken = list(keys)
    for kid in sorted(missing, key=lambda i: cells.get(i, [(99, 99)])[0]):
        if kid not in cells:
            continue
        r = sum(r for r, _ in cells[kid]) / len(cells[kid])
        c = sum(c for _, c in cells[kid]) / len(cells[kid])
        key = Key(kid, ax * c + bx - 0.5, ay * r + by - 0.5)
        # si cae encima de otra tecla, se sube a una fila nueva por encima
        while any(_overlaps(key, o) for o in taken):
            key = Key(kid, key.x, min(o.y for o in taken) - 1.25)
        placed.append(key)
        taken.append(key)
    return placed


def _overlaps(a: Key, b: Key) -> bool:
    e = 1e-6
    return a.x < b.x + b.w - e and b.x < a.x + a.w - e and a.y < b.y + b.h - e and b.y < a.y + a.h - e


def _shift_to_origin(keys: list[Key]) -> list[Key]:
    x0 = min(k.x for k in keys)
    y0 = min(k.y for k in keys)
    return [Key(k.id, k.x - x0, k.y - y0, k.w, k.h) for k in keys]


def _grid_keys(cells) -> list[Key]:
    """Distribución de cuadrícula pura: cada tecla ocupa sus celdas de la matriz."""
    keys = []
    for kid, cs in cells.items():
        rows = {r for r, _ in cs}
        r = min(rows)
        cols = sorted(c for rr, c in cs if rr == r)
        keys.append(Key(kid, float(cols[0]), float(r), float(cols[-1] - cols[0] + 1), float(len(rows))))
    return _shift_to_origin(sorted(keys, key=lambda k: (k.y, k.x)))
