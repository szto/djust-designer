from django.template import Context, Template
from django.test import override_settings


def _render():
    tpl = Template("{% load zdesign_tags %}{% zdesign_scripts %}")
    return tpl.render(Context({}))


def test_zdesign_scripts_emits_link_and_script_when_debug():
    out = _render()
    assert 'href="/static/zdesign/overlay.css"' in out
    assert 'src="/static/zdesign/overlay.js"' in out


@override_settings(DEBUG=False)
def test_zdesign_scripts_empty_when_not_debug():
    out = _render()
    assert out == ""
