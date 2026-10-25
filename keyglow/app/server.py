"""Servidor HTTP local que sirve la interfaz y una pequeña API JSON.

Solo escucha en 127.0.0.1. Para que una web cualquiera abierta en el navegador no
pueda manejar el teclado, se exige la cabecera Host local y JSON en los POST (un
POST con ``application/json`` desde otro origen requiere un preflight CORS que este
servidor nunca concede).
"""

from __future__ import annotations

import base64
import json
import mimetypes
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .. import __version__
from .. import color as C
from ..effects import REGISTRY
from .. import exporters
from ..importers import from_bytes
from ..keynames import label
from ..layout import BUILTIN, GROUPS, model_choices
from . import gallery_sync, layout_sync, library, system
from .engine import LightEngine, prepare
from .gamedb import installed_games
from .games import GameWatcher, running_apps

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY = 4 * 1024 * 1024

# El registro de Windows a veces asocia .js a text/plain; se fija a mano.
for _ext, _type in ((".js", "application/javascript"), (".css", "text/css"),
                    (".html", "text/html"), (".svg", "image/svg+xml"), (".png", "image/png"),
                    (".ico", "image/x-icon"), (".woff2", "font/woff2")):
    mimetypes.add_type(_type, _ext)


def apply_caps_lock(engine: LightEngine, settings: dict) -> None:
    mode = settings.get("caps_lock", "auto")
    engine.caps_lock = mode if mode in ("auto", "on", "off") else "auto"
    try:
        engine.caps_color = C.to_bytes(C.parse(settings.get("caps_lock_color") or "#ffffff"))
    except ValueError:
        engine.caps_color = (255, 255, 255)


class App:
    """Estado compartido por todas las peticiones."""

    def __init__(self, engine: LightEngine, settings: dict):
        self.engine = engine
        self.settings = settings
        self.quit_event = threading.Event()
        engine.brightness = float(settings.get("brightness", 1.0))
        engine.fps = float(settings.get("fps", 30))
        apply_caps_lock(engine, settings)
        self.games = GameWatcher(engine, lambda: self.settings, library.resolve)

    def meta(self) -> dict:
        lay = self.engine.layout
        effects = {}
        for name, cls in REGISTRY.items():
            doc = (cls.__doc__ or "").strip().split("\n")[0]
            effects[name] = {"defaults": cls.defaults, "doc": doc}
        return {
            "version": __version__,
            "layout": {
                **lay.to_dict(),
                "width": lay.width,
                "height": lay.height,
                "labels": {k: label(k) for k in lay.ids},
            },
            "effects": effects,
            "groups": {g: [k for k in keys if k in lay] for g, keys in GROUPS.items()},
            "layouts": [{"name": n, "title": f().title} for n, f in BUILTIN.items()],
            "model_layouts": model_choices(),
            "export_formats": exporters.FORMATS,
            "openrgb_path": system.find_openrgb(self.settings.get("openrgb_path", "")),
            "openrgb_url": system.OPENRGB_URL,
            "layout_rev": self.engine.layout_rev,
            "user_dir": str(library.user_profiles_dir()),
        }

    def refresh_layouts(self, force: bool = False) -> dict:
        url = self.settings.get("layouts_url") or layout_sync.DEFAULT_URL
        result = layout_sync.refresh(url, force)
        if result["updated"]:
            self.engine.refresh_layout()
        return result

    def import_profile(self, body: dict) -> dict:
        if body.get("url"):
            url = body["url"].strip()
            raw = library._download(url)
            filename = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1] or "Downloaded.json"
        elif "data" in body:  # archivo en base64 (los .orp de OpenRGB son binarios)
            raw = base64.b64decode(body["data"])
            filename = body.get("filename", "imported.json")
        else:
            raw = body.get("text", "").encode("utf-8")
            filename = body.get("filename", "imported.json")
        profile = from_bytes(raw, Path(filename).name)
        adapted, report = prepare(profile.to_dict(), self.engine.layout)
        notable = report.dropped or report.unknown or report.filled
        return {"data": adapted.to_dict(), "report": report.lines() if notable else []}


class Handler(BaseHTTPRequestHandler):
    server_version = "KeyGlow"
    app: App  # se asigna en make_server

    def log_message(self, fmt, *args):  # silencio: la app no tiene consola
        pass

    # --- utilidades --------------------------------------------------------
    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status: int = 200):
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _error(self, msg: str, status: int = 400):
        self._json({"error": msg}, status)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            raise ValueError("Request too large")
        data = json.loads(self.rfile.read(n) or b"{}")
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data

    # --- GET -----------------------------------------------------------------
    def do_GET(self):
        if not self._host_ok():
            return self._error("Host not allowed", 403)
        url = urlparse(self.path)
        app = self.app
        try:
            if url.path == "/api/meta":
                return self._json(app.meta())
            if url.path == "/api/status":
                app.engine.maybe_reconnect()
                return self._json({**app.engine.status(), "app": "keyglow"})
            if url.path == "/api/library":
                return self._json({"presets": library.presets(), "mine": library.mine()})
            if url.path == "/api/community":
                q = parse_qs(url.query)
                src = q.get("url", [app.settings.get("community_url", "")])[0]
                return self._json(library.community(src) if src else gallery_sync.listing())
            if url.path == "/api/settings":
                return self._json({**app.settings, "start_with_windows": system.autostart_enabled()})
            if url.path == "/api/layouts":
                return self._json(layout_sync.status())
            if url.path == "/api/apps":
                return self._json({"apps": running_apps()})
            if url.path == "/api/games":
                return self._json({"installed": installed_games()})
        except Exception as e:  # noqa: BLE001 - se informa a la interfaz
            return self._error(str(e))
        return self._static(url.path)

    def _static(self, path: str):
        if path in ("", "/"):
            path = "/index.html"
        target = (STATIC_DIR / path.lstrip("/")).resolve()
        if STATIC_DIR not in target.parents or not target.is_file():
            return self._error("Not found", 404)
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",):
            ctype += "; charset=utf-8"
        self._send(200, target.read_bytes(), ctype)

    # --- POST ----------------------------------------------------------------
    def do_POST(self):
        if not self._host_ok():
            return self._error("Host not allowed", 403)
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self._error("Expected JSON", HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        app, eng = self.app, self.app.engine
        path = urlparse(self.path).path
        try:
            body = self._body()
            if path == "/api/frames":
                return self._json(eng.frames(body["profile"], float(body.get("start", 0)),
                                             int(body.get("count", 30)),
                                             float(body.get("fps", 30))))
            if path == "/api/apply":
                report = eng.apply(body["profile"])
                app.settings = library.save_settings({"last_profile": body["profile"]})
                return self._json({**eng.status(), "report": report})
            if path == "/api/stop":
                eng.stop()
                return self._json(eng.status())
            if path == "/api/off":
                eng.off()
                return self._json(eng.status())
            if path == "/api/connect":
                eng.connect()
                return self._json(eng.status())
            if path == "/api/capture":
                return self._json({"data": eng.capture()})
            if path == "/api/save":
                entry = library.save_mine(body["profile"], body.get("id"))
                return self._json(entry)
            if path == "/api/delete":
                library.delete_mine(body["id"])
                return self._json({"ok": True})
            if path == "/api/import":
                return self._json(app.import_profile(body))
            if path == "/api/device/save":
                if not body.get("confirm"):
                    return self._json({"summary": eng.onboard_plan(body["profile"]).summary})
                saved = eng.save_to_memory(body["profile"])
                return self._json({**eng.status(), "saved": saved})
            if path == "/api/export":
                fmt = body.get("format", "keyglow")
                profile, _ = prepare(body["profile"], eng.layout)
                content = exporters.export(profile, eng.layout, fmt, float(body.get("at", 0)),
                                           eng.device_description() if fmt == "openrgb" else None)
                return self._json({"filename": exporters.filename(profile, fmt), "content": content})
            if path == "/api/peek":
                eng.peek(body.get("profile"))
                return self._json({"peeking": eng.peeking})
            if path == "/api/community/refresh":
                return self._json(gallery_sync.refresh(force=True))
            if path == "/api/layouts/refresh":
                return self._json(app.refresh_layouts(force=True))
            if path == "/api/openrgb/start":
                result = system.ensure_openrgb(app.settings)
                if result == "missing":
                    return self._error("OpenRGB isn't installed (or not where KeyGlow looks for it).")
                if result == "failed":
                    return self._error("Couldn't start OpenRGB.")
                return self._json({"result": result})
            if path == "/api/settings":
                if "start_with_windows" in body:
                    system.set_autostart(bool(body["start_with_windows"]))
                app.settings = library.save_settings(body)
                eng.brightness = float(app.settings["brightness"])
                eng.fps = float(app.settings["fps"])
                apply_caps_lock(eng, app.settings)
                eng.set_layout_mode(app.settings["layout"], app.settings["openrgb_device"])
                return self._json({**app.settings, "start_with_windows": system.autostart_enabled()})
            if path == "/api/quit":
                self._json({"ok": True})
                app.quit_event.set()
                return None
        except KeyError as e:
            return self._error(f"Missing field {e}")
        except Exception as e:  # noqa: BLE001 - se informa a la interfaz
            return self._error(str(e))
        return self._error("Not found", 404)


def make_server(app: App, port: int = 47821) -> ThreadingHTTPServer:
    handler = type("KeyGlowHandler", (Handler,), {"app": app})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    server.daemon_threads = True
    return server
