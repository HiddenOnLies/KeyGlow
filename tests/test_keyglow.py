import json

import pytest

from keyglow import color as C
from keyglow.importers import from_csv_text, from_json_data
from keyglow.keynames import normalize
from keyglow.layout import BUILTIN, load_layout, resolve_keys
from keyglow.profile import Profile, Renderer
from keyglow.retarget import retarget, to_portable


@pytest.mark.parametrize("name,expected", [
    ("Key: Escape", "ESC"), ("Escape", "ESC"), ("KeyW", "W"), ("Digit1", "1"),
    ("Key: Left Control", "LCTRL"), ("ControlLeft", "LCTRL"), ("Key: \\ (ANSI)", "BACKSLASH"),
    ("Key: Number Pad 7", "NUM_7"), ("Numpad7", "NUM_7"), ("KP_ENTER", "NUM_ENTER"),
    ("Number Pad /", "NUM_SLASH"), ("NumpadAdd", "NUM_PLUS"), ("Num Lock", "NUMLOCK"),
    ("ArrowUp", "UP"), ("Key: Page Down", "PAGE_DOWN"), ("F11", "F11"), ("Key: `", "GRAVE"),
    ("Right Fn", "FN"), ("PAGE_UP", "PAGE_UP"), ("NUM_0", "NUM_0"), ("Space", "SPACE"),
    ("Key: \\ (ISO)", "NONUS_BACKSLASH"), ("Key: #", "NONUS_HASH"), ("IntlBackslash", "NONUS_BACKSLASH"),
    ("KC_LCTL", "LCTRL"), ("KC_SPC", "SPACE"), ("KC_P1", "NUM_1"), ("KC_A", "A"),
    ("Key: Media Play/Pause", "MEDIA_PLAY"), ("Key: Volume Up", "VOL_UP"),
    ("Bananas", None),
])
def test_normalize(name, expected):
    assert normalize(name) == expected


def test_layout_sizes():
    sizes = {name: len(f()) for name, f in BUILTIN.items()}
    assert sizes == {"alloy_origins_65": 68, "ansi_60": 61, "ansi_65": 68, "ansi_75": 83,
                     "ansi_tkl": 87, "ansi_full": 104, "iso_60": 62, "iso_tkl": 88, "iso_full": 105}
    for f in BUILTIN.values():
        lay = f()
        assert len(set(lay.ids)) == len(lay.ids)
        keys = lay.keys
        for i, a in enumerate(keys):  # ninguna tecla pisa a otra
            for b in keys[i + 1:]:
                assert not (a.x < b.x + b.w - 1e-6 and b.x < a.x + a.w - 1e-6
                            and a.y < b.y + b.h - 1e-6 and b.y < a.y + a.h - 1e-6), (lay.name, a.id, b.id)


def _fake_matrix(lay, extra=()):
    """Nombres de LED estilo OpenRGB y una matriz aproximada para un layout (+ teclas extra)."""
    names = [f"Key: {k.id}" for k in lay.keys] + [f"Key: {e}" for e in extra]
    width = int(lay.width) + len(extra) + 2
    matrix = [[None] * width for _ in range(int(lay.height) + 1)]
    for i, k in enumerate(lay.keys):
        matrix[round(k.y)][int(k.x)] = i
    for j, _ in enumerate(extra):
        matrix[0][int(lay.width) + 1 + j] = len(lay.keys) + j
    return names, matrix


def test_device_layout_picks_matching_builtin():
    from keyglow.layout import from_device
    for name in ("ansi_tkl", "iso_full", "ansi_65"):
        names, matrix = _fake_matrix(load_layout(name))
        assert from_device("Test", names, matrix).ids == load_layout(name).ids


def test_device_layout_places_extra_keys():
    from keyglow.layout import from_device
    full = load_layout("ansi_full")
    names, matrix = _fake_matrix(full, extra=["Media Play/Pause", "Volume Up"])
    lay = from_device("With media keys", names, matrix)
    assert {"MEDIA_PLAY", "VOL_UP"} <= set(lay.ids) and len(lay) == len(full) + 2
    media = lay.get("MEDIA_PLAY")
    assert all(not (media.x < k.x + k.w and k.x < media.x + media.w and media.y < k.y + k.h and k.y < media.y + media.h)
               for k in lay.keys if k.id != "MEDIA_PLAY")


def test_device_layout_unknown_arrangement_uses_grid():
    from keyglow.layout import from_device
    names = ["Key: A", "Key: B", "Key: Media Mute", "Key: Volume Up", "Key: Volume Down"]
    lay = from_device("Macro pad", names, [[0, 1, 2], [3, 4, None]])
    assert lay.name == "device" and len(lay) == 5


def test_layout_rows_are_flush():
    lay = load_layout("alloy_origins_65")
    for row in range(5):
        right = max(k.x + k.w for k in lay.keys if int(k.y) == row)
        assert right == pytest.approx(16)


def test_groups_resolve_per_layout():
    lay = load_layout("alloy_origins_65")
    assert resolve_keys(["@wasd", "@arrows"], lay) == {"W", "A", "S", "D", "UP", "DOWN", "LEFT", "RIGHT"}
    assert resolve_keys(["@numpad", "@fn_row"], lay) == set()


def test_render_all_effects():
    lay = load_layout("ansi_full")
    from keyglow.effects import REGISTRY
    for name in REGISTRY:
        if name == "image":
            continue
        params = {"points": [{"u": 0.1, "v": 0.1, "color": "#f00"}]} if name == "points" else {}
        frame = Renderer(Profile("t", [{"effect": name, "params": params}]), lay).frame(1.3)
        assert set(frame) == set(lay.ids)
        assert all(0 <= v <= 255 for rgb in frame.values() for v in rgb)


def test_layer_filter_and_opacity():
    lay = load_layout("alloy_origins_65")
    prof = Profile("t", [
        {"effect": "solid", "params": {"color": "#000000"}},
        {"effect": "solid", "params": {"color": "#ffffff"}, "keys": ["@wasd"], "opacity": 0.5},
    ])
    f = Renderer(prof, lay).frame(0)
    assert f["W"] == (128, 128, 128)
    assert f["Q"] == (0, 0, 0)


def test_profile_validation():
    with pytest.raises(ValueError):
        Profile.from_dict({"layers": [{"effect": "nope"}]})
    with pytest.raises(ValueError):
        Renderer(Profile("t", [{"effect": "solid", "params": {"colour": "#fff"}}]), load_layout("ansi_60"))


def test_retarget_highlight_does_not_fill():
    full, k65 = load_layout("ansi_full"), load_layout("alloy_origins_65")
    prof = from_json_data({"W": "#f00", "Number Pad 5": "#0f0"})
    out, rep = retarget(prof, k65, full)
    assert out.layers[0]["params"]["keys"] == {"W": "#f00"}
    assert rep.dropped == ["NUM_5"] and not rep.filled


def test_retarget_full_map_fills_missing_keys():
    full, k60 = load_layout("ansi_full"), load_layout("ansi_60")
    prof = from_json_data({k: "#123456" for k in full.ids})
    out, rep = retarget(prof, k60, full)
    assert set(out.layers[0]["params"]["keys"]) == set(k60.ids)
    assert "FN" in rep.filled


def test_portable_conversion():
    full, k65 = load_layout("ansi_full"), load_layout("alloy_origins_65")
    prof = from_json_data({k.id: C.to_hex(C.hsv(k.x / full.width)) for k in full.keys})
    port = to_portable(prof, full)
    assert port.layers[0]["effect"] == "points"
    frame = Renderer(port, k65).frame(0)
    assert frame["ESC"] != frame["RIGHT"]


def test_csv_and_list_import():
    p = from_csv_text("key,color\nEscape,#ff0000\nKeyW,#00ff00\n")
    assert p.layers[0]["params"]["keys"] == {"Escape": "#ff0000", "KeyW": "#00ff00"}
    p = from_json_data([{"led": "Key: A", "color": [255, 0, 0]}])
    assert Renderer(p, load_layout("ansi_60")).frame(0)["A"] == (255, 0, 0)


def test_example_profiles_load(tmp_path):
    from pathlib import Path
    from keyglow.importers import load_any
    for f in Path(__file__).parent.parent.joinpath("profiles").glob("*.json"):
        prof = load_any(str(f))
        out, _ = retarget(prof, load_layout("alloy_origins_65"),
                          load_layout(prof.designed_for or "ansi_full"))
        Renderer(out, load_layout("alloy_origins_65")).frame(0.5)
        out.save(tmp_path / f.name)
        json.loads((tmp_path / f.name).read_text())


def test_device_layout_exact_model_by_usb_id():
    from keyglow.layout import from_device
    names, matrix = _fake_matrix(load_layout("ansi_tkl"))  # aunque las teclas no coincidan
    lay = from_device("Some keyboard", names, matrix, usb="03F0:038F")
    assert lay.name == "alloy_origins_65" and lay.source == "model" and lay.usb == "03f0:038f"


def test_device_layout_moves_keys_the_matrix_puts_in_another_row():
    from keyglow.layout import Key, Layout, from_device
    base = load_layout("ansi_75")
    # un 75% cuyo HOME está en la fila de PAGE_DOWN y al revés
    home, pgdn = base.get("HOME"), base.get("PAGE_DOWN")
    keys = [Key(k.id, k.x, pgdn.y if k.id == "HOME" else home.y if k.id == "PAGE_DOWN" else k.y, k.w, k.h)
            for k in base.keys]
    names, matrix = _fake_matrix(Layout("x", "x", keys))
    lay = from_device("Odd 75", names, matrix)
    assert lay.source == "adapted:ansi_75"
    assert lay.get("HOME").y == pgdn.y and lay.get("PAGE_DOWN").y == home.y


def test_device_layout_standard_source():
    from keyglow.layout import from_device
    names, matrix = _fake_matrix(load_layout("iso_tkl"))
    lay = from_device("Plain ISO TKL", names, matrix)
    assert lay.name == "iso_tkl" and lay.source == "standard:iso_tkl"
