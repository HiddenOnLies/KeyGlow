"""Perfiles por juego: el vigilante aplica y retira el perfil temporal."""

from keyglow.app import library
from keyglow.app.engine import LightEngine
from keyglow.app.games import GameWatcher, foreground_exe, running_apps


class FakeEngine:
    running = True

    def __init__(self):
        self.override = None
        self.calls = []

    def apply_override(self, data, reason):
        self.override = {"reason": reason, "profile": data["name"]}
        self.calls.append(("on", data["name"]))

    def clear_override(self):
        self.override = None
        self.calls.append(("off",))


def make(rules, switching=True):
    eng = FakeEngine()
    settings = {"game_rules": rules, "game_switching": switching}
    w = GameWatcher(eng, lambda: settings, library.resolve)
    return eng, w


def test_aplica_y_retira_perfil_del_juego():
    eng, w = make([{"exe": "cs2.exe", "name": "CS2", "profile_id": "preset:fire"}])
    w.check("cs2.exe")
    w.check("cs2.exe")  # sin cambios: no se vuelve a aplicar
    assert eng.calls == [("on", "Fire")]
    w.check("discord.exe")
    assert eng.calls[-1] == ("off",) and eng.override is None


def test_desactivado_o_luces_apagadas_no_hace_nada():
    eng, w = make([{"exe": "cs2.exe", "profile_id": "preset:fire"}], switching=False)
    w.check("cs2.exe")
    assert eng.calls == []
    eng, w = make([{"exe": "cs2.exe", "profile_id": "preset:fire"}])
    eng.running = False
    w.check("cs2.exe")
    assert eng.calls == []


def test_recomendado_solo_si_se_activa():
    eng, w = make([])
    w.check("cs2.exe")
    assert eng.calls == []  # desactivado por defecto
    eng = FakeEngine()
    settings = {"game_rules": [{"exe": "dota2.exe", "profile_id": "preset:fire"}], "auto_games": True}
    w = GameWatcher(eng, lambda: settings, library.resolve)
    w.check("cs2.exe")
    assert eng.calls == [("on", "FPS Red")] and eng.override["reason"] == "Counter-Strike 2"
    w.check("dota2.exe")  # la regla del usuario manda sobre la recomendación
    assert eng.calls[-1] == ("on", "Fire")


def test_perfil_borrado_no_rompe():
    eng, w = make([{"exe": "cs2.exe", "profile_id": "mine:no_existe"}])
    w.check("cs2.exe")
    assert eng.calls == []


def test_override_en_motor_real():
    eng = LightEngine()
    eng._thread = type("T", (), {"is_alive": lambda self: True})()  # simula luces encendidas
    eng._base_renderer = base = object()
    eng._renderer = base
    eng.apply_override(library.resolve("preset:rainbow"), "Juego")
    assert eng.override == {"reason": "Juego", "profile": "Rainbow", "reactive": False, "music": False}
    assert eng._renderer is not base
    eng.clear_override()
    assert eng.override is None and eng._renderer is base


def test_ventanas_de_windows():
    # en Windows devuelve algo con sentido; en otros sistemas, vacío
    assert isinstance(foreground_exe(), str)
    assert all("exe" in a for a in running_apps())
