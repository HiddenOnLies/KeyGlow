"""Remolino, cometa, rebote, interferencias y los estilos cross/burst al pulsar."""

import time

import pytest

from keyglow import input as keyinput
from keyglow.layout import load_layout
from keyglow.profile import Profile, Renderer

LAY = load_layout("alloy_origins_65")


def frames(effect, *times, **params):
    r = Renderer(Profile("t", [{"effect": effect, "params": params}]), LAY)
    return [r.frame(t) for t in times]


@pytest.mark.parametrize("effect", ["swirl", "comet", "bounce", "glitch"])
def test_moves_over_time_and_covers_every_key(effect):
    a, b = frames(effect, 0.0, 1.3)
    assert set(a) == set(LAY.ids) and a != b


def test_swirl_turns_around_the_center():
    (f,) = frames("swirl", 0.0, colors=["#ff0000", "#0000ff"])
    assert f["Q"] != f["PAGE_DOWN"]  # lados opuestos del centro, colores distintos


def test_comet_is_one_bright_spot_with_a_tail():
    (f,) = frames("comet", 0.5, color="#ffffff", background="#000000", speed=0.2, length=0.1)
    lit = [k for k, c in f.items() if c != (0, 0, 0)]
    assert 0 < len(lit) < len(f) * 0.2


def test_bounce_stays_in_one_place_at_a_time():
    (f,) = frames("bounce", 2.0, color="#ffffff", background="#000000", size=0.08)
    bright = [k for k, c in f.items() if c[0] > 128]
    assert 0 < len(bright) < 10


def test_glitch_is_the_same_on_every_pc():
    assert frames("glitch", 0.7) == frames("glitch", 0.7)


def press_render(style, key, age=0.02, **params):
    keyinput.clear()
    keyinput.press(key, when=time.monotonic() - age)
    prof = Profile("r", [{"effect": "solid", "params": {"color": "#000000"}},
                         {"effect": "reactive", "params": {"colors": ["#ff0000"], "style": style, **params}}])
    f = Renderer(prof, LAY).frame(0.01)
    keyinput.clear()
    return f


def test_cross_lights_row_and_column():
    f = press_render("cross", "G")
    assert f["A"][0] > 100 and f["T"][0] > 100  # misma fila / misma columna
    assert f["Q"] == (0, 0, 0)


def test_burst_is_a_filled_circle_around_the_key():
    f = press_render("burst", "G", age=0.2, duration=1.0)
    assert f["G"][0] > 100 and f["F"][0] > 100 and f["ESC"] == (0, 0, 0)
