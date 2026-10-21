"""Servidor HTTP local que sirve la interfaz y una pequeña API JSON.

Solo escucha en 127.0.0.1. Para que una web cualquiera abierta en el navegador no
pueda manejar el teclado, se exige la cabecera Host local y JSON en los POST (un
POST con ``application/json`` desde otro origen requiere un preflight CORS que este
servidor nunca concede).
"""

from __future__ import annotations

import json
import mimetypes
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .. import __version__
from ..effects import REGISTRY
from ..importers import from_csv_text, from_json_data
from ..keynames import label
from ..layout import GROUPS
from . import library
from .engine import LightEngine, prepare
from .gamedb import installed_games
from .games import GameWatcher, running_apps

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY = 4 * 1024 * 1024

# El registro de Windows a veces asocia .js a text/plain; se fija a mano.
for _ext, _type in ((".js", "application/javascript"), (".css", "text/css"),
                    (".html", "text/html"), (".svg", "image/svg+xml"), (".png", "image/png"),
                    (".ico", "image/x-icon")):
    mimetypes.add_type(_type, _ext)


class App:
    """Estado compartido por todas las peticiones."""

    def __init__(self, engine: LightEngine, settings: dict):
        self.engine = engine
        self.settings = settings
        self.quit_event = threading.Event()
        engine.brightness = float(settings.get("brightness", 1.0))
        engine.fps = float(settings.get("fps", 30))
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
            "user_dir": str(library.user_profiles_dir()),
        }

    def import_profile(self, body: dict) -> dict:
        if body.get("url"):
            url = body["url"].strip()
            raw = library._download(url).decode("utf-8")
            name = url.rstrip("/").rsplit("/", 1)[-1].rsplit(".", 1)[0] or "Downloaded"
            text, filename = raw, url
        else:
            text, filename = body.get("text", ""), body.get("filename", "imported.json")
            name = Path(filename).stem or "Imported"
        if filename.lower().endswith(".csv"):
            profile = from_csv_text(text, name)
        else:
            profile = from_json_data(json.loads(text), name)
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
                return self._json(library.community(src))
            if url.path == "/api/settings":
                return self._json(app.settings)
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
            if path == "/api/settings":
                app.settings = library.save_settings(body)
                eng.brightness = float(app.settings["brightness"])
                eng.fps = float(app.settings["fps"])
                return self._json(app.settings)
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
