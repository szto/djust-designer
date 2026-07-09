"""HTTP JSON views: resolve zd_id -> source entry, apply class edit, undo.

DEBUG-only. Uses `resolve_within` to refuse writes outside the template
whitelist. Takes a backup before every write so `undo` can restore.
"""

from __future__ import annotations

import json
import os

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from djust_designer.edit.classedit import apply_class_change
from djust_designer.edit.paths import resolve_within
from djust_designer.edit.snapshot import Backups
from djust_designer.instrument.registry import registry

# Most-recent element the designer clicked in the overlay. The MCP server
# reads this so Claude Code can act on the current selection.
_current_selection: dict | None = None


def _template_roots() -> list[str]:
    roots: list[str] = []
    for tpl in getattr(settings, "TEMPLATES", []):
        for d in tpl.get("DIRS", []) or []:
            roots.append(str(d))
        if tpl.get("APP_DIRS"):
            from django.apps import apps

            for app in apps.get_app_configs():
                app_tpl = os.path.join(app.path, "templates")
                if os.path.isdir(app_tpl):
                    roots.append(app_tpl)
    return roots or [str(getattr(settings, "BASE_DIR", "."))]


def _guard(request):
    if not getattr(settings, "DEBUG", False):
        return JsonResponse({"error": "disabled"}, status=403)
    if request.META.get("REMOTE_ADDR") not in ("127.0.0.1", "::1"):
        return JsonResponse({"error": "loopback only"}, status=403)
    return None


@csrf_exempt
@require_POST
def resolve(request):
    if (g := _guard(request)) is not None:
        return g
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")
    entry = registry.get(data.get("zd_id", ""))
    if not entry:
        return JsonResponse({"error": "unknown id"}, status=404)
    return JsonResponse(entry)


@csrf_exempt
@require_POST
def edit_class(request):
    if (g := _guard(request)) is not None:
        return g
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")
    entry = registry.get(data.get("zd_id", ""))
    if not entry:
        return JsonResponse({"error": "unknown id"}, status=404)
    new_class = data.get("class", "")
    if any(c in new_class for c in "\"<>'"):
        return HttpResponseBadRequest("invalid class value")
    path = resolve_within(entry["file"], _template_roots())
    Backups(str(settings.BASE_DIR)).snapshot(path)
    with open(path, encoding="utf-8") as f:
        src = f.read()
    new = apply_class_change(src, entry["line"], new_class)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def undo(request):
    if (g := _guard(request)) is not None:
        return g
    restored = Backups(str(settings.BASE_DIR)).undo_last()
    return JsonResponse({"restored": restored})


@csrf_exempt
@require_POST
def select(request):
    """Overlay-side: record the element the designer just clicked."""
    if (g := _guard(request)) is not None:
        return g
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")
    zd_id = data.get("zd_id", "")
    entry = registry.get(zd_id)
    if not entry:
        return JsonResponse({"error": "unknown id"}, status=404)
    global _current_selection
    _current_selection = {
        "zd_id": zd_id,
        "class": data.get("class", ""),
        **entry,
    }
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def selection(request):
    """MCP-side: return the most recent overlay selection, if any."""
    if (g := _guard(request)) is not None:
        return g
    if not _current_selection:
        return JsonResponse({"error": "no selection"}, status=404)
    return JsonResponse(_current_selection)
