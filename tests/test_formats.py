import json
import struct

import pytest

from keyglow import exporters
from keyglow.formats import openrgb
from keyglow.importers import from_bytes
from keyglow.keynames import external_name
from keyglow.layout import load_layout
from keyglow.profile import Profile

LAY = load_layout("alloy_origins_65")
PROFILE = Profile(name="Test", layers=[
    {"effect": "solid", "params": {"color": "#102030"}},
    {"effect": "solid", "params": {"color": "#ff0000"}, "keys": ["@wasd"]},
])


@pytest.mark.parametrize("fmt", ["keys-openrgb", "keys-web", "keys-qmk", "csv", "openrgb", "keyglow"])
def test_export_then_import_keeps_colors(fmt):
    content = exporters.export(PROFILE, LAY, fmt)
    back = from_bytes(content.encode("utf-8"), exporters.filename(PROFILE, fmt))
    frame = exporters.snapshot(back, LAY)
    assert frame["W"] == (255, 0, 0)
    assert frame["P"] == (0x10, 0x20, 0x30)


def test_export_names_per_program():
    assert external_name("LCTRL", "openrgb") == "Key: Left Control"
    assert external_name("LCTRL", "web") == "ControlLeft"
    assert external_name("LCTRL", "qmk") == "KC_LCTL"
    keys = json.loads(exporters.export(PROFILE, LAY, "keys-web"))
    assert keys["KeyW"] == "#ff0000" and keys["ArrowUp"] == "#102030"


def test_openrgb_export_uses_device_leds():
    device = openrgb.generic_device(LAY, "My keyboard")
    device["leds"].insert(0, {"name": ""})  # hueco de matriz sin tecla
    doc = json.loads(exporters.export(PROFILE, LAY, "openrgb", device=device))
    c = doc["controllers"][0]
    assert c["name"] == "My keyboard" and len(c["colors"]) == len(c["leds"])
    assert c["colors"][0] == 0
    w = [led["name"] for led in c["leds"]].index("Key: W")
    assert c["colors"][w] == 0x0000FF  # 0x00BBGGRR


def _orp(version: int, leds: list[str], colors: list[int], matrix: list[list[int]]) -> bytes:
    """Perfil .orp mínimo, con la estructura de RGBController::SetDeviceDescription."""
    def s(text):
        raw = text.encode() + b"\0"
        return struct.pack("<H", len(raw)) + raw

    body = struct.pack("<i", openrgb.KEYBOARD) + s("Test keyboard")
    if version >= 1:
        body += s("Vendor")
    body += s("desc") + s("1.0") + s("serial") + s("loc")
    mode = s("Direct") + struct.pack("<i", 0) + struct.pack("<III", 32, 0, 0)
    if version >= 3:
        mode += struct.pack("<II", 0, 0)
    mode += struct.pack("<III", 0, 0, 0)
    if version >= 3:
        mode += struct.pack("<I", 0)
    mode += struct.pack("<II", 0, 1) + struct.pack("<H", 0)
    body += struct.pack("<Hi", 1, 0) + mode
    h, w = len(matrix), len(matrix[0])
    zone = s("Keyboard") + struct.pack("<iIII", 2, len(leds), len(leds), len(leds))
    zone += struct.pack("<HII", h * w, h, w) + struct.pack(f"<{h * w}I", *[c for row in matrix for c in row])
    if version >= 4:
        zone += struct.pack("<H", 0)
    body += struct.pack("<H", 1) + zone
    body += struct.pack("<H", len(leds)) + b"".join(s(n) + struct.pack("<I", 0) for n in leds)
    body += struct.pack("<H", len(colors)) + struct.pack(f"<{len(colors)}I", *colors)
    block = struct.pack("<I", len(body) + 4) + body
    return struct.pack("<16sI", b"OPENRGB_PROFILE\0", version or 1) + block


@pytest.mark.parametrize("version", [0, 2, 3, 4])
def test_read_legacy_orp(version):
    none = 0xFFFFFFFF
    raw = _orp(version, ["Key: W", "Key: A", "", "Key: Media Volume +"],
               [0x0000FF, 0x00FF00, 0, 0xFF0000], [[0, 1, none], [2, none, 3]])
    name, ctrls = openrgb.parse(raw)
    assert ctrls[0].name == "Test keyboard"
    assert ctrls[0].matrix == [[0, 1, None], [2, None, 3]]
    profile = from_bytes(raw, "gaming.orp")
    assert profile.name == "gaming"
    assert profile.layers[0]["params"]["keys"] == {"W": "#ff0000", "A": "#00ff00", "VOL_UP": "#0000ff"}


def test_read_openrgb_json_skips_other_devices():
    doc = {"profile_name": "Desk", "controllers": [
        {"name": "RAM", "type": 1, "leds": [{"name": "LED 1"}], "colors": [255]},
        {"name": "Board", "type": 5, "leds": [{"name": "Key: Escape"}, {"name": "Key: Q"}],
         "colors": [0x00FF00, 0x0000FF],
         "zones": [{"leds_count": 2, "matrix_map": {"height": 1, "width": 2, "map": [0, 1]}}]},
    ]}
    profile = from_bytes(json.dumps(doc).encode(), "desk.json")
    assert profile.name == "Desk"
    assert profile.layers[0]["params"]["keys"] == {"ESC": "#00ff00", "Q": "#ff0000"}


def test_not_an_openrgb_profile():
    with pytest.raises(ValueError):
        openrgb.parse(b"hello")
