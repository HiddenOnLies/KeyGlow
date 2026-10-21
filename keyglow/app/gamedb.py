"""Juegos conocidos, su género y el preset recomendado, y búsqueda de juegos instalados.

La recomendación es opcional (Settings > Game profiles): si está activa y el juego en
primer plano está en esta lista y el usuario no le asignó un perfil, se usa el preset
de su género. Detectar los instalados solo lee carpetas y manifiestos locales de
Steam, Epic Games y Riot; no se conecta a nada.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

GENRE_PRESET = {
    "fps": "preset:fps_red",
    "moba": "preset:moba",
    "battle_royale": "preset:battle_royale",
    "racing": "preset:racing",
    "rpg": "preset:rpg",
    "survival": "preset:stealth",
    "cyberpunk": "preset:neon_city",
    "sandbox": "preset:forest",
    "horror": "preset:halloween",
    "sports": "preset:aurora",
}
GENRE_NAMES = {
    "fps": "Shooter", "moba": "MOBA", "battle_royale": "Battle royale", "racing": "Racing",
    "rpg": "RPG", "survival": "Survival", "cyberpunk": "Cyberpunk", "sandbox": "Sandbox",
    "horror": "Horror", "sports": "Sports",
}

# name, executables, genre, carpeta de instalación en Steam (si aplica)
_GAMES = [
    ("Counter-Strike 2", ["cs2.exe"], "fps", "Counter-Strike Global Offensive"),
    ("VALORANT", ["valorant-win64-shipping.exe"], "fps", None),
    ("Overwatch 2", ["overwatch.exe"], "fps", "Overwatch"),
    ("Rainbow Six Siege", ["rainbowsix.exe", "rainbowsix_vulkan.exe"], "fps", "Tom Clancy's Rainbow Six Siege"),
    ("Call of Duty", ["cod.exe", "cod24-cod.exe", "cod25-cod.exe"], "fps", "Call of Duty HQ"),
    ("Battlefield 2042", ["bf2042.exe"], "fps", "Battlefield 2042"),
    ("Team Fortress 2", ["tf_win64.exe", "hl2.exe"], "fps", "Team Fortress 2"),
    ("DOOM Eternal", ["doometernalx64vk.exe"], "fps", "DOOMEternal"),
    ("Halo Infinite", ["haloinfinite.exe"], "fps", "Halo Infinite"),
    ("The Finals", ["discovery.exe"], "fps", "THE FINALS"),
    ("Destiny 2", ["destiny2.exe"], "fps", "Destiny 2"),
    ("Deadlock", ["deadlock.exe", "project8.exe"], "moba", "Deadlock"),
    ("League of Legends", ["league of legends.exe"], "moba", None),
    ("Dota 2", ["dota2.exe"], "moba", "dota 2 beta"),
    ("SMITE 2", ["hemingway-win64-shipping.exe"], "moba", "SMITE 2"),
    ("Fortnite", ["fortniteclient-win64-shipping.exe"], "battle_royale", None),
    ("Apex Legends", ["r5apex.exe", "r5apex_dx12.exe"], "battle_royale", "Apex Legends"),
    ("PUBG: Battlegrounds", ["tslgame.exe"], "battle_royale", "PUBG"),
    ("Warzone", ["cod.exe"], "battle_royale", None),
    ("Rocket League", ["rocketleague.exe"], "sports", "rocketleague"),
    ("EA SPORTS FC", ["fc25.exe", "fc26.exe"], "sports", None),
    ("Forza Horizon 5", ["forzahorizon5.exe"], "racing", "ForzaHorizon5"),
    ("Assetto Corsa Competizione", ["ac2-win64-shipping.exe"], "racing", "Assetto Corsa Competizione"),
    ("F1 25", ["f1_25.exe"], "racing", "F1 25"),
    ("Elden Ring", ["eldenring.exe"], "rpg", "ELDEN RING"),
    ("Baldur's Gate 3", ["bg3.exe", "bg3_dx11.exe"], "rpg", "Baldurs Gate 3"),
    ("The Witcher 3", ["witcher3.exe"], "rpg", "The Witcher 3"),
    ("Path of Exile 2", ["pathofexile_x64steam.exe", "pathofexile_x64.exe"], "rpg", "Path of Exile 2"),
    ("Diablo IV", ["diablo iv.exe"], "rpg", "Diablo IV"),
    ("Genshin Impact", ["genshinimpact.exe"], "rpg", None),
    ("World of Warcraft", ["wow.exe"], "rpg", None),
    ("Monster Hunter Wilds", ["monsterhunterwilds.exe"], "rpg", "MonsterHunterWilds"),
    ("Cyberpunk 2077", ["cyberpunk2077.exe"], "cyberpunk", "Cyberpunk 2077"),
    ("Rust", ["rustclient.exe"], "survival", "Rust"),
    ("Escape from Tarkov", ["escapefromtarkov.exe"], "survival", None),
    ("DayZ", ["dayz_x64.exe"], "survival", "DayZ"),
    ("Valheim", ["valheim.exe"], "survival", "Valheim"),
    ("Minecraft", ["minecraft.windows.exe"], "sandbox", None),
    ("Terraria", ["terraria.exe"], "sandbox", "Terraria"),
    ("Grand Theft Auto V", ["gta5.exe", "gta5_enhanced.exe"], "racing", "Grand Theft Auto V"),
    ("Phasmophobia", ["phasmophobia.exe"], "horror", "Phasmophobia"),
    ("Dead by Daylight", ["deadbydaylight-win64-shipping.exe"], "horror", "Dead by Daylight"),
    ("Lethal Company", ["lethal company.exe"], "horror", "Lethal Company"),
]

KNOWN: list[dict] = [
    {"name": n, "exes": e, "genre": g, "steam_dir": s, "profile_id": GENRE_PRESET[g]}
    for n, e, g, s in _GAMES
]
_BY_EXE = {exe: g for g in KNOWN for exe in g["exes"]}
_BY_STEAM = {g["steam_dir"].lower(): g for g in KNOWN if g["steam_dir"]}


def lookup(exe: str) -> dict | None:
    """El juego conocido cuyo ejecutable es ``exe`` (en minúsculas), si lo hay."""
    return _BY_EXE.get(exe.lower())


def _steam_libraries() -> list[Path]:
    roots: list[Path] = []
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
                roots.append(Path(winreg.QueryValueEx(k, "SteamPath")[0]))
        except OSError:
            pass
    roots.append(Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Steam")
    libs: list[Path] = []
    for root in roots:
        vdf = root / "steamapps" / "libraryfolders.vdf"
        try:
            text = vdf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        libs.append(root)
        for m in re.finditer(r'"path"\s+"([^"]+)"', text):
            libs.append(Path(m.group(1).replace("\\\\", "\\")))
    seen, out = set(), []
    for lib in libs:
        key = str(lib).lower()
        if key not in seen and (lib / "steamapps").is_dir():
            seen.add(key)
            out.append(lib)
    return out


def installed_games() -> list[dict]:
    """Juegos conocidos que parecen instalados: ``[{name, exe, genre, profile_id, source}]``."""
    found: dict[str, dict] = {}

    def add(game: dict, source: str):
        found.setdefault(game["name"], {
            "name": game["name"], "exe": game["exes"][0], "genre": game["genre"],
            "genre_name": GENRE_NAMES[game["genre"]], "profile_id": game["profile_id"], "source": source,
        })

    for lib in _steam_libraries():
        for acf in (lib / "steamapps").glob("appmanifest_*.acf"):
            try:
                m = re.search(r'"installdir"\s+"([^"]+)"', acf.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            if m and m.group(1).lower() in _BY_STEAM:
                add(_BY_STEAM[m.group(1).lower()], "Steam")

    manifests = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Epic/EpicGamesLauncher/Data/Manifests"
    for item in manifests.glob("*.item") if manifests.is_dir() else []:
        try:
            data = json.loads(item.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, ValueError):
            continue
        game = lookup(Path(data.get("LaunchExecutable", "")).name)
        if game:
            add(game, "Epic Games")

    riot = Path(os.environ.get("SYSTEMDRIVE", "C:") + "\\") / "Riot Games"
    for folder, name in (("League of Legends", "League of Legends"), ("VALORANT", "VALORANT")):
        if (riot / folder).is_dir():
            add(next(g for g in KNOWN if g["name"] == name), "Riot")

    return sorted(found.values(), key=lambda g: g["name"].lower())
