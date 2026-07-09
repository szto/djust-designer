"""Injects data-zd-id into HTML opening tags and records source positions.

Pure. No Django. Operates on template source text — positions refer to the
ORIGINAL (pre-injection) source, so the sourcemap remains valid for
writing back to disk.
"""

from __future__ import annotations

import re

_OPEN_TAG = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)")

# Tags we do not annotate — either meaningless to select (structural) or
# would break if given an extra attribute (raw text / metadata contexts).
_SKIP = frozenset({"html", "head", "meta", "link", "title", "script", "style", "base"})


def instrument_html(source: str, template_name: str, start: int = 1) -> tuple[str, dict[str, dict]]:
    """Return (new_source, sourcemap).

    sourcemap: {"zd<N>": {"file": template_name, "line": int, "col": int, "tag": str}}
    Positions are 1-based and refer to the ORIGINAL source.
    """
    out: list[str] = []
    smap: dict[str, dict] = {}
    counter = start
    pos = 0
    for m in _OPEN_TAG.finditer(source):
        tag = m.group(1).lower()
        if tag in _SKIP:
            continue
        insert_at = m.end()  # right after the tag name
        line = source.count("\n", 0, m.start()) + 1
        last_nl = source.rfind("\n", 0, m.start())
        col = m.start() - last_nl  # 1-based when last_nl == -1 (first line)
        zid = f"zd{counter}"
        counter += 1
        smap[zid] = {"file": template_name, "line": line, "col": col, "tag": tag}
        out.append(source[pos:insert_at])
        out.append(f' data-zd-id="{zid}"')
        pos = insert_at
    out.append(source[pos:])
    return "".join(out), smap
