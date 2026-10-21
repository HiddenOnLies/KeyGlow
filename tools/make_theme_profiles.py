"""Genera perfiles de la galería a partir de temas de colores con licencia MIT.

Uso: python tools/make_theme_profiles.py
Descarga los repositorios de origen, escribe ``keyglow/community/themes/*.json``,
actualiza las entradas ``themes/`` de ``keyglow/community/index.json`` (las demás se
conservan) y escribe ``keyglow/community/themes/CREDITS.md`` con la atribución y el
texto de cada licencia.

Fuentes (todas MIT):
- Catppuccin       https://github.com/catppuccin/palette
- Dracula          https://github.com/dracula/dracula-theme
- Nord             https://github.com/nordtheme/nord
- Tinted Theming   https://github.com/tinted-theming/schemes (esquemas base16)
"""

from __future__ import annotations

import colorsys
import io
import json
import re
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "keyglow" / "community"
THEMES = OUT / "themes"
PREFIX = "themes/"  # entradas del índice generadas por este script

SOURCES = {
    "catppuccin": ("catppuccin/palette", "main"),
    "dracula": ("dracula/dracula-theme", "main"),
    "nord": ("nordtheme/nord", "develop"),
    "tinted": ("tinted-theming/schemes", "spec-0.11"),
}
# temas que ya llegan de su repositorio oficial: no se repiten desde base16
OFFICIAL = ("catppuccin", "dracula", "nord")


def fetch(repo: str, branch: str) -> dict[str, bytes]:
    """Descarga un repositorio de GitHub y devuelve {ruta: contenido} de sus archivos."""
    url = f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}"
    with urllib.request.urlopen(url, timeout=120) as r:
        data = r.read()
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for m in tar.getmembers():
            if m.isfile():
                files[m.name.split("/", 1)[1]] = tar.extractfile(m).read()
    return files


def license_text(files: dict[str, bytes]) -> str:
    for name in ("LICENSE", "license", "LICENSE.md", "license.md"):
        if name in files:
            return files[name].decode("utf-8").strip()
    raise ValueError("License file not found")


def led(hex_color: str, floor: float = 0.8) -> str:
    """Sube el brillo de colores apagados para que se vean en un LED sin cambiar el tono."""
    r, g, b = (int(hex_color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(h, s, max(v, floor))
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def clean_author(author: str) -> str:
    """Quita correos y enlaces para mostrarlo en la app (la versión completa va a los créditos)."""
    author = re.sub(r"<[^>]*>|\([^)]*\)|https?://\S+", "", author)
    author = re.sub(r"\s+([,;])", r"\1", re.sub(r"\s+", " ", author))
    return author.strip(" ,;") or "Unknown"


# ---------------------------------------------------------------------------
# Perfiles
# ---------------------------------------------------------------------------
def code_profile(name: str, author: str, source: str, p: dict) -> dict:
    """Perfil fijo al estilo de un editor: degradado del tema y grupos de teclas resaltados.

    ``p`` usa los nombres de base16: blue, magenta, cyan, yellow, green, red, orange.
    """
    c = {k: led(v) for k, v in p.items()}
    return {
        "format": "keyglow/1",
        "name": name,
        "author": f"{author} · {source} (MIT)",
        "description": f"Colors from the {name} theme by {author}. MIT License.",
        "tags": ["theme", "static"],
        "layers": [
            {"effect": "gradient", "params": {"colors": [c["blue"], c["magenta"]], "angle": 0}},
            {"effect": "solid", "params": {"color": c["yellow"]}, "keys": ["@numbers"]},
            {"effect": "solid", "params": {"color": c["cyan"]}, "keys": ["@modifiers"]},
            {"effect": "solid", "params": {"color": c["green"]}, "keys": ["@arrows", "@nav"]},
            {"effect": "solid", "params": {"color": c["red"]}, "keys": ["ESC"]},
            {"effect": "solid", "params": {"color": c["orange"]}, "keys": ["@wasd"]},
        ],
    }


def wave_profile(name: str, author: str, source: str, colors: list[str]) -> dict:
    return {
        "format": "keyglow/1",
        "name": f"{name} Wave",
        "author": f"{author} · {source} (MIT)",
        "description": f"The accent colors of the {name} theme by {author}, rolling slowly. MIT License.",
        "tags": ["theme", "animated"],
        "layers": [
            {"effect": "color_wave", "params": {"colors": [led(x) for x in colors], "speed": 0.08, "wavelength": 1.4}},
        ],
    }


def catppuccin(files) -> list[tuple[dict, str]]:
    pal = json.loads(files["palette.json"])
    out = []
    for flavor in ("latte", "frappe", "macchiato", "mocha"):
        f = pal[flavor]
        col = {k: v["hex"] for k, v in f["colors"].items()}
        name = f"Catppuccin {f['name']}"
        p = {"blue": col["blue"], "magenta": col["mauve"], "cyan": col["sky"], "yellow": col["yellow"],
             "green": col["green"], "red": col["red"], "orange": col["peach"]}
        out.append((code_profile(name, "Catppuccin", "Catppuccin", p), "catppuccin"))
        wave = [col[k] for k in ("mauve", "pink", "flamingo", "peach", "yellow", "green", "teal", "sapphire", "lavender")]
        out.append((wave_profile(name, "Catppuccin", "Catppuccin", wave), "catppuccin"))
    return out


def dracula(files) -> list[tuple[dict, str]]:
    # la primera tabla del README es la paleta oscura (la segunda es Alucard, la clara)
    text = files["README.md"].decode("utf-8")
    col = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*([A-Za-z ]+?)\s*\|\s*`(#[0-9a-fA-F]{6})`", line)
        if m:
            col.setdefault(m.group(1).lower(), m.group(2))
        elif col and not line.strip():
            break
    p = {"blue": col["purple"], "magenta": col["pink"], "cyan": col["cyan"], "yellow": col["yellow"],
         "green": col["green"], "red": col["red"], "orange": col["orange"]}
    wave = [col[k] for k in ("purple", "pink", "red", "orange", "yellow", "green", "cyan")]
    return [(code_profile("Dracula", "Dracula Theme", "Dracula", p), "dracula"),
            (wave_profile("Dracula", "Dracula Theme", "Dracula", wave), "dracula")]


def nord(files) -> list[tuple[dict, str]]:
    css = files["src/nord.css"].decode("utf-8")
    n = {int(i): v for i, v in re.findall(r"--nord(\d+):\s*(#[0-9a-fA-F]{6})", css)}
    p = {"blue": n[10], "magenta": n[15], "cyan": n[8], "yellow": n[13],
         "green": n[14], "red": n[11], "orange": n[12]}
    wave = [n[i] for i in (7, 8, 9, 10, 15, 11, 12, 13, 14)]
    return [(code_profile("Nord", "Sven Greb", "Nord", p), "nord"),
            (wave_profile("Nord", "Sven Greb", "Nord", wave), "nord")]


def tinted(files) -> tuple[list[tuple[dict, str]], list[tuple[str, str]]]:
    """Esquemas base16 oscuros; los claros comparten acentos con su versión oscura."""
    out, credits, seen = [], [], set()
    for path in sorted(files):
        if not (path.startswith("base16/") and path.endswith(".yaml")):
            continue
        text = files[path].decode("utf-8")
        field = lambda k: (re.search(rf'^{k}:\s*"?(.*?)"?\s*$', text, re.M) or [None, ""])[1]
        if field("variant") == "light":
            continue
        name, author = field("name"), field("author")
        if any(o in name.lower() for o in OFFICIAL):
            continue
        base = {k.lower(): v.lower() for k, v in re.findall(r'(base0[0-9A-Fa-f]):\s*"?(#?[0-9a-fA-F]{6})', text)}
        base = {k: v if v.startswith("#") else "#" + v for k, v in base.items()}
        p = {"red": base["base08"], "orange": base["base09"], "yellow": base["base0a"], "green": base["base0b"],
             "cyan": base["base0c"], "blue": base["base0d"], "magenta": base["base0e"]}
        key = tuple(led(v) for v in p.values())
        if key in seen or len(set(key)) < 3:  # repetidos o casi monocromos
            continue
        seen.add(key)
        out.append((code_profile(name, clean_author(author), "Tinted Theming", p), "tinted"))
        credits.append((name, author))
    return out, credits


# ---------------------------------------------------------------------------
def main() -> int:
    repos = {k: fetch(*v) for k, v in SOURCES.items()}
    profiles = catppuccin(repos["catppuccin"]) + dracula(repos["dracula"]) + nord(repos["nord"])
    base16, base16_credits = tinted(repos["tinted"])
    profiles += base16

    THEMES.mkdir(exist_ok=True)
    for old in THEMES.glob("*.json"):
        old.unlink()
    entries, used = [], set()
    for prof, _src in profiles:
        name = slug(prof["name"])
        while name in used:
            name += "-2"
        used.add(name)
        file = f"{PREFIX}{name}.json"
        (OUT / file).write_text(json.dumps(prof, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        entries.append({k: prof[k] for k in ("name", "author", "description", "tags")} | {"file": file})

    index_path = OUT / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    keep = [e for e in index["profiles"] if not str(e.get("file", "")).startswith(PREFIX)]
    index["profiles"] = keep + entries
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Theme credits",
        "",
        "The profiles in this folder are generated by `tools/make_theme_profiles.py`",
        "from the color palettes below. Colors are brightened where needed so they show on LEDs.",
        "Each source is used under the MIT License, reproduced in full at the end of this file.",
        "",
        "| Source | Profiles | Repository |",
        "|---|---|---|",
    ]
    counts = {s: sum(1 for _, src in profiles if src == s) for s in SOURCES}
    for key, (repo, _branch) in SOURCES.items():
        lines.append(f"| {key.capitalize()} | {counts[key]} | https://github.com/{repo} |")
    lines += ["", "## Base16 schemes (Tinted Theming)", "", "| Scheme | Author |", "|---|---|"]
    lines += [f"| {n} | {a.replace('|', '/')} |" for n, a in base16_credits]
    lines += ["", "## Licenses"]
    for key, (repo, _branch) in SOURCES.items():
        lines += ["", f"### {repo}", "", "```", license_text(repos[key]), "```"]
    (THEMES / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"{len(profiles)} profiles: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
