"""Distribuciones hechas con el editor: se guardan en el PC y mandan sobre las demás."""

import pytest

from keyglow import layout as L
from keyglow.app import layout_store, library

KEYS = [{"id": "ESC", "x": 0, "y": 0}, {"id": "Q", "x": 1.5, "y": 0}, {"id": "SPACE", "x": 0, "y": 1, "w": 6.25}]


@pytest.fixture(autouse=True)
def appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(library, "app_data_dir", lambda: tmp_path)
    L.LOCAL_MODELS.clear()
    L.WORKSHOP_MODELS.clear()
    yield
    L.LOCAL_MODELS.clear()
    L.WORKSHOP_MODELS.clear()


def test_saved_layout_is_used_for_that_keyboard_and_beats_the_workshop():
    L.WORKSHOP_MODELS[:] = [{"title": "Workshop", "usb": ["1234:abcd"], "verified": True,
                             "keys": [{"id": "ESC", "x": 0, "y": 0}, {"id": "Q", "x": 1, "y": 0}, {"id": "SPACE", "x": 0, "y": 1}]}]
    name = layout_store.save("My board", KEYS, usb="1234:ABCD", device="Some Keyboard")
    assert name == "model:local-my-board"
    lay = L.model_layout("1234:abcd")
    assert lay.title == "My board" and lay.source == "model:local" and lay.get("Q").x == 1.5
    assert L.load_layout(name).get("SPACE").w == 6.25                 # también se puede elegir a mano
    assert any(c["name"] == name and c["local"] for c in L.model_choices())


def test_it_survives_a_restart():
    layout_store.save("My board", KEYS, usb="1234:abcd")
    L.LOCAL_MODELS.clear()
    assert layout_store.load() == 1 and L.model_layout("1234:abcd").title == "My board"


def test_overlapping_keys_are_refused():
    with pytest.raises(ValueError, match="overlap"):
        layout_store.save("Bad", KEYS + [{"id": "W", "x": 0.5, "y": 0}], usb="1234:abcd")


def test_known_keys_cover_full_keyboards():
    ids = {k["id"] for k in layout_store.known_keys()}
    assert {"ESC", "NUM_5", "NONUS_BACKSLASH", "MEDIA_PLAY_PAUSE"} & ids >= {"ESC", "NUM_5", "NONUS_BACKSLASH"}
