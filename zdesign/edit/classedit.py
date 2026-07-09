"""Rewrite the `class="..."` attribute of the first opening tag on a given line.

Pure. Operates on the template file's original source. If no class attribute
exists, one is inserted immediately after the tag name.
"""

from __future__ import annotations

import re

_CLASS = re.compile(r"""\bclass\s*=\s*(?P<q>["'])(?P<val>.*?)(?P=q)""", re.DOTALL)
_TAG = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)")


def apply_class_change(source: str, line: int, new_class: str) -> str:
    lines = source.splitlines(keepends=True)
    if line < 1 or line > len(lines):
        raise IndexError(f"line {line} out of range (1..{len(lines)})")
    idx = line - 1
    target = lines[idx]

    m = _CLASS.search(target)
    if m:
        replacement = f'class="{new_class}"'
        new_line = target[: m.start()] + replacement + target[m.end() :]
    else:
        tm = _TAG.search(target)
        if not tm:
            raise ValueError(f"no opening tag on line {line}")
        insert_at = tm.end()
        new_line = target[:insert_at] + f' class="{new_class}"' + target[insert_at:]
    lines[idx] = new_line
    return "".join(lines)
