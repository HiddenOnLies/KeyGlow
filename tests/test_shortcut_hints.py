"""Atajos que se iluminan al mantener Ctrl, Alt o Win."""

import pytest

from keyglow import shortcuts
from keyglow.app import engine as E
from keyglow.app import library, server
from keyglow.app.engine import LightEngine
from keyglow.layout import load_layout

LAY = load_layout("ansi_full")
FRAME = {k: (100, 100, 100) for k in LAY.ids}


@pytest.mark.parametrize("mods, combo", [
    ({"ctrl"}, "ctrl"), ({"shift", "ctrl"}, "ctrl+shift"), ({"win"}, "win"),
    ({"shift"}, ""),               # Shift solo es para escribir
    ({"ctrl", "alt"}, ""),         # AltGr llega como Ctrl+Alt
    (set(), ""),
])
def test_combo(mods, combo):
    assert shortcuts.combo(mods) == combo


def test_apps_have_their_own_shortcuts():
    assert "C" in shortcuts.keys_for({"ctrl"})
    assert "P" in shortcuts.keys_for({"ctrl"}, "Code.exe") and shortcuts.app_name("code.exe") == "VS Code"
    assert shortcuts.keys_for({"ctrl"}, "msedge.exe") == shortcuts.keys_for({"ctrl"}, "chrome.exe")
    # la tecla Win es siempre de Windows
    assert shortcuts.keys_for({"win"}, "code.exe") == shortcuts.keys_for({"win"})
    # sin atajos propios para esa combinación: los de Windows
    assert shortcuts.keys_for({"win", "shift"}, "discord.exe") == shortcuts.keys_for({"win", "shift"})


def test_every_shortcut_key_is_a_real_key():
    ids = set(LAY.ids) | set(load_layout("iso_full").ids)
    data = shortcuts._data()
    sets = list(data["default"].values()) + [v for app in data["apps"].values() for k, v in app.items() if isinstance(v, list)]
    assert {k for keys in sets for k in keys} <= ids


def engine(mods, **settings):
    eng = LightEngine("ansi_full")
    held = {"now": set(mods)}
    eng.mods_state = lambda: held["now"]
    server.apply_caps_lock(eng, {**library.DEFAULT_SETTINGS, **settings})
    return eng, held


def test_holding_ctrl_lights_its_shortcuts_after_a_moment():
    eng, held = engine({"ctrl"})
    assert eng.with_shortcut_hints(FRAME, 10.0) == FRAME          # todavía no: puede ser un Ctrl+C rápido
    f = eng.with_shortcut_hints(FRAME, 10.0 + E.HINT_DELAY + E.HINT_FADE)
    assert f["C"] == (255, 255, 255) and f["LCTRL"] == (255, 255, 255)
    assert f["Q"] == (18, 18, 18)                                  # el resto, atenuado
    held["now"] = set()                                            # al soltar se apaga poco a poco
    t = 10.0 + E.HINT_DELAY + E.HINT_FADE
    mid = eng.with_shortcut_hints(FRAME, t + E.HINT_FADE / 2)
    assert 100 < mid["C"][0] < 255
    assert eng.with_shortcut_hints(FRAME, t + E.HINT_FADE * 2) == FRAME


def test_a_quick_shortcut_does_not_flash():
    eng, held = engine({"ctrl"})
    eng.with_shortcut_hints(FRAME, 1.0)
    held["now"] = set()
    assert eng.with_shortcut_hints(FRAME, 1.1) == FRAME


@pytest.mark.parametrize("setup", ["setting_off", "game", "game_profile"])
def test_off_when_disabled_or_in_games(setup):
    eng, _ = engine({"ctrl"}, shortcut_hints=setup != "setting_off")
    if setup == "game":
        eng.foreground = "cs2.exe"
    if setup == "game_profile":
        eng.override = {"reason": "Some game", "profile": "x", "reactive": False}
    eng.with_shortcut_hints(FRAME, 1.0)
    assert eng.with_shortcut_hints(FRAME, 2.0) == FRAME


def test_hint_color_setting():
    eng, _ = engine({"win"}, shortcut_hints_color="#00ff00")
    eng.with_shortcut_hints(FRAME, 1.0)
    assert eng.with_shortcut_hints(FRAME, 2.0)["D"] == (0, 255, 0)
