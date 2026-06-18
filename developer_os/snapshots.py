"""Historical snapshot storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import JsonStore


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SnapshotStore:
    path: Path

    def _store(self) -> JsonStore:
        return JsonStore(path=self.path, default={"snapshots": []})

    def history(self) -> list[dict[str, Any]]:
        data = self._store().read()
        return list((data or {}).get("snapshots", []))

    def append(self, snapshot: dict[str, Any]) -> None:
        def mutate(data: dict[str, Any]) -> dict[str, Any]:
            data = dict(data or {})
            data.setdefault("snapshots", [])
            data["snapshots"].append(snapshot)
            return data

        self._store().update(mutate)

    def successful(self) -> list[dict[str, Any]]:
        return [snapshot for snapshot in self.history() if snapshot.get("status") == "ok"]

    def latest_successful(self) -> dict[str, Any] | None:
        successes = self.successful()
        return successes[-1] if successes else None

    def previous_successful(self) -> dict[str, Any] | None:
        successes = self.successful()
        return successes[-2] if len(successes) >= 2 else None

