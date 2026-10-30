"""Perfiles por juego: cambia de perfil cuando una aplicación concreta está en primer plano.

Es lo que hacen G HUB o Synapse con sus "perfiles vinculados": se elige un ejecutable
(``cs2.exe``, ``League of Legends.exe``...) y el perfil que debe usarse mientras esa
ventana tiene el foco. Al cambiar a otra ventana vuelve el perfil normal.

Solo funciona en Windows (usa la API Win32 mediante ctypes, sin dependencias).
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

from . import conflicts
from .gamedb import lookup

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.IsWindowVisible.argtypes = [wintypes.HWND]
    _user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    _user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                     ctypes.POINTER(wintypes.DWORD)]
    _ENUM_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _exe_of_window(hwnd) -> str:
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""
    handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        if _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        _kernel32.CloseHandle(handle)


def foreground_exe() -> str:
    """Nombre del ejecutable de la ventana activa, en minúsculas (``cs2.exe``)."""
    if sys.platform != "win32":
        return ""
    hwnd = _user32.GetForegroundWindow()
    return Path(_exe_of_window(hwnd)).name.lower() if hwnd else ""


# Ventanas del sistema que no tiene sentido ofrecer como "juego".
_IGNORE = {"explorer.exe", "searchhost.exe", "shellexperiencehost.exe", "startmenuexperiencehost.exe",
           "textinputhost.exe", "applicationframehost.exe", "systemsettings.exe", "keyglow.exe"}


def running_apps() -> list[dict]:
    """Aplicaciones con ventana visible, para elegir a cuál vincular un perfil."""
    if sys.platform != "win32":
        return []
    found: dict[str, dict] = {}

    def cb(hwnd, _):
        if not _user32.IsWindowVisible(hwnd):
            return True
        n = _user32.GetWindowTextLengthW(hwnd)
        if n == 0:
            return True
        path = _exe_of_window(hwnd)
        exe = Path(path).name.lower()
        if exe and exe not in _IGNORE and exe not in found:
            title = ctypes.create_unicode_buffer(n + 1)
            _user32.GetWindowTextW(hwnd, title, n + 1)
            found[exe] = {"exe": exe, "title": title.value, "path": path}
        return True

    _user32.EnumWindows(_ENUM_PROC(cb), 0)
    return sorted(found.values(), key=lambda a: a["title"].lower())


class GameWatcher:
    """Mira la ventana activa cada segundo y aplica el perfil vinculado, si lo hay."""

    def __init__(self, engine, get_settings, resolve_profile, interval: float = 1.0):
        self.engine = engine
        self.get_settings = get_settings
        self.resolve_profile = resolve_profile
        self.interval = interval
        self.active: dict | None = None  # regla en uso
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="keyglow-juegos", daemon=True)
        self._conflicts_at = 0.0

    def start(self) -> None:
        if sys.platform == "win32":
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            try:
                self.engine.housekeeping()
                exe = foreground_exe()
                self.engine.foreground = exe  # para los atajos de cada aplicación
                self.check(exe)
                self.check_conflicts()
            except Exception:  # noqa: BLE001 - un fallo puntual no debe parar el vigilante
                pass

    def check_conflicts(self) -> None:
        """Otros programas RGB abiertos. Sin teclado se avisa de todos (pueden ser la causa);
        con teclado, solo de los de su marca (son los que se pelean con KeyGlow)."""
        import time
        device = self.engine.device_name
        now = time.monotonic()
        if now - self._conflicts_at < (5 if not device else 30):  # mirar procesos cuesta unos ms
            return
        self._conflicts_at = now
        apps = conflicts.running()
        self.engine.conflicts = conflicts.for_keyboard(apps, device) if device else apps

    def check(self, exe: str) -> None:
        settings = self.get_settings()
        rules = settings.get("game_rules") or []
        rule = None
        if settings.get("game_switching", True) and self.engine.running:
            rule = next((r for r in rules if r.get("exe", "").lower() == exe), None)
            if rule is None and settings.get("auto_games") and exe:
                # opcional: juego conocido sin perfil elegido -> preset recomendado de su género
                game = lookup(exe)
                if game:
                    rule = {"exe": exe, "name": game["name"], "profile_id": game["profile_id"]}
        if rule is not None:
            # también si el perfil temporal se perdió (p. ej. se volvió a encender la luz)
            if self.active is None or self.active.get("exe") != rule["exe"] or self.engine.override is None:
                profile = self.resolve_profile(rule.get("profile_id", ""))
                if profile is not None:
                    self.engine.apply_override(profile, rule.get("name") or rule["exe"])
                    self.active = rule
        elif self.active is not None:
            self.active = None
            self.engine.clear_override()
