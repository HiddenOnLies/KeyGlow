import json

import pytest

from keyglow import gallery
from keyglow.app import gallery_sync, library

GOOD = {"format": "keyglow/1", "name": "Glow", "author": "me", "tags": ["chill"],
        "layers": [{"effect": "solid", "params": {"color": "#ff0000"}}]}


@pytest.fixture(autouse=True)
def appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(library, "app_data_dir", lambda: tmp_path)


@pytest.mark.parametrize("bad", [
    {**GOOD, "layers": []},
    {**GOOD, "layers": [{"effect": "nope"}]},
    {**GOOD, "layers": [{"effect": "solid", "params": {"color": "not a color"}}]},
    {**GOOD, "layers": [{"effect": "image", "params": {"path": "C:/Users/someone/secret.png"}}]},
    {**GOOD, "layers": ["solid"]},
    {**GOOD, "name": ""},
    {**GOOD, "tags": "chill"},
    {**GOOD, "description": "x" * 1000},
])
def test_rejects_bad_profiles(bad):
    with pytest.raises(ValueError):
        gallery.validate_profile(bad, "glow")


def test_rejects_bad_ids():
    with pytest.raises(ValueError):
        gallery.validate_profile(GOOD, "../evil")


def bundle_file(tmp_path, profiles):
    f = tmp_path / "gallery.json"
    f.write_text(json.dumps({"format": gallery.FORMAT, "profiles": profiles}), encoding="utf-8")
    return f


def test_refresh_downloads_validates_and_caches(tmp_path):
    f = bundle_file(tmp_path, [{"id": "glow", "profile": GOOD}, {"id": "bad", "profile": {"layers": []}}])
    r = gallery_sync.refresh(f.as_uri(), force=True)
    assert r["updated"] and r["count"] == 1 and not r["error"]  # el inválido se descarta
    listing = gallery_sync.listing()
    assert [e["id"] for e in listing["profiles"]] == ["community:glow"] and listing["fetched"]
    # sin conexión se mantiene la caché, y no se vuelve a descargar antes de un día
    assert gallery_sync.refresh((tmp_path / "missing.json").as_uri(), force=True)["error"]
    assert gallery_sync.listing()["profiles"][0]["name"] == "Glow"
    assert gallery_sync.refresh(f.as_uri())["updated"] is False


def test_bundled_copy_is_used_before_the_first_download():
    listing = gallery_sync.listing()
    assert listing["fetched"] == 0 and len(listing["profiles"]) >= 10
    assert all(e["data"]["layers"] for e in listing["profiles"])


def test_bundled_copy_is_a_valid_gallery():
    entries = gallery.parse(gallery_sync.BUNDLED.read_bytes())  # ninguno se descarta
    raw = json.loads(gallery_sync.BUNDLED.read_text(encoding="utf-8"))["profiles"]
    assert len(entries) == len(raw)


def test_rejects_files_that_are_not_galleries(tmp_path):
    other = tmp_path / "layouts.json"
    other.write_text('{"format": "keyglow-layouts/1", "layouts": []}', encoding="utf-8")
    assert gallery_sync.refresh(other.as_uri(), force=True)["error"]


def test_check_finds_duplicate_names(tmp_path):
    for stem in ("a", "b"):
        (tmp_path / f"{stem}.json").write_text(json.dumps(GOOD), encoding="utf-8")
    good, errors = gallery.check([str(tmp_path)])
    assert len(good) == 2 and any("Glow" in e or "glow" in e for e in errors)
