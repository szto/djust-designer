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
        source = super().get_contents(origin)  # type: ignore[misc]  # ty: ignore[unresolved-attribute]
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
