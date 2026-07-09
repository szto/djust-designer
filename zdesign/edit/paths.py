"""Path whitelist guard — refuse to touch files outside the allowed roots.

Resolves symlinks on both the target and the roots so that a symlink cannot
be used to escape the whitelist.
"""

from __future__ import annotations

import os


def resolve_within(path: str, roots: list[str]) -> str:
    rp = os.path.realpath(path)
    for root in roots:
        rr = os.path.realpath(root)
        if rp == rr or rp.startswith(rr + os.sep):
            return rp
    raise PermissionError(f"path escapes allowed roots: {path}")
