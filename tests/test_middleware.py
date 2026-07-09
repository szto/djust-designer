from unittest.mock import Mock

from django.http import HttpResponse, StreamingHttpResponse
from django.test import override_settings

from zdesign.middleware import ZdesignMiddleware


def _mw():
    return ZdesignMiddleware(get_response=lambda r: r)


def test_injects_assets_into_html_response_when_debug():
    resp = HttpResponse("<html><body>hi</body></html>", content_type="text/html")
    out = _mw().process_response(Mock(), resp)
    body = out.content.decode()
    assert "zdesign/overlay.js" in body
    assert "zdesign/overlay.css" in body
    assert body.endswith("</body></html>")


@override_settings(DEBUG=False)
def test_no_inject_when_debug_false():
    resp = HttpResponse("<html><body>hi</body></html>", content_type="text/html")
    out = _mw().process_response(Mock(), resp)
    assert "zdesign/overlay.js" not in out.content.decode()


def test_no_inject_for_non_html():
    resp = HttpResponse('{"ok": true}', content_type="application/json")
    out = _mw().process_response(Mock(), resp)
    assert "zdesign/overlay.js" not in out.content.decode()


def test_no_inject_for_streaming_response():
    resp = StreamingHttpResponse(
        iter([b"<html><body>x</body></html>"]),
        content_type="text/html",
    )
    out = _mw().process_response(Mock(), resp)
    # StreamingHttpResponse has no `.content`; middleware should pass through unchanged
    assert getattr(out, "streaming", False) is True


def test_idempotent_when_already_injected():
    src = '<html><body>x<script src="/static/zdesign/overlay.js"></script></body></html>'
    resp = HttpResponse(src, content_type="text/html")
    out = _mw().process_response(Mock(), resp)
    assert out.content.decode().count("zdesign/overlay.js") == 1
