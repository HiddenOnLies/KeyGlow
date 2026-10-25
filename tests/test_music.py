"""Efecto de música: niveles del sonido, sus tres estilos y cuándo se escucha."""

import math

import pytest

from keyglow import sound
from keyglow.app.audio import band_levels
from keyglow.app.engine import LightEngine
from keyglow.layout import load_layout
from keyglow.profile import Profile, Renderer

np = pytest.importorskip("numpy")
LAY = load_layout("ansi_full")


@pytest.fixture(autouse=True)
def silence():
    sound.clear()
    yield
    sound.clear()


def tone(freq, n=1024, rate=48000, amp=0.5):
    t = np.arange(n) / rate
    return (amp * np.sin(2 * math.pi * freq * t)).astype("float32")


def test_a_low_tone_lights_the_bass_bands_and_a_high_one_the_treble():
    state = {}
    for _ in range(10):
        low = band_levels(tone(60), state=state)
    state = {}
    for _ in range(10):
        high = band_levels(tone(8000), state=state)
    assert low.index(max(low)) <= 2 and high.index(max(high)) >= 12


def test_silence_stays_dark():
    state = {}
    for _ in range(10):
        levels = band_levels(np.zeros(1024, dtype="float32"), state=state)
    assert max(levels) < 0.05


def render(style, **params):
    prof = Profile("m", [{"effect": "solid", "params": {"color": "#000000"}},
                         {"effect": "music", "params": {"colors": ["#ff0000"], "style": style, **params}}])
    return Renderer(prof, LAY).frame(0.5)


def test_bars_grow_from_the_bottom_in_their_column():
    sound.set_levels([0.5] + [0.0] * (sound.BANDS - 1))  # solo graves, a media altura
    f = render("bars")
    assert f["LCTRL"][0] > 200 and f["ESC"] == (0, 0, 0)       # la columna de la izquierda, hasta la mitad
    sound.set_levels([1.0] + [0.0] * (sound.BANDS - 1))
    assert render("bars")["ESC"][0] > 200                      # a tope, llega arriba
    assert f["RCTRL"] == (0, 0, 0)                             # la de los agudos, apagada


def test_pulse_and_vu():
    sound.set_levels([0.8] * sound.BANDS)
    assert render("pulse")["A"][0] > 150
    sound.set_levels([0.3] * sound.BANDS)
    f = render("vu")
    assert f["ESC"][0] > 200 and f["NUM_PLUS"] == (0, 0, 0)    # llena desde la izquierda


def test_silence_or_stale_levels_show_the_layers_below():
    assert render("bars") == render("pulse") == {k: (0, 0, 0) for k in LAY.ids}


class FakeMeter:
    def __init__(self, log):
        self.log = log

    @property
    def active(self):
        return bool(self.log) and self.log[-1] == "start"

    def start(self):
        self.log.append("start")

    def stop(self):
        self.log.append("stop")


def test_audio_runs_only_while_a_profile_uses_music():
    eng = LightEngine("ansi_full")
    started = []
    eng.audio = FakeMeter(started)
    eng._thread = type("T", (), {"is_alive": lambda self: True})()      # luces encendidas
    eng._music_live = True
    eng.housekeeping()
    eng._music_live = False
    eng.housekeeping()
    assert started == ["start", "stop"]
