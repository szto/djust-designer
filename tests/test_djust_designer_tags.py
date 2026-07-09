from django.template import Context, Template
from django.test import override_settings


def _render():
    tpl = Template("{% load djust_designer_tags %}{% djust_designer_scripts %}")
    return tpl.render(Context({}))


def test_djust_designer_scripts_emits_link_and_script_when_debug():
    out = _render()
    assert 'href="/static/djust_designer/overlay.css"' in out
    assert 'src="/static/djust_designer/overlay.js"' in out


@override_settings(DEBUG=False)
def test_djust_designer_scripts_empty_when_not_debug():
    out = _render()
    assert out == ""
