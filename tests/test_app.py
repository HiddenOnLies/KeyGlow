"""Pruebas de la aplicación (servidor + biblioteca) sin hardware."""

import json
import threading
import urllib.error
import urllib.request

import pytest

from keyglow.app import library
from keyglow.app.engine import LightEngine
from keyglow.app.server import App, make_server


@pytest.fixture()
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setattr(library, "_documents_dir", lambda: tmp_path / "docs")
    app = App(LightEngine(), library.load_settings())
    srv = make_server(app, 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", tmp_path
    srv.shutdown()


def call(base, path, body=None, headers=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, headers={
        "Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def test_meta_y_biblioteca(server):
    base, _ = server
    meta = call(base, "/api/meta")
    assert meta["layout"]["name"] == "alloy_origins_65"
    assert "rainbow_wave" in meta["effects"]
    lib = call(base, "/api/library")
    names = {e["name"] for e in lib["presets"]}
    assert {"Aurora", "Rainbow", "Gaming WASD"} <= names
    assert lib["mine"] == []
    gallery = call(base, "/api/community")
    assert len(gallery["profiles"]) >= 3 and all(e["data"] for e in gallery["profiles"])


def test_todos_los_predeterminados_renderizan(server):
    base, _ = server
    for entry in call(base, "/api/library")["presets"]:
        r = call(base, "/api/frames", {"profile": entry["data"], "start": 0.5, "count": 3})
        assert len(r["frames"]) == 3 and len(r["frames"][0]) == len(r["keys"])


def test_guardar_y_borrar(server):
    base, tmp = server
    prof = {"format": "keyglow/1", "name": "Mine ñ", "layers": [{"effect": "solid", "params": {"color": "#f00"}}]}
    entry = call(base, "/api/save", {"profile": prof})
    assert entry["id"] == "mine:mine_n"
    assert (tmp / "docs" / "KeyGlow" / "Perfiles" / "mine_n.json").exists()
    call(base, "/api/save", {"profile": {**prof, "name": "Otro"}, "id": entry["id"]})
    assert [e["name"] for e in call(base, "/api/library")["mine"]] == ["Otro"]
    call(base, "/api/delete", {"id": entry["id"]})
    assert call(base, "/api/library")["mine"] == []


def test_importar_adapta_nombres(server):
    base, _ = server
    r = call(base, "/api/import", {"text": json.dumps({"Key: W": "#f00", "Number Pad 1": "#0f0"}),
                                   "filename": "mapa.json"})
    assert r["data"]["layers"][0]["params"]["keys"] == {"W": "#f00"}
    assert r["report"]


def test_perfil_invalido_da_error(server):
    base, _ = server
    with pytest.raises(urllib.error.HTTPError) as e:
        call(base, "/api/frames", {"profile": {"layers": [{"effect": "nope"}]}})
    assert e.value.code == 400


def test_rechaza_host_ajeno_y_post_sin_json(server):
    base, _ = server
    with pytest.raises(urllib.error.HTTPError) as e:
        call(base, "/api/meta", headers={"Host": "evil.example"})
    assert e.value.code == 403
    req = urllib.request.Request(base + "/api/stop", data=b"{}", headers={"Content-Type": "text/plain"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 415


def test_ajustes_persisten(server):
    base, tmp = server
    call(base, "/api/settings", {"brightness": 0.5, "desconocido": 1})
    saved = json.loads((tmp / "appdata" / "KeyGlow" / "settings.json").read_text(encoding="utf-8"))
    assert saved["brightness"] == 0.5 and "desconocido" not in saved


def test_a_new_window_opens_on_the_active_profile(server):
    base, _ = server
    assert call(base, "/api/active")["profile"] is None              # nada en marcha todavía
