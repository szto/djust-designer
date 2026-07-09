import pytest

from djust_designer.edit.classedit import apply_class_change


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


def test_raises_when_no_opening_tag():
    with pytest.raises(ValueError):
        apply_class_change("just text here\n", 1, "p-4")


def test_ignores_class_in_html_comment_on_same_line():
    src = '<!-- class="old" --><div class="real">x</div>\n'
    out = apply_class_change(src, 1, "new")
    assert out == '<!-- class="old" --><div class="new">x</div>\n'


def test_ignores_class_word_in_text_content():
    src = '<p>See class="foo" for details</p>\n'
    out = apply_class_change(src, 1, "big")
    # No existing class= inside the <p> tag itself — a new class= is inserted
    # right after the tag name, leaving the text content untouched.
    assert out == '<p class="big">See class="foo" for details</p>\n'
