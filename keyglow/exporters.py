"""Exportación de perfiles a formatos que entienden otros programas.

Los demás programas no tienen capas ni efectos portables, así que lo que se exporta
es una "foto": los colores de cada tecla en un instante del perfil (``at`` segundos).

Formatos (``FORMATS``):
- ``keyglow``: el perfil KeyGlow completo (con sus animaciones).
- ``openrgb``: perfil de OpenRGB (``.json``, OpenRGB 1.0+) para el teclado indicado.
- ``keys-openrgb`` / ``keys-web`` / ``keys-qmk``: mapa ``{tecla: "#rrggbb"}`` con los
  nombres de tecla de OpenRGB, de los navegadores (``KeyboardEvent.code``) o de QMK.
- ``csv``: ``key,color`` (nombres de OpenRGB), para hojas de cálculo u otras herramientas.
"""

from __future__ import annotations

import csv
import io
import json
import re

from .formats import openrgb
from .keynames import external_name
from .layout import Layout
from .profile import Profile, Renderer

FORMATS = {
    "keyglow": "KeyGlow profile (.json, keeps animations)",
    "openrgb": "OpenRGB profile (.json, OpenRGB 1.0+)",
    "keys-openrgb": "Key colors with OpenRGB key names (.json)",
    "keys-web": "Key colors with web key codes (.json)",
    "keys-qmk": "Key colors with QMK keycodes (.json)",
    "csv": "Key colors as CSV (key,color)",
}


def snapshot(profile: Profile, layout: Layout, at: float = 0.0) -> dict[str, tuple[int, int, int]]:
    """Colores de cada tecla del ``layout`` en el instante ``at``."""
    return Renderer(profile, layout).frame(at)


def _hex(c: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % c


def filename(profile: Profile, fmt: str) -> str:
    stem = re.sub(r"[^\w\- ]+", "", profile.name or "profile").strip().replace(" ", "_") or "profile"
    if fmt == "csv":
        return f"{stem}.csv"
    if fmt == "openrgb":
        return f"{stem}.openrgb.json"
    if fmt.startswith("keys-"):
        return f"{stem}.{fmt[5:]}-keys.json"
    return f"{stem}.json"


def export(profile: Profile, layout: Layout, fmt: str, at: float = 0.0,
           device: dict | None = None) -> str:
    """Devuelve el contenido del archivo en el formato ``fmt``.

    Para ``openrgb``, ``device`` es la descripción del teclado real (sin ella se usa una
    genérica, que OpenRGB solo aplicará si su teclado se llama igual).
    """
    if fmt not in FORMATS:
        raise ValueError(f"Unknown export format: {fmt}. Available: {', '.join(FORMATS)}")
    if fmt == "keyglow":
        return json.dumps(profile.to_dict(), indent=2, ensure_ascii=False) + "\n"
    frame = snapshot(profile, layout, at)
    if fmt == "openrgb":
        doc = openrgb.export(profile.name, frame, device or openrgb.generic_device(layout))
        return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    style = "openrgb" if fmt == "csv" else fmt[5:]
    rows = [(external_name(k, style), _hex(frame[k])) for k in layout.ids if k in frame]
    if fmt == "csv":
        out = io.StringIO()
        w = csv.writer(out, lineterminator="\n")
        w.writerow(["key", "color"])
        w.writerows(rows)
        return out.getvalue()
    return json.dumps(dict(rows), indent=2, ensure_ascii=False) + "\n"
