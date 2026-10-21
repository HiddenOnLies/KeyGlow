"""Punto de entrada de la aplicación de escritorio (``keyglow-app`` / KeyGlow.exe).

Arranca el servidor local, abre la interfaz en una ventana propia (Edge o Chrome
en modo aplicación, o el navegador por defecto) y deja un icono en la bandeja del
sistema para reabrirla, apagar las luces o salir. Las luces siguen funcionando
aunque se cierre la ventana.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

from . import library, system
from .engine import LightEngine
from .server import STATIC_DIR, App, make_server

DEFAULT_PORT = 47821


def _already_running(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=1) as r:
            return json.loads(r.read()).get("app") == "keyglow"
    except (OSError, ValueError):
        return False


def _browser_candidates() -> list[str]:
    found = []
    for env in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if not base:
            continue
        found += [str(Path(base) / "Microsoft/Edge/Application/msedge.exe"),
                  str(Path(base) / "Google/Chrome/Application/chrome.exe")]
    for name in ("msedge", "chrome", "chromium", "google-chrome"):
        exe = shutil.which(name)
        if exe:
            found.append(exe)
    return [p for p in found if Path(p).is_file()]


def open_window(url: str) -> None:
    """Abre la interfaz como ventana de aplicación (sin pestañas ni barra de direcciones)."""
    profile_dir = library.app_data_dir() / "ventana"
    for exe in _browser_candidates():
        try:
            subprocess.Popen([exe, f"--app={url}", "--window-size=1440,900",
                              f"--user-data-dir={profile_dir}", "--no-first-run",
                              "--no-default-browser-check"],
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return
        except OSError:
            continue
    webbrowser.open(url)


def _run_tray(app: App, url: str) -> bool:
    """Icono en la bandeja. Devuelve False si pystray no está disponible."""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        return False
    icon_img = Image.open(STATIC_DIR / "icon.png")

    def on_open(icon, item):
        open_window(url)

    def on_off(icon, item):
        app.engine.off()

    def on_quit(icon, item):
        app.quit_event.set()

    icon = pystray.Icon("KeyGlow", icon_img, "KeyGlow", menu=pystray.Menu(
        pystray.MenuItem("Open KeyGlow", on_open, default=True),
        pystray.MenuItem("Lights off", on_off),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    ))
    threading.Thread(target=lambda: (app.quit_event.wait(), icon.stop()), daemon=True).start()
    icon.run()
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="keyglow-app", description="KeyGlow app")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--no-window", action="store_true", help="do not open the window on start")
    p.add_argument("--no-tray", action="store_true", help="no system tray icon")
    p.add_argument("--layout", help="keyboard layout name or .json (default: from settings, 'auto')")
    args = p.parse_args(argv)
    url = f"http://127.0.0.1:{args.port}/"

    if _already_running(args.port):
        open_window(url)  # segunda instancia: solo muestra la ventana de la primera
        return 0

    settings = library.load_settings()
    if settings.get("start_openrgb"):
        system.ensure_openrgb(settings)  # el motor reintenta conectar hasta que OpenRGB responda
    engine = LightEngine(args.layout or settings["layout"], settings["openrgb_host"],
                         int(settings["openrgb_port"]), settings["openrgb_device"],
                         cached_layout=settings.get("device_layout"),
                         on_layout=lambda lay: library.save_settings({"device_layout": lay.to_dict()}))
    app = App(engine, settings)
    server = make_server(app, args.port)
    threading.Thread(target=server.serve_forever, name="keyglow-http", daemon=True).start()
    app.games.start()

    if settings.get("apply_last_on_start") and settings.get("last_profile"):
        try:
            engine.apply(settings["last_profile"])
        except Exception:  # noqa: BLE001 - un perfil roto no debe impedir arrancar
            pass
    if not args.no_window:
        open_window(url)
    if sys.stdout is not None:
        print(f"KeyGlow running at {url} (Ctrl+C to quit)")

    try:
        if args.no_tray or not _run_tray(app, url):
            while not app.quit_event.wait(0.5):
                pass
    except KeyboardInterrupt:
        pass
    finally:
        app.games.stop()
        engine.stop()
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
