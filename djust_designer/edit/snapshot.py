"""Backup-based snapshot/undo — works with or without git.

Snapshots each file into `<root>/.djust_designer/backups/` and appends a JSONL log.
`undo_last` restores the newest entry and trims the log.
"""

from __future__ import annotations

import json
import os
import shutil
import time


class Backups:
    def __init__(self, root: str) -> None:
        self.dir = os.path.join(root, ".djust_designer", "backups")
        os.makedirs(self.dir, exist_ok=True)
        self.log = os.path.join(self.dir, "log.jsonl")
        self._counter = 0

    def snapshot(self, file_path: str) -> str:
        ts_ms = int(time.time() * 1000)
        # Ensure uniqueness by appending a counter within the same millisecond
        ts = f"{ts_ms}_{self._counter}"
        self._counter += 1
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
