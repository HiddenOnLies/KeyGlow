import pytest

from keyglow import layout as L
from keyglow.app import library, server
from keyglow.app.engine import LightEngine

FRAME = {"CAPSLOCK": (10, 20, 30), "A": (1, 2, 3)}


def engine(layout="alloy_origins_65", caps=True, **settings):
    eng = LightEngine(layout)
    eng.caps_state = lambda: caps
    server.apply_caps_lock(eng, {**library.DEFAULT_SETTINGS, **settings})
    return eng


def test_lights_caps_lock_while_it_is_on():
    assert engine().with_caps_lock(FRAME) == {"CAPSLOCK": (255, 255, 255), "A": (1, 2, 3)}
    assert engine(caps=False).with_caps_lock(FRAME) == FRAME


def test_color_and_off_setting():
    assert engine(caps_lock_color="#ff0000").with_caps_lock(FRAME)["CAPSLOCK"] == (255, 0, 0)
    assert engine(caps_lock="off").with_caps_lock(FRAME) == FRAME
    assert engine(caps_lock_color="nonsense").caps_color == (255, 255, 255)


@pytest.mark.parametrize("has_indicator, mode, lit", [
    (True, "auto", False),   # el teclado ya tiene piloto: no hace falta
    (False, "auto", True),
    (None, "auto", True),    # no se sabe: mejor encenderla
    (True, "on", True),
])
def test_auto_depends_on_the_keyboard(has_indicator, mode, lit):
    eng = engine(caps_lock=mode)
    eng.layout.caps_indicator = has_indicator
    assert eng.caps_light() is lit


def test_model_layouts_carry_the_indicator_flag():
    assert L.model_layout("03f0:038f").caps_indicator is False  # HyperX Alloy Origins 65
    L.WORKSHOP_MODELS[:] = [{"title": "Board", "usb": ["1234:abcd"], "caps_lock_indicator": True,
                             "keys": [{"id": "CAPSLOCK", "x": 0, "y": 0}]}]
    try:
        lay = L.model_layout("1234:abcd")
        assert lay.caps_indicator is True
        # sobrevive a la caché de la última distribución detectada
        assert L.Layout.from_dict(lay.to_dict()).caps_indicator is True
        with pytest.raises(ValueError):
            L.validate_model({**L.WORKSHOP_MODELS[0], "caps_lock_indicator": "yes"})
    finally:
        L.WORKSHOP_MODELS.clear()
