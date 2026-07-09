import json

import pytest
from django.template.loader import get_template
from django.test import Client

from zdesign.instrument.registry import registry


@pytest.mark.django_db
def test_resolve_returns_entry_for_known_id():
    registry.reset()
    get_template("home.html").render({})  # populate registry

    c = Client()
    r = c.post(
        "/__zdesign__/resolve",
        data=json.dumps({"zd_id": "zd1"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    body = r.json()
    assert body["tag"] == "div"
    assert body["line"] == 1


@pytest.mark.django_db
def test_resolve_404_for_unknown_id():
    registry.reset()
    c = Client()
    r = c.post(
        "/__zdesign__/resolve",
        data=json.dumps({"zd_id": "nope"}),
        content_type="application/json",
    )
    assert r.status_code == 404


@pytest.mark.django_db
def test_edit_class_rewrites_source_and_supports_undo(tmp_path, settings):
    # Point BASE_DIR at a tmp so backups land in tmp
    settings.BASE_DIR = tmp_path

    # Copy fixture template into an editable tmp location and register it manually
    src_file = tmp_path / "home.html"
    src_file.write_text('<div class="p-2">x</div>\n')

    registry.reset()
    registry.update(
        {
            "zd1": {"file": str(src_file), "line": 1, "col": 1, "tag": "div"},
        }
    )

    # Allow writes into tmp_path by overriding TEMPLATES DIRS via settings
    settings.TEMPLATES = [
        {
            **settings.TEMPLATES[0],
            "DIRS": [str(tmp_path)],
        }
    ]

    c = Client()
    r = c.post(
        "/__zdesign__/edit/class",
        data=json.dumps({"zd_id": "zd1", "class": "p-4"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    assert src_file.read_text() == '<div class="p-4">x</div>\n'

    r = c.post("/__zdesign__/undo", content_type="application/json")
    assert r.status_code == 200
    assert src_file.read_text() == '<div class="p-2">x</div>\n'


@pytest.mark.django_db
def test_resolve_rejects_non_loopback():
    registry.reset()
    registry.update({"zd1": {"file": "x", "line": 1, "col": 1, "tag": "div"}})
    c = Client(REMOTE_ADDR="10.0.0.1")
    r = c.post(
        "/__zdesign__/resolve",
        data=json.dumps({"zd_id": "zd1"}),
        content_type="application/json",
    )
    assert r.status_code == 403


@pytest.mark.django_db
def test_edit_class_rejects_html_injection(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    src_file = tmp_path / "home.html"
    src_file.write_text('<div class="p-2">x</div>\n')
    registry.reset()
    registry.update({"zd1": {"file": str(src_file), "line": 1, "col": 1, "tag": "div"}})
    settings.TEMPLATES = [{**settings.TEMPLATES[0], "DIRS": [str(tmp_path)]}]

    c = Client()
    r = c.post(
        "/__zdesign__/edit/class",
        data=json.dumps({"zd_id": "zd1", "class": 'p-4"><script>x</script>'}),
        content_type="application/json",
    )
    assert r.status_code == 400
    # File must be untouched.
    assert src_file.read_text() == '<div class="p-2">x</div>\n'
