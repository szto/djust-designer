import pytest

from zdesign.edit.classedit import apply_class_change


def test_replaces_existing_class_double_quoted():
    src = '<div class="p-2 text-sm">x</div>\n'
    assert apply_class_change(src, 1, "p-4 text-sm") == '<div class="p-4 text-sm">x</div>\n'


def test_replaces_existing_class_single_quoted():
    src = "<div class='p-2'>x</div>\n"
    assert apply_class_change(src, 1, "p-4") == '<div class="p-4">x</div>\n'


def test_adds_class_when_missing():
    src = "<div>x</div>\n"
    assert apply_class_change(src, 1, "p-4") == '<div class="p-4">x</div>\n'


def test_preserves_other_lines_and_attrs():
    src = 'a\n<button id="b" class="old" data-x="1">Hi</button>\nc\n'
    out = apply_class_change(src, 2, "new")
    assert out == 'a\n<button id="b" class="new" data-x="1">Hi</button>\nc\n'


def test_raises_when_line_out_of_range():
    with pytest.raises(IndexError):
        apply_class_change("<div>x</div>\n", 5, "p-4")
