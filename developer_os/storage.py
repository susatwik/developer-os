"""JSON-backed storage helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class JsonStore:
    path: Path
    default: Any

    def read(self) -> Any:
        if not self.path.exists():
            return self.default
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return self.default

    def write(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def update(self, mutator: Callable[[Any], Any]) -> Any:
        current = self.read()
        updated = mutator(current)
        self.write(updated)
        return updated
