"""Atajos de teclado que se iluminan al mantener Ctrl, Alt o Win.

Los atajos están en ``shortcuts.json``: un juego para Windows (``default``) y otros para
aplicaciones concretas por su ejecutable. Los de la aplicación activa se suman a los de
Windows (Ctrl+C sigue sirviendo en el navegador). Los de la tecla Win son siempre los de Windows.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent / "shortcuts.json"
ORDER = ("ctrl", "shift", "alt", "win")
# teclas que forman cada modificador (para iluminar también las que se mantienen)
MOD_KEYS = {"ctrl": ("LCTRL", "RCTRL"), "shift": ("LSHIFT", "RSHIFT"), "alt": ("LALT", "RALT"),
            "win": ("LWIN", "RWIN")}


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def combo(mods) -> str:
    """``{"shift", "ctrl"}`` -> ``"ctrl+shift"``. Vacío con Shift solo, que sirve para escribir.
    (AltGr, que Windows ve como Ctrl+Alt, lo descarta antes ``keyhook.held_modifiers``.)"""
    mods = set(mods)
    if not mods or mods == {"shift"}:
        return ""
    return "+".join(m for m in ORDER if m in mods)


def app_name(exe: str) -> str:
    app = _app(exe)
    return app.get("name", "") if app else ""


def _app(exe: str) -> dict | None:
    apps = _data()["apps"]
    app = apps.get(exe.lower())
    if app and "same_as" in app:
        app = apps.get(app["same_as"])
    return app


def keys_for(mods, exe: str = "") -> list[str]:
    """Las teclas a iluminar al mantener ``mods`` con ``exe`` en primer plano."""
    c = combo(mods)
    if not c:
        return []
    app = _app(exe) if "win" not in c else None
    keys = list((app or {}).get(c, [])) + _data()["default"].get(c, [])
    return list(dict.fromkeys(keys))  # sin repetir, primero los de la aplicación
