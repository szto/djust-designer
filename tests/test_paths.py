import os

import pytest

from zdesign.edit.paths import resolve_within


def test_returns_realpath_when_within_root(tmp_path):
    root = tmp_path / "templates"
    root.mkdir()
    f = root / "home.html"
    f.write_text("x")
    got = resolve_within(str(f), [str(root)])
    assert got == os.path.realpath(str(f))


def test_raises_on_traversal(tmp_path):
    root = tmp_path / "templates"
    root.mkdir()
    outside = tmp_path / "secrets.txt"
    outside.write_text("x")
    with pytest.raises(PermissionError):
        resolve_within(str(outside), [str(root)])


def test_multiple_roots_any_match(tmp_path):
    r1 = tmp_path / "a"
    r1.mkdir()
    r2 = tmp_path / "b"
    r2.mkdir()
    f = r2 / "t.html"
    f.write_text("x")
    got = resolve_within(str(f), [str(r1), str(r2)])
    assert got == os.path.realpath(str(f))
