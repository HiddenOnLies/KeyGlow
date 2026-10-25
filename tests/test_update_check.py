import json

import pytest

from keyglow.app import library, update_check as U


@pytest.fixture(autouse=True)
def appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(library, "app_data_dir", lambda: tmp_path)
    monkeypatch.setattr(U, "__version__", "0.4.0")


def releases(tmp_path, *tags, draft=None):
    f = tmp_path / "releases.json"
    f.write_text(json.dumps([{"tag_name": t, "draft": t == draft, "prerelease": True,
                              "html_url": f"https://example.invalid/{t}"} for t in tags]), encoding="utf-8")
    return f.as_uri()


def test_version_order():
    assert U.version_tuple("v0.10.0") > U.version_tuple("v0.9.9") > U.version_tuple("0.4.0-beta")
    assert U.newest([{"tag_name": "v0.2.0"}, {"tag_name": "v0.10.0"}, {"tag_name": "v0.4.0"}])["tag_name"] == "v0.10.0"


def test_tells_about_a_newer_release(tmp_path):
    s = U.check(force=True, url=releases(tmp_path, "v0.3.0", "v0.5.0", "v0.4.0"))
    assert s["newer"] and s["latest"] == "v0.5.0" and s["url"].endswith("v0.5.0") and not s["skipped"]


def test_same_or_older_is_not_new(tmp_path):
    assert not U.check(force=True, url=releases(tmp_path, "v0.4.0", "v0.3.0"))["newer"]


def test_drafts_are_ignored(tmp_path):
    assert U.check(force=True, url=releases(tmp_path, "v0.4.0", "v0.9.0", draft="v0.9.0"))["latest"] == "v0.4.0"


def test_skipping_a_version_hides_it_until_a_newer_one(tmp_path):
    U.check(force=True, url=releases(tmp_path, "v0.5.0"))
    assert U.status(skipped="v0.5.0")["skipped"]
    U.check(force=True, url=releases(tmp_path, "v0.6.0"))
    assert not U.status(skipped="v0.5.0")["skipped"]


def test_checks_once_a_day_and_keeps_the_answer_offline(tmp_path):
    U.check(force=True, url=releases(tmp_path, "v0.5.0"))
    assert U.check(url=(tmp_path / "missing.json").as_uri())["latest"] == "v0.5.0"     # no vuelve a preguntar
    s = U.check(force=True, url=(tmp_path / "missing.json").as_uri())
    assert s["latest"] == "v0.5.0" and s["error"]                                       # sin conexión
