"""Biblioteca de perfiles: predeterminados, los del usuario y los de la comunidad.

- Predeterminados: ``keyglow/presets/*.json`` (vienen con la app).
- Mis perfiles: ``Documentos/KeyGlow/Perfiles`` (archivos JSON normales, se pueden
  copiar, compartir o editar a mano).
- Comunidad: la galería oficial (repositorio KeyGlow-profiles, ver
  ``keyglow.app.gallery_sync``) o un índice JSON en otra URL (configurable). Formato del índice::

      {"format": "keyglow-gallery/1", "name": "...",
       "profiles": [{"name": "...", "author": "...", "tags": [...],
                     "url": "neon.json"}            # relativa al índice o absoluta
                    {"name": "...", "profile": {...}}]}  # o el perfil incrustado

Los perfiles son siempre datos (JSON), nunca código.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from .. import __version__
from ..importers import MAX_DOWNLOAD
from ..profile import Profile

PACKAGE_DIR = Path(__file__).resolve().parent.parent
PRESETS_DIR = PACKAGE_DIR / "presets"
COMMUNITY_DIR = PACKAGE_DIR / "community"

DEFAULT_SETTINGS = {
    "brightness": 1.0,
    "caps_lock": "auto",  # encender Bloq Mayús: "auto" (si el teclado no tiene piloto), "on", "off"
    "caps_lock_color": "#ffffff",
    "shortcut_hints": True,  # al mantener Ctrl, Alt o Win, iluminar las teclas de sus atajos
    "shortcut_hints_color": "#ffffff",
    "fps": 30,
    "community_url": "",
    "apply_last_on_start": True,
    "last_profile": None,
    "openrgb_host": "127.0.0.1",
    "openrgb_port": 6742,
    "openrgb_device": "",
    "openrgb_path": "",  # OpenRGB.exe, si no está en la carpeta habitual
    "start_openrgb": True,
    "layout_updates": True,  # descargar distribuciones del workshop (KeyGlow-layouts)
    "gallery_updates": True,  # descargar perfiles nuevos de la galería (KeyGlow-profiles)
    "layouts_url": "",  # vacío = el workshop oficial  # abrir OpenRGB (minimizado, con el servidor) si no está en marcha  # parte del nombre del teclado, si OpenRGB ve más de uno
    "layout": "auto",  # "auto" = la distribución que informa OpenRGB, o un nombre de BUILTIN
    "device_layout": None,  # última distribución detectada, para arrancar sin esperar
    "game_switching": True,
    "auto_games": False,  # usar el preset recomendado en juegos conocidos sin perfil propio
    # [{"exe": "cs2.exe", "name": "Counter-Strike 2", "profile_id": "preset:fps_red"}]
    "game_rules": [],
}


def _documents_dir() -> Path:
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            # CSIDL_PERSONAL = 5: respeta la carpeta Documentos movida a OneDrive
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0:
                return Path(buf.value)
        except (AttributeError, OSError):
            pass
    return Path.home() / "Documents"


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA")
    d = Path(base) / "KeyGlow" if base else Path.home() / ".keyglow"
    d.mkdir(parents=True, exist_ok=True)
    return d


def user_profiles_dir() -> Path:
    d = _documents_dir() / "KeyGlow" / "Perfiles"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- ajustes -----------------------------------------------------------------

def load_settings() -> dict:
    path = app_data_dir() / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return {**DEFAULT_SETTINGS, **{k: v for k, v in data.items() if k in DEFAULT_SETTINGS}}


def save_settings(settings: dict) -> dict:
    merged = {**load_settings(), **{k: v for k, v in settings.items() if k in DEFAULT_SETTINGS}}
    path = app_data_dir() / "settings.json"
    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return merged


# --- perfiles ----------------------------------------------------------------

def _entry(kind: str, path: Path, data: dict) -> dict:
    return {
        "id": f"{kind}:{path.stem}",
        "kind": kind,
        "name": data.get("name", path.stem),
        "author": data.get("author", ""),
        "description": data.get("description", ""),
        "tags": data.get("tags", []),
        "data": data,
    }


def _read_dir(kind: str, folder: Path) -> list[dict]:
    out = []
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.json")):
        if path.name == "index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            Profile.from_dict(data)
        except (OSError, ValueError, AttributeError, TypeError):
            continue  # un archivo roto no debe tumbar la biblioteca
        out.append(_entry(kind, path, data))
    return out


def presets() -> list[dict]:
    items = _read_dir("preset", PRESETS_DIR)
    order = ["aurora", "rainbow", "gaming_wasd"]
    items.sort(key=lambda e: (order.index(e["id"][7:]) if e["id"][7:] in order else 99,
                              e["name"].lower()))
    return items


def mine() -> list[dict]:
    return _read_dir("mine", user_profiles_dir())


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s[:60] or "profile"


def save_mine(data: dict, overwrite_id: str | None = None) -> dict:
    Profile.from_dict(data)  # valida
    folder = user_profiles_dir()
    if overwrite_id and overwrite_id.startswith("mine:"):
        stem = slugify(overwrite_id[5:])
    else:
        stem, n = slugify(data.get("name", "profile")), 2
        base = stem
        while (folder / f"{stem}.json").exists():
            stem, n = f"{base}_{n}", n + 1
    path = folder / f"{stem}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return _entry("mine", path, data)


def resolve(profile_id: str) -> dict | None:
    """Devuelve el perfil ``preset:xxx`` o ``mine:xxx``, o None si ya no existe."""
    kind, _, stem = profile_id.partition(":")
    folder = {"preset": PRESETS_DIR, "mine": user_profiles_dir()}.get(kind)
    if folder is None or not stem:
        return None
    try:
        return json.loads((folder / f"{slugify(stem)}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def delete_mine(profile_id: str) -> None:
    if not profile_id.startswith("mine:"):
        raise ValueError("Only your own profiles can be deleted")
    path = user_profiles_dir() / f"{slugify(profile_id[5:])}.json"
    if path.exists():
        path.unlink()


# --- comunidad ---------------------------------------------------------------

def _download(url: str) -> bytes:
    if not url.startswith(("https://", "http://")):
        raise ValueError("The link must start with http:// or https://")
    req = urllib.request.Request(url, headers={"User-Agent": f"keyglow-app/{__version__}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read(MAX_DOWNLOAD + 1)
    if len(raw) > MAX_DOWNLOAD:
        raise ValueError("The downloaded file is too large")
    return raw


def community(url: str) -> dict:
    """Descarga una galería que no es la oficial (un índice en ``url``)."""
    index = json.loads(_download(url).decode("utf-8"))
    source = url
    items = []
    for i, item in enumerate(index.get("profiles", [])):
        if not isinstance(item, dict):
            continue
        entry = {
            "id": f"community:{i}",
            "kind": "community",
            "name": item.get("name", f"Profile {i + 1}"),
            "author": item.get("author", ""),
            "description": item.get("description", ""),
            "tags": item.get("tags", []),
            "data": None,
            "url": None,
        }
        if isinstance(item.get("profile"), dict):
            entry["data"] = item["profile"]
        elif item.get("url"):
            entry["url"] = urllib.parse.urljoin(url, item["url"])
        else:
            continue
        items.append(entry)
    return {"name": index.get("name", "Community"), "source": source, "profiles": items}


def fetch_profile_json(url: str) -> dict:
    return json.loads(_download(url).decode("utf-8"))
