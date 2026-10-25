"""Distribuciones hechas con el editor de KeyGlow, guardadas en el PC del usuario.

Son distribuciones de modelo como las del workshop (mismo formato y misma validación), pero
viven en ``%APPDATA%/KeyGlow/layouts`` y tienen prioridad sobre las incluidas y las del
workshop: si alguien corrige la de su teclado, se usa la suya.
"""

from __future__ import annotations

import json
import re

from .. import layout as L
from .. import keynames
from ..layout import Key, _overlaps, validate_model
from . import library


def folder():
    d = library.app_data_dir() / "layouts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load() -> int:
    """Pone las distribuciones guardadas a disposición de ``layout.model_layout``."""
    models = []
    for f in sorted(folder().glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            models.append({**validate_model(d), "name": d.get("name") or f.stem})
        except (OSError, ValueError):
            continue
    L.LOCAL_MODELS[:] = models
    return len(models)


def save(title: str, keys: list[dict], usb: str = "", device: str = "") -> str:
    """Guarda la distribución de ``device`` y devuelve su nombre para elegirla (``model:...``).

    Lanza ``ValueError`` si falta algo o hay teclas montadas unas sobre otras.
    """
    title = (title or device or "My keyboard").strip()[:100]
    model = {"title": title, "usb": [usb.lower()] if usb else [], "names": [device] if device else [title],
             "verified": True, "verified_on": "Made with KeyGlow's layout editor", "keys": keys}
    clean = validate_model(model)
    placed = [Key(k["id"], k["x"], k["y"], k["w"], k["h"]) for k in clean["keys"]]
    clash = [f"{a.id}/{b.id}" for i, a in enumerate(placed) for b in placed[i + 1:] if _overlaps(a, b)]
    if clash:
        raise ValueError(f"Some keys overlap: {', '.join(clash[:4])}")
    name = "local-" + (re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "keyboard")[:50]
    (folder() / f"{name}.json").write_text(json.dumps({**model, "name": name, "keys": clean["keys"]}, indent=1) + "\n",
                                           encoding="utf-8")
    load()
    return f"model:{name}"


def known_keys() -> list[dict]:
    """Todas las teclas que KeyGlow conoce, para añadirlas en el editor."""
    ids = set(keynames.LABELS)
    for build in L.BUILTIN.values():
        ids.update(build().ids)
    return sorted(({"id": k, "label": keynames.label(k)} for k in ids), key=lambda k: k["id"])
