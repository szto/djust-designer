from zdesign.instrument.registry import SourceMapRegistry


def test_counter_allocates_disjoint_ranges():
    r = SourceMapRegistry()
    assert r.next_start(3) == 1
    assert r.next_start(2) == 4
    assert r.next_start(1) == 6


def test_update_and_get():
    r = SourceMapRegistry()
    r.update({"zd1": {"file": "t.html", "line": 1, "col": 1, "tag": "div"}})
    entry = r.get("zd1")
    assert entry is not None
    assert entry["tag"] == "div"
    assert r.get("missing") is None


def test_reset_clears_everything():
    r = SourceMapRegistry()
    r.next_start(5)
    r.update({"zd1": {"file": "t.html", "line": 1, "col": 1, "tag": "div"}})
    r.reset()
    assert r.get("zd1") is None
    assert r.next_start(1) == 1
