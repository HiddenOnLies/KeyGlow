import json

import pytest

from keyglow import layout as L
from keyglow.app import layout_sync, library

KEYS = [{"id": "ESC", "x": 0, "y": 0}, {"id": "Q", "x": 1, "y": 0}, {"id": "SPACE", "x": 0, "y": 1, "w": 6.25}]


def model(**over):
    return {"title": "Test board", "usb": ["1234:abcd"], "keys": KEYS, **over}


@pytest.fixture(autouse=True)
def clean(monkeypatch, tmp_path):
    monkeypatch.setattr(library, "app_data_dir", lambda: tmp_path)
    L.WORKSHOP_MODELS.clear()
    yield
    L.WORKSHOP_MODELS.clear()


@pytest.mark.parametrize("bad", [
    {"usb": ["1234:abcd"], "keys": KEYS},                       # sin título
    model(usb=["12345:1"]),                                     # USB mal escrito
    model(usb=[], names=[]),                                    # no hay cómo reconocerlo
    model(keys=[{"id": "ESC", "x": 0, "y": 0}] * 2),            # tecla repetida
    model(keys=[{"id": "esc; rm", "x": 0, "y": 0}]),            # id raro
    model(keys=[{"id": "ESC", "x": 999, "y": 0}]),              # fuera de rango
    model(builtin="does_not_exist", keys=None),
])
def test_validation_rejects(bad):
    with pytest.raises(ValueError):
        L.validate_model(bad)


def test_workshop_layout_is_used_and_marked():
    L.WORKSHOP_MODELS[:] = [model(name="test-board")]
    lay = L.model_layout("1234:ABCD")
    assert lay.source == "model:workshop" and lay.title == "Test board" and lay.verified is False
    assert lay.ids == ["ESC", "Q", "SPACE"]


def test_verified_wins_then_workshop_wins_over_bundled():
    L.WORKSHOP_MODELS[:] = [model(title="Unverified"), model(title="Verified", verified=True)]
    assert L.model_layout("1234:abcd").title == "Verified"
    # el HyperX está incluido y verificado; una copia del workshop, también verificada, gana
    L.WORKSHOP_MODELS[:] = [model(title="Workshop copy", usb=["03f0:038f"], verified=True)]
    assert L.model_layout("03f0:038f").title == "Workshop copy"
    # pero una sin verificar no le gana a la incluida verificada
    L.WORKSHOP_MODELS[:] = [model(title="Workshop guess", usb=["03f0:038f"])]
    assert L.model_layout("03f0:038f").source == "model"


def test_refresh_downloads_validates_and_caches(tmp_path):
    bundle = tmp_path / "layouts.json"
    bundle.write_text(json.dumps({"format": layout_sync.FORMAT,
                                  "layouts": [model(name="good"), model(usb=["nope"])]}), encoding="utf-8")
    r = layout_sync.refresh(bundle.as_uri(), force=True)
    assert r["updated"] and r["count"] == 1 and not r["error"]          # el inválido se descarta
    assert L.model_layout("1234:abcd").title == "Test board"
    # sin conexión: se mantiene la caché
    L.WORKSHOP_MODELS.clear()
    r = layout_sync.refresh((tmp_path / "missing.json").as_uri(), force=True)
    assert not r["updated"] and r["error"] and r["count"] == 1
    # y no se vuelve a descargar antes de un día
    assert layout_sync.refresh(bundle.as_uri())["updated"] is False


def test_refresh_rejects_files_that_are_not_layouts(tmp_path):
    other = tmp_path / "other.json"
    other.write_text('{"format": "keyglow-gallery/1", "profiles": []}', encoding="utf-8")
    assert layout_sync.refresh(other.as_uri(), force=True)["error"]
