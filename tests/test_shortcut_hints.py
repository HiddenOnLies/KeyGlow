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
    ({"ctrl", "alt"}, "ctrl+alt"),  # AltGr (Alt derecho) lo descarta antes keyhook.held_modifiers
    ({"win", "ctrl", "shift"}, "ctrl+shift+win"),
    (set(), ""),
])
def test_combo(mods, combo):
    assert shortcuts.combo(mods) == combo


def test_apps_have_their_own_shortcuts():
    assert "C" in shortcuts.keys_for({"ctrl"})
    assert "P" in shortcuts.keys_for({"ctrl"}, "Code.exe") and shortcuts.app_name("code.exe") == "VS Code"
    assert {"T", "C", "A"} <= set(shortcuts.keys_for({"ctrl"}, "chrome.exe"))  # los de la app y los de Windows
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


def test_three_key_combos():
    assert "DELETE" in shortcuts.keys_for({"ctrl", "alt"})                 # Ctrl+Alt+Supr
    assert shortcuts.keys_for({"ctrl", "shift", "win"}) == ["B"]           # reinicia el driver gráfico
    assert "R" in shortcuts.keys_for({"alt", "win"})                       # grabar con la Game Bar


def profile_engine(mods, hints=None):
    eng, held = engine(mods)
    eng._profile = {"name": "p", "layers": [], **({"shortcut_hints": hints} if hints else {})}
    return eng, held


def lit(eng, t=2.0):
    eng.with_shortcut_hints(FRAME, 1.0)
    return eng.with_shortcut_hints(FRAME, t)


def test_a_profile_can_turn_them_off():
    eng, _ = profile_engine({"ctrl"}, {"enabled": False})
    assert lit(eng) == FRAME


def test_effects():
    eng, _ = profile_engine({"ctrl"}, {"effect": "solid", "color": "#ff0000"})
    assert lit(eng)["C"] == (255, 0, 0)
    eng, _ = profile_engine({"ctrl"}, {"effect": "pulse", "color": "#ff0000"})
    pulses = {lit(eng, t)["C"][0] for t in (2.0, 2.3, 2.6)}
    assert len(pulses) > 1 and max(pulses) <= 255
    eng, _ = profile_engine({"ctrl"}, {"effect": "rainbow"})
    f = lit(eng)
    assert f["A"] != f["P"]                                    # cada atajo, su color
    eng, _ = profile_engine({"ctrl"}, {"effect": "profile"})
    assert lit(eng)["C"] == (255, 255, 255)                    # el gris del perfil, a todo brillo


def test_preview_lights_ctrl_shortcuts_without_holding_anything():
    eng, _ = profile_engine(set())
    eng.preview_hints({"effect": "solid", "color": "#00ff00"})
    eng.with_shortcut_hints(FRAME, 1.0)
    assert eng.with_shortcut_hints(FRAME, 1.0 + E.HINT_DELAY + E.HINT_FADE)["C"] == (0, 255, 0)


def test_profile_field_is_validated_and_kept():
    from keyglow.profile import Profile
    base = {"name": "p", "layers": [{"effect": "solid", "params": {}}]}
    p = Profile.from_dict({**base, "shortcut_hints": {"effect": "pulse", "color": "red"}})
    assert p.to_dict()["shortcut_hints"] == {"enabled": True, "effect": "pulse", "color": "#ff0000"}
    with pytest.raises(ValueError):
        Profile.from_dict({**base, "shortcut_hints": {"effect": "lasers"}})


def test_more_effects():
    eng, _ = profile_engine({"ctrl"}, {"effect": "gradient", "colors": ["#ff0000", "#0000ff"]})
    f = lit(eng)
    assert f["A"][0] > f["A"][2] and f["P"][2] > f["P"][0]          # rojo a la izquierda, azul a la derecha
    assert len(run({"effect": "wave", "colors": ["#ff0000", "#0000ff"]}, 2, 0.8)) == 2  # se mueve
    assert run({"effect": "blink", "color": "#ff0000"}, 8, 0.1) == {(255, 0, 0), (30, 0, 0)}  # encendido / apagado
    seen = run({"effect": "sparkle", "color": "#ff0000"}, 40, 1 / 6)
    assert (255, 0, 0) in seen and any(c[1] > 0 for c in seen)      # a veces destella hacia el blanco


def run(hints, steps, dt, key="C"):
    """Colores de ``key`` en ``steps`` fotogramas seguidos, ya con los atajos encendidos."""
    eng, _ = profile_engine({"ctrl"}, hints)
    eng.with_shortcut_hints(FRAME, 1.0)
    return {eng.with_shortcut_hints(FRAME, 2.0 + i * dt)[key] for i in range(steps)}


def test_parameters():
    eng, _ = profile_engine({"ctrl"}, {"dim": 0.0})
    assert lit(eng)["Q"] == (0, 0, 0)                                # el resto, apagado del todo
    eng, _ = profile_engine({"ctrl"}, {"delay": 1.2})
    eng.with_shortcut_hints(FRAME, 1.0)
    assert eng.with_shortcut_hints(FRAME, 1.0 + 0.8) == FRAME        # aún no: hay que mantener 1,2 s
    assert eng.with_shortcut_hints(FRAME, 1.0 + 1.2 + E.HINT_FADE)["C"] == (255, 255, 255)
    fast = {c[0] for c in run({"effect": "pulse", "color": "#ff0000", "speed": 3}, 5, 0.1)}
    slow = {c[0] for c in run({"effect": "pulse", "color": "#ff0000", "speed": 0.2}, 5, 0.1)}
    assert max(fast) - min(fast) > max(slow) - min(slow)


def test_parameters_are_validated():
    from keyglow.profile import Profile
    base = {"name": "p", "layers": [{"effect": "solid", "params": {}}]}
    p = Profile.from_dict({**base, "shortcut_hints": {"effect": "wave", "colors": ["red", "#00f"], "speed": 9, "dim": -1}})
    h = p.to_dict()["shortcut_hints"]
    assert h["colors"] == ["#ff0000", "#0000ff"] and h["speed"] == 3.0 and h["dim"] == 0.0   # se ajusta al rango
    for bad in ({"colors": []}, {"colors": "red"}, {"speed": "fast"}):
        with pytest.raises(ValueError):
            Profile.from_dict({**base, "shortcut_hints": bad})
