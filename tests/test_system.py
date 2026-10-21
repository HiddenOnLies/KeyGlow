import sys

import pytest

from keyglow.app import system

SETTINGS = {"openrgb_host": "127.0.0.1", "openrgb_port": 6742, "openrgb_path": ""}


def test_find_openrgb_prefers_custom_path(tmp_path):
    exe = tmp_path / "OpenRGB.exe"
    exe.write_bytes(b"")
    assert system.find_openrgb(str(exe)) == str(exe)


def test_ensure_openrgb(monkeypatch):
    started = []
    monkeypatch.setattr(system, "start_openrgb", lambda path, port: started.append((path, port)))
    monkeypatch.setattr(system, "server_up", lambda host, port: True)
    assert system.ensure_openrgb(SETTINGS) == "running" and not started

    monkeypatch.setattr(system, "server_up", lambda host, port: False)
    monkeypatch.setattr(system, "find_openrgb", lambda custom="": None)
    assert system.ensure_openrgb(SETTINGS) == "missing"

    monkeypatch.setattr(system, "find_openrgb", lambda custom="": "C:/OpenRGB/OpenRGB.exe")
    assert system.ensure_openrgb(SETTINGS) == "started"
    assert started == [("C:/OpenRGB/OpenRGB.exe", 6742)]

    # nunca se arranca nada para un OpenRGB remoto
    assert system.ensure_openrgb({**SETTINGS, "openrgb_host": "192.168.1.20"}) == "running"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows registry")
def test_autostart_roundtrip():
    key = r"Software\KeyGlowTest\Run"
    try:
        system.set_autostart(True, key)
        assert system.autostart_enabled(key)
        system.set_autostart(False, key)
        assert not system.autostart_enabled(key)
    finally:
        import winreg
        for sub in (r"Software\KeyGlowTest\Run", r"Software\KeyGlowTest"):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub)
            except OSError:
                pass
