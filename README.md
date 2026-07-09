# zdesign

Visual design collaboration layer for [djust](https://github.com/szto/djust) (Django) apps.
Point at any element on your running page → see its source template + line → edit its
Tailwind classes with automatic write-back → undo with one click. No terminal, no code
editor. P2 will add an in-app Claude chat panel.

**Runs on `DEBUG=True` only.** No traces in production.

## Install

````
pip install -e path/to/zdesign
````

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

## Design docs

- Design: `docs/superpowers/specs/2026-07-09-zdesign-design.md`
- Plan: `docs/superpowers/plans/2026-07-09-zdesign-p1-mvp.md`
