"""El teclado cambia en OpenRGB (cable -> receptor, se desconecta...): KeyGlow lo nota."""

import struct
import threading
import socket
import time

from keyglow.app import engine as E
from keyglow.app.engine import LightEngine
from keyglow.backends import openrgb as B

RED = {"name": "red", "layers": [{"effect": "solid", "params": {"color": "#ff0000"}}]}


class Fake:
    def __init__(self, name, there=True):
        self.name, self.there, self.writes, self.closed = name, there, 0, False

    def write(self, frame):
        self.writes += 1

    def modes(self):
        return []

    def still_there(self):
        return self.there

    def close(self):
        self.closed = True

    def layout(self):
        raise ValueError("not needed here")


def test_a_keyboard_that_left_the_list_is_replaced(monkeypatch):
    monkeypatch.setattr(E, "DEVICE_CHECK_EVERY", 0.05)
    eng = LightEngine("alloy_origins_65")
    eng.fps = 60
    cable = Fake("ASUS ROG Azoth USB", there=False)       # se pasó al receptor
    dongle = Fake("ASUS ROG Azoth 2.4GHz")
    eng._kb = cable
    monkeypatch.setattr(eng, "_connect", lambda: setattr(eng, "_kb", dongle) or dongle)
    eng.apply(RED)
    try:
        for _ in range(50):
            if dongle.writes:
                break
            time.sleep(0.02)
        assert cable.closed and eng._kb is dongle and dongle.writes
    finally:
        eng.stop()


def test_no_keyboard_tells_what_openrgb_sees():
    e = B.NoKeyboard("OpenRGB doesn't see any keyboard.", ["ASUS ROG Omni Receiver (mouse)"])
    eng = LightEngine("alloy_origins_65")
    eng.devices_seen = e.devices
    assert eng.status()["devices_seen"] == ["ASUS ROG Omni Receiver (mouse)"]


def fake_server(version):
    """Un OpenRGB mínimo: contesta la versión de protocolo y apunta lo que recibe."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    got = []

    def run():
        conn, _ = srv.accept()
        with conn:
            head = conn.recv(16)
            _, _, pid, size = struct.unpack("<4sIII", head)
            conn.recv(size)
            conn.sendall(struct.pack("<4sIII", b"ORGB", 0, 40, 4) + struct.pack("<I", version))
            conn.settimeout(1)
            try:
                head = conn.recv(16)
                if head:
                    got.append(struct.unpack("<4sIII", head)[2])
            except OSError:
                pass
        srv.close()

    threading.Thread(target=run, daemon=True).start()
    return srv.getsockname()[1], got


def test_rescan_on_openrgb_1_0_and_later():
    port, got = fake_server(5)
    assert B.rescan("127.0.0.1", port) is True
    time.sleep(0.2)
    assert got == [140]


def test_older_openrgb_has_no_rescan():
    port, got = fake_server(4)
    assert B.rescan("127.0.0.1", port) is False
    time.sleep(0.2)
    assert got == []
