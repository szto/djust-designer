from zdesign.edit.snapshot import Backups


def test_snapshot_then_undo_restores_original(tmp_path):
    root = tmp_path
    f = root / "home.html"
    f.write_text("original\n")
    b = Backups(str(root))
    b.snapshot(str(f))
    f.write_text("modified\n")

    restored = b.undo_last()
    assert restored == str(f)
    assert f.read_text() == "original\n"


def test_undo_is_lifo_across_multiple_edits(tmp_path):
    f = tmp_path / "home.html"
    f.write_text("v0")
    b = Backups(str(tmp_path))
    b.snapshot(str(f))
    f.write_text("v1")
    b.snapshot(str(f))
    f.write_text("v2")

    b.undo_last()
    assert f.read_text() == "v1"
    b.undo_last()
    assert f.read_text() == "v0"


def test_undo_last_returns_none_when_empty(tmp_path):
    b = Backups(str(tmp_path))
    assert b.undo_last() is None
