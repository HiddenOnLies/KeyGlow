"""Integración con el sistema: arrancar OpenRGB y abrir KeyGlow al iniciar Windows.

Para que KeyGlow funcione "descargar y usar", hace falta que el servidor SDK de OpenRGB
esté en marcha. Si no lo está y OpenRGB está instalado, KeyGlow lo abre minimizado y con
el servidor activo (``OpenRGB --server --startminimized``).
"""

from __future__ import annotations

import os
import shutil
import socket
import sys
from pathlib import Path

OPENRGB_URL = "https://openrgb.org/releases.html"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "KeyGlow"


# --- OpenRGB ---------------------------------------------------------------------
def find_openrgb(custom: str = "") -> str | None:
    """Ruta de ``OpenRGB.exe`` (la indicada en ajustes o las habituales), o ``None``."""
    candidates = [custom] if custom else []
    for env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            candidates += [str(Path(base) / "OpenRGB" / "OpenRGB.exe"),
                           str(Path(base) / "Programs" / "OpenRGB" / "OpenRGB.exe")]
    found = shutil.which("OpenRGB") or shutil.which("openrgb")
    if found:
        candidates.append(found)
    return next((c for c in candidates if c and Path(c).is_file()), None)


def server_up(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def is_local(host: str) -> bool:
    return host in ("127.0.0.1", "localhost", "::1")


def start_openrgb(path: str, port: int = 6742) -> None:
    """Abre OpenRGB minimizado con el servidor SDK. Si OpenRGB pide permisos de
    administrador, Windows muestra su aviso (por eso se usa ShellExecute)."""
    args = ["--server", "--startminimized"]
    if port != 6742:
        args += ["--server-port", str(port)]
    if sys.platform == "win32":
        os.startfile(path, arguments=" ".join(args), cwd=str(Path(path).parent))  # noqa: S606
    else:
        import subprocess
        subprocess.Popen([path, *args], cwd=str(Path(path).parent), start_new_session=True)


def ensure_openrgb(settings: dict) -> str:
    """Arranca OpenRGB si hace falta y se puede. Devuelve qué ha pasado (para el registro)."""
    host, port = settings["openrgb_host"], int(settings["openrgb_port"])
    if not is_local(host) or server_up(host, port):
        return "running"
    path = find_openrgb(settings.get("openrgb_path", ""))
    if not path:
        return "missing"
    try:
        start_openrgb(path, port)
    except OSError:
        return "failed"
    return "started"


# --- inicio con Windows -------------------------------------------------------------
def launch_command() -> str:
    """Orden para abrir KeyGlow en segundo plano (sin ventana) al iniciar sesión."""
    if getattr(sys, "frozen", False):  # KeyGlow.exe
        return f'"{sys.executable}" --no-window'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    exe = pythonw if pythonw.is_file() else Path(sys.executable)
    return f'"{exe}" -m keyglow.app.main --no-window'


def autostart_enabled(key: str = RUN_KEY) -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            winreg.QueryValueEx(k, RUN_NAME)
            return True
    except OSError:
        return False


def set_autostart(enabled: bool, key: str = RUN_KEY) -> None:
    if sys.platform != "win32":
        return
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
        if enabled:
            winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, launch_command())
        else:
            try:
                winreg.DeleteValue(k, RUN_NAME)
            except FileNotFoundError:
                pass
