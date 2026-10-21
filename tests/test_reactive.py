"""Efecto reactivo: se ilumina al pulsar y se apaga solo."""

import time

from keyglow import input as keyinput
from keyglow.app.keyhook import key_id
from keyglow.layout import load_layout
from keyglow.profile import Profile, Renderer

LAY = load_layout("alloy_origins_65")


def render(style, base="#000000", **params):
    prof = Profile("r", [{"effect": "solid", "params": {"color": base}},
                         {"effect": "reactive", "params": {"colors": ["#ff0000"], "style": style, **params}}])
    return Renderer(prof, LAY)


def test_tecla_se_ilumina_y_se_apaga():
    keyinput.clear()
    r = render("key", duration=0.5)
    keyinput.press("W")
    f = r.frame(0.01)
    assert f["W"][0] > 200 and f["Q"] == (0, 0, 0)
    keyinput.press("W", when=time.monotonic() - 10)  # pulsación vieja: no cuenta
    keyinput.clear()
    time.sleep(0.01)  # el efecto lee las pulsaciones una vez por fotograma
    assert r.frame(0.02)["W"] == (0, 0, 0)


def test_transparente_sobre_la_capa_de_abajo():
    keyinput.clear()
    r = render("key", base="#0000ff", duration=1.0)
    keyinput.press("A", when=time.monotonic() - 0.5)  # a mitad del desvanecimiento
    f = r.frame(0.03)
    assert f["S"] == (0, 0, 255)
    assert 90 < f["A"][0] < 170 and 90 < f["A"][2] < 170  # mezcla de rojo y azul


def test_fila_y_onda():
    keyinput.clear()
    keyinput.press("G")
    f = render("row").frame(0.04)
    assert f["A"][0] > 200 and f["Q"] == (0, 0, 0)  # misma fila que G, otra fila no
    keyinput.clear()
    keyinput.press("G", when=time.monotonic() - 0.1)
    f = render("ripple", speed=1.0, duration=0.6).frame(0.05)
    assert f["D"][0] > f["G"][0]  # la onda ya salió de G y pasa por teclas cercanas


def test_codigos_de_windows():
    assert key_id(0x41, 0) == "A" and key_id(0xA0, 0) == "LSHIFT"
    assert key_id(0x0D, 0) == "ENTER" and key_id(0x0D, 1) == "NUM_ENTER"
    assert key_id(0x70, 0) == "F1" and key_id(0xFF, 0) is None
