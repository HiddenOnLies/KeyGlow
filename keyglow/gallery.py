"""Galería de la comunidad (repositorio KeyGlow-profiles).

El repositorio guarda un perfil por archivo (``profiles/*.json``) y un único
``gallery.json`` con todos, que es lo que descarga la app. Este módulo comprueba los
perfiles y arma ese archivo; la descarga y la caché están en ``keyglow.app.gallery_sync``.
Formato::

    {"format": "keyglow-gallery/1", "name": "...", "generated": "AAAA-MM-DD",
     "profiles": [{"id": "nebula", "name": "...", "author": "...", "description": "...",
                   "tags": [...], "profile": {...}}]}

Los perfiles son siempre datos (JSON), nunca código.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

from .layout import load_layout
from .profile import Profile, Renderer

FORMAT = "keyglow-gallery/1"
NAME = "KeyGlow community"
MAX_PROFILES = 500
MAX_PROFILE_BYTES = 64 * 1024
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
# efectos que leen archivos del PC: no tienen sentido en perfiles compartidos
_LOCAL_ONLY = {"image"}


def _text(d: dict, key: str, limit: int) -> str:
    v = d.get(key, "")
    if not isinstance(v, str) or len(v) > limit:
        raise ValueError(f"'{key}' must be a text of up to {limit} characters")
    return v


def validate_profile(d: dict, pid: str = "") -> dict:
    """Comprueba un perfil de la galería y devuelve su entrada normalizada.

    Lanza ``ValueError`` con el motivo si algo no encaja.
    """
    if not isinstance(d, dict):
        raise ValueError("a profile must be a JSON object")
    if len(json.dumps(d)) > MAX_PROFILE_BYTES:
        raise ValueError("the profile is too large")
    if pid and not _ID_RE.match(pid):
        raise ValueError(f"bad id {pid!r}: use lowercase letters, digits and dashes")
    try:
        profile = Profile.from_dict(d)
        local = sorted({layer.get("effect") for layer in d["layers"]} & _LOCAL_ONLY)
        if not local:
            Renderer(profile, load_layout("ansi_full")).frame(0.5)  # parámetros y colores válidos
    except (AttributeError, KeyError, TypeError) as e:
        raise ValueError(f"malformed profile ({e})") from None
    if not 0 < len(profile.name) <= 60:
        raise ValueError("'name' must be a short text")
    if local:
        raise ValueError(f"effect {local[0]!r} reads files on your PC and can't be shared")
    tags = d.get("tags", [])
    if not isinstance(tags, list) or len(tags) > 8 or not all(isinstance(t, str) and 0 < len(t) <= 24 for t in tags):
        raise ValueError("'tags' must be a list of up to 8 short texts")
    return {"id": pid, "name": profile.name, "author": _text(d, "author", 100),
            "description": _text(d, "description", 300), "tags": tags, "profile": d}


def parse(raw: bytes) -> list[dict]:
    """Las entradas válidas de un ``gallery.json`` (las inválidas se descartan)."""
    doc = json.loads(raw.decode("utf-8"))
    if not isinstance(doc, dict) or doc.get("format") != FORMAT or not isinstance(doc.get("profiles"), list):
        raise ValueError("Not a KeyGlow gallery file")
    out = []
    for item in doc["profiles"][:MAX_PROFILES]:
        try:
            out.append(validate_profile(item.get("profile"), str(item.get("id", ""))))
        except (AttributeError, ValueError):
            continue
    return out


def check(paths: list[str]) -> tuple[list[dict], list[str]]:
    """Comprueba los archivos (o carpetas) y devuelve ``(entradas válidas, errores)``."""
    files = sorted(f for p in paths for f in (Path(p).glob("*.json") if Path(p).is_dir() else [Path(p)]))
    good, errors = [], []
    for f in files:
        try:
            good.append(validate_profile(json.loads(f.read_text(encoding="utf-8")), f.stem))
        except (OSError, ValueError) as e:
            errors.append(f"{f.name}: {e}")
    names = [e["name"].lower() for e in good]
    errors += [f"two profiles are called {n!r}" for n in sorted({n for n in names if names.count(n) > 1})]
    return good, errors


def bundle(entries: list[dict]) -> dict:
    return {"format": FORMAT, "name": NAME, "generated": datetime.date.today().isoformat(),
            "profiles": sorted(entries, key=lambda e: e["name"].lower())}
