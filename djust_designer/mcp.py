"""djust_designer MCP stdio server — bridges Claude Code to a running djust_designer app.

The overlay records the designer's most-recent selection on the Django server.
This MCP server exposes that selection (plus edit/undo tools) to Claude Code so
the assistant can act on what the designer just clicked.

Usage
-----
1. Install the extra: ``pip install 'djust_designer[mcp]'`` (installs the ``mcp`` SDK).
2. Register with Claude Code::

       claude mcp add djust_designer python -m djust_designer.mcp

3. In Claude Code, ask something like *"restyle the currently selected element
   to be rounder and darker"*. Claude calls ``get_current_selection`` then
   ``edit_class`` — the file is rewritten and hot-reload shows the change.

The server assumes the Django app is reachable at ``http://127.0.0.1:8737`` by
default. Override with ``DJUST_DESIGNER_URL`` or the ``--url`` flag.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "djust_designer.mcp requires the `mcp` package. Install it with:\n    pip install 'djust_designer[mcp]'"
    ) from exc


BASE_URL = os.environ.get("DJUST_DESIGNER_URL", "http://127.0.0.1:8737")
mcp = FastMCP("djust-designer")


def _post(path: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode(errors="replace")}
    except urllib.error.URLError as e:
        return {"error": "unreachable", "detail": str(e.reason)}


@mcp.tool()
def get_current_selection() -> dict:
    """Return the element the designer most-recently clicked in the overlay.

    Keys: ``zd_id``, ``file``, ``line``, ``col``, ``tag``, ``class``.
    Returns ``{"error": "no selection"}`` if the overlay hasn't been used yet.
    """
    return _post("/__djust_designer__/selection")


@mcp.tool()
def resolve_id(zd_id: str) -> dict:
    """Look up the source location and tag of any ``zd_id`` visible in the DOM.

    Every element the InstrumentedFilesystemLoader touched carries a
    ``data-zd-id="zdN"`` attribute — that ``zdN`` is what this tool resolves.
    """
    return _post("/__djust_designer__/resolve", {"zd_id": zd_id})


@mcp.tool()
def edit_class(zd_id: str, new_class: str) -> dict:
    """Rewrite the ``class`` attribute of the element identified by ``zd_id``.

    A backup is taken before writing, so ``undo_last`` can restore it. Class
    values containing ``"``, ``'``, ``<``, or ``>`` are rejected by the server.
    """
    return _post("/__djust_designer__/edit/class", {"zd_id": zd_id, "class": new_class})


@mcp.tool()
def undo_last() -> dict:
    """Restore the most recent snapshot taken by ``edit_class``."""
    return _post("/__djust_designer__/undo")


def main() -> None:
    global BASE_URL
    parser = argparse.ArgumentParser(description="djust_designer MCP stdio server")
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help="Base URL of the running djust_designer Django app (default: %(default)s)",
    )
    args = parser.parse_args()
    BASE_URL = args.url.rstrip("/")
    mcp.run()


if __name__ == "__main__":
    main()
