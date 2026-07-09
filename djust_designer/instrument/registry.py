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
