# zdesign

Visual design collaboration layer for [djust](https://github.com/szto/djust) / Django apps.
Point at any element on your running page → see its source template + line → edit its
Tailwind classes with automatic write-back → undo with one click. No terminal, no code
editor. Ships with a Claude Code MCP bridge so an AI assistant can act on whatever the
designer just clicked.

**Runs on `DEBUG=True` only.** No traces in production.

## Install

Plain Django project:

```bash
pip install zdesign
```

With Claude Code MCP bridge:

```bash
pip install 'zdesign[mcp]'
```

Targeting a [djust](https://github.com/szto/djust) app (pulls djust too):

```bash
pip install 'zdesign[djust,mcp]'
```

Local development:

```bash
pip install -e '.[dev,mcp]'
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

### Using `APP_DIRS = True`

If your project relies on per-app `templates/` directories, use `InstrumentedAppDirsLoader` instead (or in addition to) the filesystem loader:

```python
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": False,
    "OPTIONS": {"loaders": [
        ("zdesign.instrument.loader.InstrumentedFilesystemLoader",
         [str(BASE_DIR / "templates")]),
        "zdesign.instrument.loader.InstrumentedAppDirsLoader",
    ]},
}]
```

Every template — whether from `DIRS` or an installed app — is edit-eligible.

## Try the demo

````
cd demo && python manage.py runserver 8000
# open http://localhost:8000
````

Hover → highlight. Click → panel. Edit class → Apply → source rewritten → hot-reloaded.
Undo → previous state.

### Panel niceties

- **Tailwind autocomplete** — the class input suggests ~1,600 common Tailwind
  utilities as you type. Arrow keys navigate, Enter/Tab inserts.
- **Tag label** — the panel header shows the selected element's tag name
  (e.g. `<button>`) so you always know what you're editing.
- **Toast** — Apply/Undo produce a small feedback toast so failures are visible.

## Claude Code (MCP)

The overlay mirrors the designer's current selection to the server so an MCP
client can act on it. Install and register:

```bash
pip install -e '.[mcp]'
claude mcp add zdesign python -m zdesign.mcp
```

Then, with the demo (or any zdesign-wired app) running, ask Claude Code:

> "Restyle whatever I just clicked to be rounder with a dark background."

Claude Code calls the MCP tools:

- `get_current_selection()` — what the designer just clicked (zd_id, file, line, tag, class)
- `resolve_id(zd_id)` — source location for any `data-zd-id` visible in the DOM
- `edit_class(zd_id, new_class)` — rewrite the class attribute (backup-safe)
- `undo_last()` — restore the most recent snapshot

If the app is on a non-default port, set `ZDESIGN_URL` or pass `--url` when
registering:

```bash
claude mcp add zdesign -- python -m zdesign.mcp --url http://127.0.0.1:9000
```

## Publishing to PyPI

Sanity check first, then build and upload:

```bash
pip install -e '.[dev]'
pytest -q && ruff check . && ruff format --check . && ty check
rm -rf dist/
python -m build         # produces dist/*.whl and dist/*.tar.gz
twine check dist/*
twine upload dist/*     # or `twine upload --repository testpypi dist/*` first
```

Version bumps live in `pyproject.toml` (`[project].version`). Tag the release
in git before uploading (`git tag v0.1.0 && git push --tags`).

## License

MIT — see `LICENSE`.

## Design docs

- Design: `docs/superpowers/specs/2026-07-09-zdesign-design.md`
- Plan: `docs/superpowers/plans/2026-07-09-zdesign-p1-mvp.md`
