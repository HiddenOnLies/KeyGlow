"""Importación de perfiles desde distintos formatos.

Soportado:
- Perfiles KeyGlow (``.json`` con ``layers``).
- Perfiles de OpenRGB: ``.json`` (OpenRGB 1.0+) y ``.orp`` (versiones anteriores).
- Mapas de colores por tecla en JSON, en cualquiera de estas formas::

      {"Escape": "#ff0000", "Key: Left Control": [0, 0, 255], ...}
      [{"key": "KeyW", "color": "#ff0000"}, {"led": "Key: A", "color": "#0f0"}]
      {"name": "Mi perfil", "keys": {...}}

  Los nombres de tecla se reconocen en estilo OpenRGB, códigos web
  (``KeyboardEvent.code``), QMK (``KC_A``), Linux y nombres comunes.
- CSV con columnas ``tecla,color``.
- URLs http(s) a cualquiera de los anteriores (``fetch``).
"""

from __future__ import annotations

import csv
import io
import json
import urllib.request
from pathlib import Path

from .formats import openrgb
from .profile import Profile

MAX_DOWNLOAD = 2 * 1024 * 1024


def _keymap_profile(name: str, keys: dict, designed_for: str = "") -> Profile:
    return Profile(name=name, designed_for=designed_for,
                   layers=[{"effect": "static", "params": {"keys": keys}}])


def from_json_data(data, name: str = "Importado") -> Profile:
    if isinstance(data, dict) and "layers" in data:
        return Profile.from_dict(data)
    if isinstance(data, dict) and isinstance(data.get("controllers"), list):
        return openrgb.to_profile(json.dumps(data).encode("utf-8"), name)
    if isinstance(data, dict) and isinstance(data.get("keys"), dict):
        return _keymap_profile(data.get("name", name), data["keys"], data.get("layout", ""))
    if isinstance(data, dict):
        return _keymap_profile(name, data)
    if isinstance(data, list):
        keys = {}
        for item in data:
            k = item.get("key") or item.get("name") or item.get("led") or item.get("id")
            c = item.get("color") or item.get("colour") or item.get("rgb")
            if k is None or c is None:
                raise ValueError(f"Entry without a key or color: {item}")
            keys[k] = c
        return _keymap_profile(name, keys)
    raise ValueError("This JSON is neither a profile nor a key color map")


def from_csv_text(text: str, name: str = "Importado") -> Profile:
    keys = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 2 or row[0].strip().lower() in ("key", "tecla", "#"):
            continue
        keys[row[0].strip()] = row[1].strip()
    return _keymap_profile(name, keys)


def from_bytes(data: bytes, filename: str) -> Profile:
    """Detecta el formato por el contenido y la extensión de ``filename``."""
    name = Path(filename).stem.removesuffix(".openrgb") or "Imported"
    if data.startswith(b"OPENRGB_PROFILE") or filename.lower().endswith(".orp"):
        return openrgb.to_profile(data, name)
    text = data.decode("utf-8-sig")
    if filename.lower().endswith(".csv"):
        return from_csv_text(text, name)
    return from_json_data(json.loads(text), name)


def load_any(path: str) -> Profile:
    if path.startswith(("http://", "https://")):
        return fetch(path)
    p = Path(path)
    return from_bytes(p.read_bytes(), p.name)


def fetch(url: str) -> Profile:
    """Descarga un perfil de una URL. Solo se aceptan datos (JSON/CSV/OpenRGB), nunca código."""
    req = urllib.request.Request(url, headers={"User-Agent": "keyglow/0.1"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read(MAX_DOWNLOAD + 1)
    if len(raw) > MAX_DOWNLOAD:
        raise ValueError("The downloaded file is too large to be a profile")
    filename = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1] or "Downloaded.json"
    return from_bytes(raw, filename)
