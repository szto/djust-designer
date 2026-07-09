"""HTTP JSON views: resolve zd_id -> source entry, apply class edit, undo.

DEBUG-only. Uses `resolve_within` to refuse writes outside the template
whitelist. Takes a backup before every write so `undo` can restore.
"""

from __future__ import annotations

import json

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from zdesign.edit.classedit import apply_class_change
from zdesign.edit.paths import resolve_within
from zdesign.edit.snapshot import Backups
from zdesign.instrument.registry import registry


def _template_roots() -> list[str]:
    roots: list[str] = []
    for tpl in getattr(settings, "TEMPLATES", []):
        for d in tpl.get("DIRS", []) or []:
            roots.append(str(d))
    return roots or [str(getattr(settings, "BASE_DIR", "."))]


def _guard():
    if not getattr(settings, "DEBUG", False):
        return JsonResponse({"error": "disabled"}, status=403)
    return None


@csrf_exempt
@require_POST
def resolve(request):
    if (g := _guard()) is not None:
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
    if (g := _guard()) is not None:
        return g
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")
    entry = registry.get(data.get("zd_id", ""))
    if not entry:
        return JsonResponse({"error": "unknown id"}, status=404)
    new_class = data.get("class", "")
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
    if (g := _guard()) is not None:
        return g
    restored = Backups(str(settings.BASE_DIR)).undo_last()
    return JsonResponse({"restored": restored})
