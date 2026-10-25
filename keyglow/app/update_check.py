"""Aviso de versión nueva: mira las releases de KeyGlow en GitHub, como mucho una vez al día.

Solo se descarga la lista de releases (sin datos del PC, aparte de la versión en el
User-Agent) y se guarda el resultado; KeyGlow nunca se actualiza solo, solo avisa con un
enlace a la página de la release.
"""

from __future__ import annotations

import json
import re
import time
import urllib.request

from .. import __version__
from . import library

RELEASES_URL = "https://api.github.com/repos/HiddenOnLies/KeyGlow/releases?per_page=10"
CHECK_EVERY = 24 * 3600
MAX_BYTES = 1024 * 1024


def _cache_file():
    return library.app_data_dir() / "update-check.json"


def version_tuple(v: str) -> tuple[int, ...]:
    """``"v0.10.2"`` -> ``(0, 10, 2)``; lo que no sea número se ignora."""
    return tuple(int(n) for n in re.findall(r"\d+", v.split("-")[0].split("+")[0])[:3])


def newest(releases: list) -> dict | None:
    """La release publicada (no borrador) con la versión más alta."""
    ok = [r for r in releases if isinstance(r, dict) and not r.get("draft") and r.get("tag_name")]
    return max(ok, key=lambda r: version_tuple(r["tag_name"]), default=None)


def load() -> dict:
    try:
        data = json.loads(_cache_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def status(skipped: str = "") -> dict:
    """Lo último comprobado: ``{"current", "latest", "url", "newer", "checked", "error"}``."""
    data = load()
    latest = data.get("latest", "")
    newer = bool(latest) and version_tuple(latest) > version_tuple(__version__)
    return {"current": __version__, "latest": latest, "url": data.get("url", ""), "checked": data.get("checked", 0),
            "newer": newer, "skipped": bool(newer and skipped and version_tuple(skipped) >= version_tuple(latest)),
            "error": data.get("error", "")}


def check(force: bool = False, url: str = RELEASES_URL, skipped: str = "") -> dict:
    """Pregunta a GitHub si hace más de un día (o ``force``). Un fallo no borra lo que se sabía."""
    data = load()
    if not force and time.time() - data.get("checked", 0) < CHECK_EVERY:
        return status(skipped)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"KeyGlow/{__version__}",
                                                   "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("The release list is too large")
        rel = newest(json.loads(raw.decode("utf-8")))
        data = {"checked": time.time(), "latest": rel["tag_name"] if rel else "",
                "url": rel.get("html_url", "") if rel else "", "error": ""}
    except (OSError, ValueError, TypeError, AttributeError) as e:
        data = {**data, "checked": time.time(), "error": str(e)}
    _cache_file().write_text(json.dumps(data), encoding="utf-8")
    return status(skipped)
