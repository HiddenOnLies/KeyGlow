"""Distribuciones de teclado del workshop (repositorio KeyGlow-layouts).

Se descarga **un único archivo con todas las distribuciones** y se busca en local, así que
el servidor nunca sabe qué teclado tiene nadie. Se guarda en caché y se renueva como mucho
una vez al día; sin conexión se usa la caché y, si no hay, las distribuciones incluidas en
la app. Todo son datos (JSON) que se validan antes de usarlos, nunca código.
"""

from __future__ import annotations

import json
import time
import urllib.request

from .. import __version__
from .. import layout as L
from . import library

DEFAULT_URL = "https://raw.githubusercontent.com/HiddenOnLies/KeyGlow-layouts/main/layouts.json"
FORMAT = "keyglow-layouts/1"
MAX_BYTES = 2 * 1024 * 1024
REFRESH_EVERY = 24 * 3600


def _cache_file():
    return library.app_data_dir() / "workshop-layouts.json"


def parse(raw: bytes) -> list[dict]:
    """Las distribuciones válidas de un archivo del workshop (las inválidas se descartan)."""
    doc = json.loads(raw.decode("utf-8"))
    if not isinstance(doc, dict) or doc.get("format") != FORMAT or not isinstance(doc.get("layouts"), list):
        raise ValueError("Not a KeyGlow layouts file")
    out = []
    for d in doc["layouts"]:
        try:
            out.append({**L.validate_model(d), "name": str(d.get("name", ""))[:64]})
        except ValueError:
            continue
    return out


def load_cache() -> dict:
    """``{"fetched": epoch, "layouts": [...]}`` guardado, o vacío."""
    try:
        data = json.loads(_cache_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def use_cache() -> int:
    """Pone las distribuciones de la caché a disposición de ``layout.model_layout``."""
    L.WORKSHOP_MODELS[:] = load_cache().get("layouts", [])
    return len(L.WORKSHOP_MODELS)


def refresh(url: str = DEFAULT_URL, force: bool = False) -> dict:
    """Descarga el workshop si la caché tiene más de un día (o ``force``).

    Devuelve ``{"updated": bool, "count": n, "fetched": epoch, "error": str}``. Si falla la
    descarga, se sigue usando lo que hubiera en caché.
    """
    cache = load_cache()
    fetched = cache.get("fetched", 0)
    if not force and time.time() - fetched < REFRESH_EVERY:
        return {"updated": False, "count": use_cache(), "fetched": fetched, "error": ""}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"KeyGlow/{__version__}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("The layouts file is too large")
        layouts = parse(raw)
    except (OSError, ValueError) as e:
        return {"updated": False, "count": use_cache(), "fetched": fetched, "error": str(e)}
    cache = {"fetched": time.time(), "url": url, "layouts": layouts}
    _cache_file().write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return {"updated": True, "count": use_cache(), "fetched": cache["fetched"], "error": ""}


def status() -> dict:
    cache = load_cache()
    return {"count": len(cache.get("layouts", [])), "fetched": cache.get("fetched", 0)}
