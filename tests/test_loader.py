import pytest
from django.template.loader import get_template

from zdesign.instrument.registry import registry


@pytest.mark.django_db
def test_loader_injects_ids_and_populates_registry():
    registry.reset()
    tpl = get_template("home.html")
    rendered = tpl.render({})
    assert 'data-zd-id="zd1"' in rendered
    assert 'data-zd-id="zd2"' in rendered
    entry = registry.get("zd1")
    assert entry is not None
    assert entry["tag"] == "div"
    assert entry["line"] == 1
