from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TraceLogger:
    def __init__(self, root: str, puzzle_id: str):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.run_dir = Path(root) / f"{stamp}_{puzzle_id}"
        suffix = 1
        while self.run_dir.exists():
            self.run_dir = Path(root) / f"{stamp}_{puzzle_id}_{suffix}"
            suffix += 1
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.run_dir / "trace.jsonl"
        self._step = 0

    def log(self, event: str, **payload: Any) -> None:
        self._step += 1
        record = {"step": self._step, "event": event, **payload}
        with self.path.open("a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    def write_json(self, name: str, payload: Any) -> None:
        (self.run_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
