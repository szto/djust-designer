"""Rewrite the `class="..."` attribute of the first opening tag on a given line.

Pure. Operates on the template file's original source. If no class attribute
exists inside the target tag, one is inserted immediately after the tag name.

Single-quoted class values are normalized to double quotes on rewrite;
adjacent attributes are left untouched.

NOTE: single-line opening tags only. Multi-line tags (with the ``class``
attribute on a continuation line) are a P3 concern — see the plan's
Post-P1 section.
"""

from __future__ import annotations

import re

_CLASS = re.compile(r"""\bclass\s*=\s*(?P<q>["'])(?P<val>.*?)(?P=q)""")
_TAG = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)")


def apply_class_change(source: str, line: int, new_class: str) -> str:
    lines = source.splitlines(keepends=True)
    if line < 1 or line > len(lines):
        raise IndexError(f"line {line} out of range (1..{len(lines)})")
    idx = line - 1
    target = lines[idx]

    tm = _TAG.search(target)
    if not tm:
        raise ValueError(f"no opening tag on line {line}")

    # Search for class= only inside the opening tag's angle-bracket span.
    close = target.find(">", tm.end())
    tag_end = close + 1 if close != -1 else len(target)
    tag_span = target[tm.start() : tag_end]

    m = _CLASS.search(tag_span)
    if m:
        abs_start = tm.start() + m.start()
        abs_end = tm.start() + m.end()
        new_line = target[:abs_start] + f'class="{new_class}"' + target[abs_end:]
    else:
        new_line = target[: tm.end()] + f' class="{new_class}"' + target[tm.end() :]

    lines[idx] = new_line
    return "".join(lines)
