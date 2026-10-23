"""Galería de la comunidad (repositorio KeyGlow-profiles).

Igual que las distribuciones del workshop: se descarga **un único archivo** con todos los
perfiles, como mucho una vez al día, se guarda en caché y sin conexión se usa la caché o,
si no hay, la copia incluida en la app. Todo se valida antes de usarlo.
"""

from __future__ import annotations

import json
import time
import urllib.request

from .. import __version__
from .. import gallery
from . import library

DEFAULT_URL = "https://raw.githubusercontent.com/HiddenOnLies/KeyGlow-profiles/main/gallery.json"
BUNDLED = library.COMMUNITY_DIR / "gallery.json"
MAX_BYTES = 4 * 1024 * 1024
REFRESH_EVERY = 24 * 3600


def _cache_file():
    return library.app_data_dir() / "community-gallery.json"


def load_cache() -> dict:
    """``{"fetched": epoch, "profiles": [...]}`` guardado, o vacío."""
    try:
        data = json.loads(_cache_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and isinstance(data.get("profiles"), list) else {}
    except (OSError, ValueError):
        return {}


def current() -> tuple[list[dict], float]:
    """Los perfiles a mostrar y cuándo se descargaron (0 = la copia incluida en la app)."""
    cache = load_cache()
    if cache.get("profiles"):
        return cache["profiles"], cache.get("fetched", 0)
    try:
        return gallery.parse(BUNDLED.read_bytes()), 0
    except (OSError, ValueError):
        return [], 0


def refresh(url: str = DEFAULT_URL, force: bool = False) -> dict:
    """Descarga la galería si la caché tiene más de un día (o ``force``).

    Devuelve ``{"updated": bool, "count": n, "fetched": epoch, "error": str}``. Si falla la
    descarga, se sigue usando lo que hubiera.
    """
    cache = load_cache()
    fetched = cache.get("fetched", 0)
    if not force and time.time() - fetched < REFRESH_EVERY:
        return {"updated": False, "count": len(current()[0]), "fetched": fetched, "error": ""}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"KeyGlow/{__version__}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("The gallery file is too large")
        profiles = gallery.parse(raw)
    except (OSError, ValueError) as e:
        return {"updated": False, "count": len(current()[0]), "fetched": fetched, "error": str(e)}
    cache = {"fetched": time.time(), "url": url, "profiles": profiles}
    _cache_file().write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return {"updated": True, "count": len(profiles), "fetched": cache["fetched"], "error": ""}


def listing() -> dict:
    """La galería en el formato de la biblioteca (pestaña *Community* de la app)."""
    profiles, fetched = current()
    items = [{"id": f"community:{p['id'] or i}", "kind": "community", "name": p["name"],
              "author": p["author"], "description": p["description"], "tags": p["tags"],
              "data": p["profile"], "url": None} for i, p in enumerate(profiles)]
    return {"name": gallery.NAME, "source": "", "fetched": fetched, "profiles": items}
