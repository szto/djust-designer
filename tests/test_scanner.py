from zdesign.instrument.scanner import instrument_html


def test_injects_id_and_records_position():
    src = '<div class="a">\n<button>Hi</button>\n</div>'
    out, smap = instrument_html(src, "t.html", start=1)
    assert out.startswith('<div data-zd-id="zd1" class="a">')
    assert '<button data-zd-id="zd2">Hi</button>' in out
    assert smap["zd1"] == {"file": "t.html", "line": 1, "col": 1, "tag": "div"}
    assert smap["zd2"]["line"] == 2
    assert smap["zd2"]["tag"] == "button"
    assert "zd3" not in smap  # closing </div> not counted


def test_skips_head_and_script_style():
    src = "<html><head><meta><title>t</title></head><body><p>x</p><script>a=1</script><style>b</style></body></html>"
    _, smap = instrument_html(src, "t.html", start=1)
    tags = [v["tag"] for v in smap.values()]
    assert "html" not in tags
    assert "head" not in tags
    assert "meta" not in tags
    assert "title" not in tags
    assert "script" not in tags
    assert "style" not in tags
    assert "body" in tags
    assert "p" in tags


def test_ignores_closing_and_doctype_and_django_tags():
    src = "<!DOCTYPE html>\n{% if x %}<p>{{ v }}</p>{% endif %}"
    out, smap = instrument_html(src, "t.html", start=1)
    assert list(smap.keys()) == ["zd1"]
    assert smap["zd1"]["tag"] == "p"
    assert '<p data-zd-id="zd1">' in out


def test_start_offset_is_honored():
    src = "<p>x</p>"
    _, smap = instrument_html(src, "t.html", start=42)
    assert list(smap.keys()) == ["zd42"]


def test_col_is_one_based_from_line_start():
    src = "  <div>x</div>"
    _, smap = instrument_html(src, "t.html", start=1)
    assert smap["zd1"]["col"] == 3
