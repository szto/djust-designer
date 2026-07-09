# zdesign P1 (MVP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the MVP of `zdesign` — a pip-installable Django app that lets a designer hover/select any element in a running djust page, see its source template file+line, and change its Tailwind classes with automatic write-back to the source and git-safe undo. No Claude yet (that is P2).

**Architecture:** Instrumenter wraps the Django template loader to inject `data-zd-id` into every opening tag and build an in-memory `{id → file:line:col:tag}` sourcemap (dev-only, `DEBUG=True`). A middleware auto-injects the overlay JS/CSS into every HTML response. A small set of JSON views resolves a `zd_id` to source location and applies class edits with a backup-based undo. The client overlay uses vanilla JS + Shadow DOM for isolation.

**Tech Stack:** Python 3.12+, Django 5+, pytest + pytest-django, vanilla JS (no build step for P1). Runs on plain Django and on djust (djust reuse deferred to P2 — P1 is framework-general and validated on plain Django).

---

## File Structure

```
zdesign/
  __init__.py
  apps.py                            # AppConfig
  middleware.py                      # inject overlay assets into HTML responses (DEBUG only)
  urls.py                            # re-export bridge.urls
  instrument/
    __init__.py
    scanner.py                       # pure: instrument_html(src,name,start)->(new_src,smap)
    registry.py                      # global {zd_id -> entry} + monotonic counter
    loader.py                        # Django template loader mixin using scanner+registry
  edit/
    __init__.py
    classedit.py                     # pure: apply_class_change(src,line,new_class)->new_src
    paths.py                         # pure: resolve_within(path,roots) traversal guard
    snapshot.py                      # Backups(root): snapshot(file), undo_last()
  bridge/
    __init__.py
    views.py                         # resolve / edit_class / undo (JSON)
    urls.py                          # URL patterns under /__zdesign__/
  static/zdesign/
    overlay.css                      # minimal overlay styles
    overlay.js                       # hover/select/badge/panel/apply (vanilla + Shadow DOM)
  templatetags/
    __init__.py
    zdesign_tags.py                  # {% zdesign_scripts %} (optional manual injection)
tests/
  __init__.py
  settings.py                        # minimal Django settings for tests
  conftest.py
  test_scanner.py
  test_classedit.py
  test_paths.py
  test_snapshot.py
  test_registry.py
  test_loader.py
  test_middleware.py
  test_views.py
demo/
  manage.py
  demo_project/settings.py
  demo_project/urls.py
  demo_project/wsgi.py
  templates/demo/home.html
pyproject.toml
README.md
```

**Boundaries.** The `instrument/` and `edit/` packages are pure Python (no Django imports in `scanner.py`, `classedit.py`, `paths.py`, `snapshot.py`) and are the majority of the testable surface. Django integration is confined to `loader.py`, `middleware.py`, `bridge/views.py`, `apps.py`. Client code is confined to `static/zdesign/`.

---

## Task 0: Scaffold — pyproject, package skeleton, test harness

**Files:**
- Create: `pyproject.toml`
- Create: `zdesign/__init__.py`
- Create: `zdesign/apps.py`
- Create: `zdesign/instrument/__init__.py`
- Create: `zdesign/edit/__init__.py`
- Create: `zdesign/bridge/__init__.py`
- Create: `zdesign/templatetags/__init__.py`
- Create: `zdesign/static/zdesign/.keep`
- Create: `tests/__init__.py`
- Create: `tests/settings.py`
- Create: `tests/conftest.py`
- Create: `pytest.ini`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "zdesign"
version = "0.0.1"
description = "Visual design collaboration layer for djust (Django) — point at the page, edit the source."
requires-python = ">=3.12"
dependencies = ["Django>=5.0"]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-django>=4.9"]

[tool.setuptools.packages.find]
include = ["zdesign*"]

[tool.setuptools.package-data]
zdesign = ["static/zdesign/*", "templates/**/*"]
```

- [ ] **Step 2: Write `zdesign/__init__.py`**

```python
__version__ = "0.0.1"
```

- [ ] **Step 3: Write `zdesign/apps.py`**

```python
from django.apps import AppConfig


class ZdesignConfig(AppConfig):
    name = "zdesign"
    verbose_name = "zdesign"
    default_auto_field = "django.db.models.BigAutoField"
```

- [ ] **Step 4: Write empty `__init__.py` for subpackages**

Create empty files at:
- `zdesign/instrument/__init__.py`
- `zdesign/edit/__init__.py`
- `zdesign/bridge/__init__.py`
- `zdesign/templatetags/__init__.py`
- `zdesign/static/zdesign/.keep`
- `tests/__init__.py`

- [ ] **Step 5: Write `tests/settings.py`**

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "test-only-not-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "zdesign",
]

MIDDLEWARE = [
    "zdesign.middleware.ZdesignMiddleware",
]

ROOT_URLCONF = "zdesign.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "tests" / "fixtures" / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": [
                (
                    "zdesign.instrument.loader.InstrumentedFilesystemLoader",
                    [str(BASE_DIR / "tests" / "fixtures" / "templates")],
                ),
            ],
        },
    },
]

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
```

- [ ] **Step 6: Write `tests/conftest.py`**

```python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
```

- [ ] **Step 7: Write `pytest.ini`**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = tests.settings
python_files = test_*.py
```

- [ ] **Step 8: Verify scaffold works**

Run: `pip install -e '.[dev]' && python -c "import django; django.setup(); import zdesign; print(zdesign.__version__)"`
Expected: `0.0.1`

Run: `pytest -q`
Expected: no tests collected, exit 0 (or exit 5 "no tests ran" — treat both as pass).

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml pytest.ini zdesign/ tests/
git commit -m "chore: scaffold zdesign package + pytest-django harness"
```

---

## Task 1: `instrument.scanner` — inject `data-zd-id` and build sourcemap

**Files:**
- Create: `tests/test_scanner.py`
- Create: `zdesign/instrument/scanner.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_scanner.py`:
```python
from zdesign.instrument.scanner import instrument_html


def test_injects_id_and_records_position():
    src = '<div class="a">\n<button>Hi</button>\n</div>'
    out, smap = instrument_html(src, "t.html", start=1)
    assert out.startswith('<div data-zd-id="zd1" class="a">')
    assert '<button data-zd-id="zd2">Hi</button>' in out
    assert smap["zd1"] == {"file": "t.html", "line": 1, "col": 1, "tag": "div"}
    assert smap["zd2"]["line"] == 2
    assert smap["zd2"]["tag"] == "button"
    assert "zd3" not in smap  # closing </div> not counted


def test_skips_head_and_script_style():
    src = "<html><head><meta><title>t</title></head><body><p>x</p><script>a=1</script><style>b</style></body></html>"
    out, smap = instrument_html(src, "t.html", start=1)
    tags = [v["tag"] for v in smap.values()]
    assert "html" not in tags
    assert "head" not in tags
    assert "meta" not in tags
    assert "title" not in tags
    assert "script" not in tags
    assert "style" not in tags
    assert "body" in tags
    assert "p" in tags


def test_ignores_closing_and_doctype_and_django_tags():
    src = "<!DOCTYPE html>\n{% if x %}<p>{{ v }}</p>{% endif %}"
    out, smap = instrument_html(src, "t.html", start=1)
    assert list(smap.keys()) == ["zd1"]
    assert smap["zd1"]["tag"] == "p"
    assert '<p data-zd-id="zd1">' in out


def test_start_offset_is_honored():
    src = "<p>x</p>"
    _, smap = instrument_html(src, "t.html", start=42)
    assert list(smap.keys()) == ["zd42"]


def test_col_is_one_based_from_line_start():
    src = "  <div>x</div>"
    _, smap = instrument_html(src, "t.html", start=1)
    assert smap["zd1"]["col"] == 3
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_scanner.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'zdesign.instrument.scanner'`.

- [ ] **Step 3: Implement `zdesign/instrument/scanner.py`**

```python
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
_SKIP = frozenset(
    {"html", "head", "meta", "link", "title", "script", "style", "base"}
)


def instrument_html(
    source: str, template_name: str, start: int = 1
) -> tuple[str, dict[str, dict]]:
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
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/test_scanner.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add zdesign/instrument/scanner.py tests/test_scanner.py
git commit -m "feat(instrument): scanner injects data-zd-id and records source positions"
```

---

## Task 2: `edit.classedit` — precise class rewrite on a source line

**Files:**
- Create: `tests/test_classedit.py`
- Create: `zdesign/edit/classedit.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_classedit.py`:
```python
from zdesign.edit.classedit import apply_class_change


def test_replaces_existing_class_double_quoted():
    src = '<div class="p-2 text-sm">x</div>\n'
    assert (
        apply_class_change(src, 1, "p-4 text-sm")
        == '<div class="p-4 text-sm">x</div>\n'
    )


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
    import pytest as _pytest
    with _pytest.raises(IndexError):
        apply_class_change("<div>x</div>\n", 5, "p-4")
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_classedit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'zdesign.edit.classedit'`.

- [ ] **Step 3: Implement `zdesign/edit/classedit.py`**

```python
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
        new_line = (
            target[:insert_at] + f' class="{new_class}"' + target[insert_at:]
        )
    lines[idx] = new_line
    return "".join(lines)
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/test_classedit.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add zdesign/edit/classedit.py tests/test_classedit.py
git commit -m "feat(edit): apply_class_change rewrites or inserts class on a line"
```

---

## Task 3: `edit.paths` — traversal guard

**Files:**
- Create: `tests/test_paths.py`
- Create: `zdesign/edit/paths.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_paths.py`:
```python
import os
import pytest

from zdesign.edit.paths import resolve_within


def test_returns_realpath_when_within_root(tmp_path):
    root = tmp_path / "templates"
    root.mkdir()
    f = root / "home.html"
    f.write_text("x")
    got = resolve_within(str(f), [str(root)])
    assert got == os.path.realpath(str(f))


def test_raises_on_traversal(tmp_path):
    root = tmp_path / "templates"
    root.mkdir()
    outside = tmp_path / "secrets.txt"
    outside.write_text("x")
    with pytest.raises(PermissionError):
        resolve_within(str(outside), [str(root)])


def test_multiple_roots_any_match(tmp_path):
    r1 = tmp_path / "a"; r1.mkdir()
    r2 = tmp_path / "b"; r2.mkdir()
    f = r2 / "t.html"; f.write_text("x")
    got = resolve_within(str(f), [str(r1), str(r2)])
    assert got == os.path.realpath(str(f))
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_paths.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `zdesign/edit/paths.py`**

```python
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
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/test_paths.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add zdesign/edit/paths.py tests/test_paths.py
git commit -m "feat(edit): resolve_within refuses paths that escape allowed roots"
```

---

## Task 4: `edit.snapshot` — backup-based snapshot/undo

**Files:**
- Create: `tests/test_snapshot.py`
- Create: `zdesign/edit/snapshot.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_snapshot.py`:
```python
from zdesign.edit.snapshot import Backups


def test_snapshot_then_undo_restores_original(tmp_path):
    root = tmp_path
    f = root / "home.html"
    f.write_text("original\n")
    b = Backups(str(root))
    b.snapshot(str(f))
    f.write_text("modified\n")

    restored = b.undo_last()
    assert restored == str(f)
    assert f.read_text() == "original\n"


def test_undo_is_lifo_across_multiple_edits(tmp_path):
    f = tmp_path / "home.html"
    f.write_text("v0")
    b = Backups(str(tmp_path))
    b.snapshot(str(f)); f.write_text("v1")
    b.snapshot(str(f)); f.write_text("v2")

    b.undo_last()
    assert f.read_text() == "v1"
    b.undo_last()
    assert f.read_text() == "v0"


def test_undo_last_returns_none_when_empty(tmp_path):
    b = Backups(str(tmp_path))
    assert b.undo_last() is None
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_snapshot.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `zdesign/edit/snapshot.py`**

```python
"""Backup-based snapshot/undo — works with or without git.

Snapshots each file into `<root>/.zdesign/backups/` and appends a JSONL log.
`undo_last` restores the newest entry and trims the log.
"""
from __future__ import annotations

import json
import os
import shutil
import time


class Backups:
    def __init__(self, root: str) -> None:
        self.dir = os.path.join(root, ".zdesign", "backups")
        os.makedirs(self.dir, exist_ok=True)
        self.log = os.path.join(self.dir, "log.jsonl")

    def snapshot(self, file_path: str) -> str:
        ts = f"{int(time.time() * 1000)}"
        dst = os.path.join(self.dir, f"{ts}__{os.path.basename(file_path)}")
        shutil.copy2(file_path, dst)
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ts, "file": file_path, "backup": dst}) + "\n")
        return dst

    def undo_last(self) -> str | None:
        if not os.path.exists(self.log):
            return None
        with open(self.log, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
        if not entries:
            return None
        last = entries[-1]
        shutil.copy2(last["backup"], last["file"])
        with open(self.log, "w", encoding="utf-8") as f:
            for e in entries[:-1]:
                f.write(json.dumps(e) + "\n")
        return last["file"]
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/test_snapshot.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add zdesign/edit/snapshot.py tests/test_snapshot.py
git commit -m "feat(edit): Backups snapshot/undo (LIFO, backup-based)"
```

---

## Task 5: `instrument.registry` — global sourcemap store + monotonic counter

**Files:**
- Create: `tests/test_registry.py`
- Create: `zdesign/instrument/registry.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_registry.py`:
```python
from zdesign.instrument.registry import SourceMapRegistry


def test_counter_allocates_disjoint_ranges():
    r = SourceMapRegistry()
    assert r.next_start(3) == 1
    assert r.next_start(2) == 4
    assert r.next_start(1) == 6


def test_update_and_get():
    r = SourceMapRegistry()
    r.update({"zd1": {"file": "t.html", "line": 1, "col": 1, "tag": "div"}})
    assert r.get("zd1")["tag"] == "div"
    assert r.get("missing") is None


def test_reset_clears_everything():
    r = SourceMapRegistry()
    r.next_start(5)
    r.update({"zd1": {"file": "t.html", "line": 1, "col": 1, "tag": "div"}})
    r.reset()
    assert r.get("zd1") is None
    assert r.next_start(1) == 1
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `zdesign/instrument/registry.py`**

```python
"""In-memory sourcemap store shared across template loads.

Thread-safe. The counter reserves disjoint ranges per load so the
scanner in one thread does not collide with another. Reserved ranges
may be sparsely used (not every reserved id is emitted); that is fine.
"""
from __future__ import annotations

import threading


class SourceMapRegistry:
    def __init__(self) -> None:
        self._map: dict[str, dict] = {}
        self._counter = 1
        self._lock = threading.Lock()

    def next_start(self, n: int) -> int:
        with self._lock:
            s = self._counter
            self._counter += max(n, 0)
            return s

    def update(self, smap: dict[str, dict]) -> None:
        with self._lock:
            self._map.update(smap)

    def get(self, zid: str) -> dict | None:
        return self._map.get(zid)

    def reset(self) -> None:
        with self._lock:
            self._map.clear()
            self._counter = 1


registry = SourceMapRegistry()
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/test_registry.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add zdesign/instrument/registry.py tests/test_registry.py
git commit -m "feat(instrument): SourceMapRegistry with disjoint id ranges"
```

---

## Task 6: `instrument.loader` — Django template loader that instruments on load

**Files:**
- Create: `tests/fixtures/templates/home.html`
- Create: `tests/test_loader.py`
- Create: `zdesign/instrument/loader.py`

- [ ] **Step 1: Write the fixture template**

`tests/fixtures/templates/home.html`:
```html
<div class="wrap">
  <button class="btn">Hello</button>
</div>
```

- [ ] **Step 2: Write the failing test**

`tests/test_loader.py`:
```python
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
```

- [ ] **Step 3: Run test — verify it fails**

Run: `pytest tests/test_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'zdesign.instrument.loader'`.

- [ ] **Step 4: Implement `zdesign/instrument/loader.py`**

```python
"""Django template loader that instruments source on load (DEBUG only).

Wraps the standard filesystem and app_directories loaders. On each load
we scan the source, inject `data-zd-id` attributes, and merge the
partial sourcemap into the global registry.
"""
from __future__ import annotations

from django.conf import settings
from django.template.loaders.app_directories import Loader as AppDirsLoader
from django.template.loaders.filesystem import Loader as FSLoader

from .registry import registry
from .scanner import instrument_html


class _InstrumentMixin:
    def get_contents(self, origin):
        source = super().get_contents(origin)  # type: ignore[misc]
        if not getattr(settings, "DEBUG", False):
            return source
        # Over-allocate — one id per '<' is a safe upper bound.
        start = registry.next_start(source.count("<"))
        new_source, smap = instrument_html(source, origin.name, start=start)
        registry.update(smap)
        return new_source


class InstrumentedFilesystemLoader(_InstrumentMixin, FSLoader):
    pass


class InstrumentedAppDirsLoader(_InstrumentMixin, AppDirsLoader):
    pass
```

- [ ] **Step 5: Run test — verify pass**

Run: `pytest tests/test_loader.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add zdesign/instrument/loader.py tests/fixtures/templates/home.html tests/test_loader.py
git commit -m "feat(instrument): Django loader that injects data-zd-id on load (DEBUG only)"
```

---

## Task 7: `middleware` — auto-inject overlay assets into HTML responses

**Files:**
- Create: `tests/test_middleware.py`
- Create: `zdesign/middleware.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_middleware.py`:
```python
from unittest.mock import Mock

from django.http import HttpResponse, StreamingHttpResponse
from django.test import override_settings

from zdesign.middleware import ZdesignMiddleware


def _mw():
    return ZdesignMiddleware(get_response=lambda r: r)


def test_injects_assets_into_html_response_when_debug():
    resp = HttpResponse("<html><body>hi</body></html>", content_type="text/html")
    out = _mw().process_response(Mock(), resp)
    body = out.content.decode()
    assert "zdesign/overlay.js" in body
    assert "zdesign/overlay.css" in body
    assert body.endswith("</body></html>")


@override_settings(DEBUG=False)
def test_no_inject_when_debug_false():
    resp = HttpResponse("<html><body>hi</body></html>", content_type="text/html")
    out = _mw().process_response(Mock(), resp)
    assert "zdesign/overlay.js" not in out.content.decode()


def test_no_inject_for_non_html():
    resp = HttpResponse('{"ok": true}', content_type="application/json")
    out = _mw().process_response(Mock(), resp)
    assert "zdesign/overlay.js" not in out.content.decode()


def test_no_inject_for_streaming_response():
    resp = StreamingHttpResponse(iter([b"<html><body>x</body></html>"]),
                                 content_type="text/html")
    out = _mw().process_response(Mock(), resp)
    # StreamingHttpResponse has no `.content`; middleware should pass through unchanged
    assert getattr(out, "streaming", False) is True


def test_idempotent_when_already_injected():
    src = '<html><body>x<script src="/static/zdesign/overlay.js"></script></body></html>'
    resp = HttpResponse(src, content_type="text/html")
    out = _mw().process_response(Mock(), resp)
    assert out.content.decode().count("zdesign/overlay.js") == 1
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_middleware.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'zdesign.middleware'`.

- [ ] **Step 3: Implement `zdesign/middleware.py`**

```python
"""Auto-inject the overlay CSS/JS before </body> on HTML responses.

DEBUG-only. Skips streaming responses and non-HTML content types. Idempotent.
"""
from __future__ import annotations

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

_INJECT = (
    '<link rel="stylesheet" href="/static/zdesign/overlay.css">'
    '<script src="/static/zdesign/overlay.js" defer></script>'
)


class ZdesignMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if not getattr(settings, "DEBUG", False):
            return response
        if getattr(response, "streaming", False):
            return response
        ct = response.get("Content-Type", "") or ""
        if "text/html" not in ct:
            return response
        content = response.content.decode(response.charset)
        if "zdesign/overlay.js" in content:
            return response
        if "</body>" not in content:
            return response
        content = content.replace("</body>", _INJECT + "</body>", 1)
        response.content = content.encode(response.charset)
        if response.has_header("Content-Length"):
            response["Content-Length"] = str(len(response.content))
        return response
```

- [ ] **Step 4: Run tests — verify pass**

Run: `pytest tests/test_middleware.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add zdesign/middleware.py tests/test_middleware.py
git commit -m "feat(middleware): auto-inject overlay assets on HTML responses (DEBUG only)"
```

---

## Task 8: `bridge` — JSON views + URL wiring

**Files:**
- Create: `tests/test_views.py`
- Create: `zdesign/bridge/views.py`
- Create: `zdesign/bridge/urls.py`
- Create: `zdesign/urls.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_views.py`:
```python
import json

import pytest
from django.template.loader import get_template
from django.test import Client

from zdesign.instrument.registry import registry


@pytest.mark.django_db
def test_resolve_returns_entry_for_known_id():
    registry.reset()
    get_template("home.html").render({})  # populate registry

    c = Client()
    r = c.post(
        "/__zdesign__/resolve",
        data=json.dumps({"zd_id": "zd1"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    body = r.json()
    assert body["tag"] == "div"
    assert body["line"] == 1


@pytest.mark.django_db
def test_resolve_404_for_unknown_id():
    registry.reset()
    c = Client()
    r = c.post(
        "/__zdesign__/resolve",
        data=json.dumps({"zd_id": "nope"}),
        content_type="application/json",
    )
    assert r.status_code == 404


@pytest.mark.django_db
def test_edit_class_rewrites_source_and_supports_undo(tmp_path, settings, monkeypatch):
    # Point BASE_DIR at a tmp so backups land in tmp
    settings.BASE_DIR = tmp_path

    # Copy fixture template into an editable tmp location and register it manually
    src_file = tmp_path / "home.html"
    src_file.write_text('<div class="p-2">x</div>\n')

    registry.reset()
    registry.update({
        "zd1": {"file": str(src_file), "line": 1, "col": 1, "tag": "div"},
    })

    # Allow writes into tmp_path by overriding TEMPLATES DIRS via settings
    settings.TEMPLATES = [{
        **settings.TEMPLATES[0],
        "DIRS": [str(tmp_path)],
    }]

    c = Client()
    r = c.post(
        "/__zdesign__/edit/class",
        data=json.dumps({"zd_id": "zd1", "class": "p-4"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    assert src_file.read_text() == '<div class="p-4">x</div>\n'

    r = c.post("/__zdesign__/undo", content_type="application/json")
    assert r.status_code == 200
    assert src_file.read_text() == '<div class="p-2">x</div>\n'
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `pytest tests/test_views.py -v`
Expected: FAIL with `ModuleNotFoundError` or URL resolution errors.

- [ ] **Step 3: Implement `zdesign/bridge/views.py`**

```python
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

from ..edit.classedit import apply_class_change
from ..edit.paths import resolve_within
from ..edit.snapshot import Backups
from ..instrument.registry import registry


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
```

- [ ] **Step 4: Implement `zdesign/bridge/urls.py`**

```python
from django.urls import path

from . import views

urlpatterns = [
    path("__zdesign__/resolve", views.resolve),
    path("__zdesign__/edit/class", views.edit_class),
    path("__zdesign__/undo", views.undo),
]
```

- [ ] **Step 5: Implement `zdesign/urls.py`**

```python
from .bridge.urls import urlpatterns  # noqa: F401
```

- [ ] **Step 6: Run tests — verify pass**

Run: `pytest tests/test_views.py -v`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add zdesign/bridge/ zdesign/urls.py tests/test_views.py
git commit -m "feat(bridge): resolve / edit_class / undo JSON views"
```

---

## Task 9: Overlay client — CSS + vanilla JS with Shadow DOM isolation

**Files:**
- Create: `zdesign/static/zdesign/overlay.css`
- Create: `zdesign/static/zdesign/overlay.js`
- Create: `zdesign/templatetags/zdesign_tags.py`

- [ ] **Step 1: Write `zdesign/static/zdesign/overlay.css`**

Minimal shell — most styling is inside the Shadow DOM built by `overlay.js`. This file only exists so the middleware injects a `<link>` for cache-busting/consistency; it is intentionally empty.

```css
/* zdesign overlay: all interactive UI lives in Shadow DOM in overlay.js.
   This file is a no-op placeholder for the injected <link>. */
```

- [ ] **Step 2: Write `zdesign/static/zdesign/overlay.js`**

```javascript
/* zdesign overlay — vanilla JS + Shadow DOM. Hover to highlight any
 * element carrying data-zd-id; click to open the edit panel; edit its
 * class attribute and POST the change back to the source. */
(() => {
  if (window.__zdesign_loaded) return;
  window.__zdesign_loaded = true;

  const host = document.createElement("div");
  host.id = "zdesign-root";
  host.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:2147483647";
  document.documentElement.appendChild(host);
  const root = host.attachShadow({ mode: "open" });

  root.innerHTML = `
    <style>
      :host { all: initial; font: 13px/1.4 system-ui, sans-serif; color: #0f172a; }
      .hi { position:absolute; outline:2px solid #6366f1; background:rgba(99,102,241,.08); pointer-events:none; transition:all .05s ease-out; }
      .badge { position:absolute; background:#4338ca; color:#fff; padding:2px 6px; border-radius:4px; font-size:11px; pointer-events:none; }
      .panel { position:fixed; right:16px; bottom:16px; width:340px; background:#fff; border:1px solid #cbd5e1; border-radius:10px; box-shadow:0 10px 30px rgba(15,23,42,.2); pointer-events:auto; overflow:hidden; }
      .panel header { padding:10px 12px; background:#0f172a; color:#fff; display:flex; justify-content:space-between; align-items:center; }
      .panel header .close { cursor:pointer; opacity:.7; }
      .panel .body { padding:12px; }
      .panel label { display:block; font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:#64748b; margin-bottom:4px; }
      .panel input { width:100%; box-sizing:border-box; padding:8px; border:1px solid #cbd5e1; border-radius:6px; font-family:ui-monospace,monospace; font-size:12px; }
      .panel .src { font-family:ui-monospace,monospace; font-size:11px; color:#334155; margin-top:8px; }
      .panel .actions { display:flex; gap:8px; margin-top:10px; }
      .panel button { flex:1; padding:8px; border:0; border-radius:6px; background:#6366f1; color:#fff; cursor:pointer; }
      .panel button.secondary { background:#e2e8f0; color:#0f172a; }
    </style>
    <div class="hi" hidden></div>
    <div class="badge" hidden></div>
    <div class="panel" hidden>
      <header>
        <span>zdesign</span>
        <span class="close">×</span>
      </header>
      <div class="body">
        <label>class</label>
        <input type="text" class="cls" />
        <div class="src"></div>
        <div class="actions">
          <button class="apply">Apply</button>
          <button class="undo secondary">Undo last</button>
        </div>
      </div>
    </div>
  `;

  const hi = root.querySelector(".hi");
  const badge = root.querySelector(".badge");
  const panel = root.querySelector(".panel");
  const clsInput = root.querySelector(".cls");
  const srcEl = root.querySelector(".src");
  const applyBtn = root.querySelector(".apply");
  const undoBtn = root.querySelector(".undo");
  const closeBtn = root.querySelector(".close");

  let selected = null;
  let hoverPinned = false;

  const findZ = (el) => {
    while (el && el.nodeType === 1) {
      if (el.dataset && el.dataset.zdId) return el;
      el = el.parentElement;
    }
    return null;
  };

  const showHighlight = (el) => {
    const r = el.getBoundingClientRect();
    hi.hidden = false;
    hi.style.left = r.left + "px";
    hi.style.top = r.top + "px";
    hi.style.width = r.width + "px";
    hi.style.height = r.height + "px";
    badge.hidden = false;
    badge.textContent = `${el.tagName.toLowerCase()} · ${el.dataset.zdId}`;
    badge.style.left = r.left + "px";
    badge.style.top = Math.max(0, r.top - 22) + "px";
  };

  const hideHighlight = () => { hi.hidden = true; badge.hidden = true; };

  document.addEventListener("mousemove", (e) => {
    if (hoverPinned) return;
    const el = findZ(e.target);
    if (el) showHighlight(el); else hideHighlight();
  }, true);

  document.addEventListener("click", async (e) => {
    if (root.contains(e.target) || e.composedPath().includes(host)) return;
    const el = findZ(e.target);
    if (!el) return;
    e.preventDefault(); e.stopPropagation();
    selected = el;
    hoverPinned = true;
    showHighlight(el);

    const zdId = el.dataset.zdId;
    const res = await fetch("/__zdesign__/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zd_id: zdId }),
    });
    const entry = res.ok ? await res.json() : { error: true };
    clsInput.value = el.getAttribute("class") || "";
    srcEl.textContent = entry.error ? "(source unknown)" : `${entry.file}:${entry.line}`;
    panel.hidden = false;
  }, true);

  applyBtn.addEventListener("click", async () => {
    if (!selected) return;
    const zdId = selected.dataset.zdId;
    const cls = clsInput.value;
    const res = await fetch("/__zdesign__/edit/class", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zd_id: zdId, class: cls }),
    });
    if (res.ok) {
      selected.setAttribute("class", cls);  // optimistic; hot reload will re-render
    }
  });

  undoBtn.addEventListener("click", async () => {
    await fetch("/__zdesign__/undo", { method: "POST" });
  });

  closeBtn.addEventListener("click", () => {
    panel.hidden = true;
    hoverPinned = false;
    hideHighlight();
    selected = null;
  });
})();
```

- [ ] **Step 3: Write `zdesign/templatetags/zdesign_tags.py`**

```python
"""Optional manual injection: `{% load zdesign_tags %}{% zdesign_scripts %}`.

The middleware already auto-injects; this tag exists for users who want
explicit placement (e.g. above a strict CSP-guarded </body>).
"""
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def zdesign_scripts() -> str:
    if not getattr(settings, "DEBUG", False):
        return ""
    return mark_safe(
        '<link rel="stylesheet" href="/static/zdesign/overlay.css">'
        '<script src="/static/zdesign/overlay.js" defer></script>'
    )
```

- [ ] **Step 4: Manual sanity check that assets load**

Run: `python -m http.server --directory zdesign/static 0`
Open the printed URL and confirm `zdesign/overlay.js` and `zdesign/overlay.css` are served with no syntax errors in the browser console.

- [ ] **Step 5: Commit**

```bash
git add zdesign/static/ zdesign/templatetags/zdesign_tags.py
git commit -m "feat(overlay): vanilla JS + Shadow DOM overlay, hover/select/apply/undo"
```

---

## Task 10: Demo project + E2E smoke test + README quickstart

**Files:**
- Create: `demo/manage.py`
- Create: `demo/demo_project/__init__.py`
- Create: `demo/demo_project/settings.py`
- Create: `demo/demo_project/urls.py`
- Create: `demo/demo_project/wsgi.py`
- Create: `demo/templates/demo/home.html`
- Create: `README.md`

- [ ] **Step 1: Write the demo `manage.py`**

`demo/manage.py`:
```python
#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo_project.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
```

- [ ] **Step 2: Write the demo settings**

`demo/demo_project/__init__.py`: empty file.

`demo/demo_project/settings.py`:
```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "demo-only"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "zdesign",
]

MIDDLEWARE = ["zdesign.middleware.ZdesignMiddleware"]

ROOT_URLCONF = "demo_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": [
                (
                    "zdesign.instrument.loader.InstrumentedFilesystemLoader",
                    [str(BASE_DIR / "templates")],
                ),
            ],
        },
    },
]

STATIC_URL = "/static/"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

`demo/demo_project/urls.py`:
```python
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import render
from django.urls import include, path


def home(request):
    return render(request, "demo/home.html")


urlpatterns = [
    path("", home),
    path("", include("zdesign.urls")),
]
urlpatterns += staticfiles_urlpatterns()
```

`demo/demo_project/wsgi.py`:
```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo_project.settings")
application = get_wsgi_application()
```

- [ ] **Step 3: Write the demo template**

`demo/templates/demo/home.html`:
```html
<!DOCTYPE html>
<html>
  <head><title>zdesign demo</title></head>
  <body>
    <div class="p-4 max-w-lg mx-auto">
      <h1 class="text-2xl font-bold">Hello, wife!</h1>
      <p class="text-slate-600">Hover me, click me, edit my class.</p>
      <button class="px-4 py-2 bg-indigo-500 text-white rounded">Try me</button>
    </div>
  </body>
</html>
```

- [ ] **Step 4: Boot the demo and smoke-check by browser**

Run: `cd demo && python manage.py runserver 8000`
Open `http://localhost:8000` in a browser.

Verify by hand (or with the `browse` skill):
- Hovering over the heading, paragraph, and button shows the outline + `data-zd-id` badge.
- Clicking the button opens the panel; the source line reads `demo/templates/demo/home.html:6` (or similar).
- Changing the `class` field to `px-6 py-3 bg-emerald-500 text-white rounded` and clicking Apply rewrites the template on disk (verify via `git diff demo/templates/demo/home.html`).
- Clicking **Undo last** restores the original class.

- [ ] **Step 5: Write `README.md`**

`README.md`:
````markdown
# zdesign

Visual design collaboration layer for [djust](https://github.com/szto/djust) (Django) apps.
Point at any element on your running page → see its source template + line → edit its
Tailwind classes with automatic write-back → undo with one click. No terminal, no code
editor. P2 will add an in-app Claude chat panel.

**Runs on `DEBUG=True` only.** No traces in production.

## Install

```bash
pip install -e path/to/zdesign
```

## Wire it up

```python
# settings.py
INSTALLED_APPS = [..., "zdesign"]
MIDDLEWARE = ["zdesign.middleware.ZdesignMiddleware", ...]

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": False,
    "OPTIONS": {"loaders": [(
        "zdesign.instrument.loader.InstrumentedFilesystemLoader",
        [str(BASE_DIR / "templates")],
    )]},
}]
```

```python
# urls.py
urlpatterns += [path("", include("zdesign.urls"))]
```

## Try the demo

```bash
cd demo && python manage.py runserver 8000
# open http://localhost:8000
```

Hover → highlight. Click → panel. Edit class → Apply → source rewritten → hot-reloaded.
Undo → previous state.

## Design docs

- Design: `docs/superpowers/specs/2026-07-09-zdesign-design.md`
- Plan: `docs/superpowers/plans/2026-07-09-zdesign-p1-mvp.md`
````

- [ ] **Step 6: Commit**

```bash
git add demo/ README.md
git commit -m "feat(demo): plain-Django demo project + README quickstart"
```

---

## Post-P1 (out of scope for this plan)

- **P2:** Anthropic API agent loop as a fourth view (`/__zdesign__/chat`), streaming responses to the overlay side-panel; agent tools = existing `edit_class` + `apply_diff` (line-range write). Reuses `describe_ui`/`get_state_snapshot`/`get_handler_schema` from djust.
- **P3:** Fingerprint fallback (Task-6 loader emits a fingerprint index for un-instrumented elements), component tree navigator in the panel, multi-select edits.
