"""Vista previa al pasar el ratón: se ve en el teclado sin cambiar el perfil activo."""

import time

from keyglow.app import engine as E
from keyglow.app.engine import LightEngine

RED = {"name": "red", "layers": [{"effect": "solid", "params": {"color": "#ff0000"}}]}
BLUE = {"name": "blue", "layers": [{"effect": "solid", "params": {"color": "#0000ff"}}]}


class FakeKeyboard:
    name = "fake"

    def __init__(self):
        self.last = {}

    def write(self, frame):
        self.last = dict(frame)

    def modes(self):
        return []


def running_engine():
    eng = LightEngine("alloy_origins_65")
    eng.fps = 60
    eng._kb = FakeKeyboard()
    eng.apply(RED)
    return eng


def wait_for(eng, color):
    for _ in range(50):
        if eng._kb.last.get("A") == color:
            return True
        time.sleep(0.02)
    return False


def test_peek_shows_a_profile_and_goes_back():
    eng = running_engine()
    try:
        assert wait_for(eng, (255, 0, 0))
        eng.peek(BLUE)
        assert eng.peeking and wait_for(eng, (0, 0, 255))
        assert eng.status()["profile"] == "red"  # el perfil activo no cambia
        eng.peek(None)
        assert not eng.peeking and wait_for(eng, (255, 0, 0))
    finally:
        eng.stop()


def test_peek_expires_by_itself(monkeypatch):
    monkeypatch.setattr(E, "PEEK_TIMEOUT", 0.1)
    eng = running_engine()
    try:
        eng.peek(BLUE)
        assert wait_for(eng, (0, 0, 255))
        time.sleep(0.15)
        assert not eng.peeking and wait_for(eng, (255, 0, 0))
    finally:
        eng.stop()
