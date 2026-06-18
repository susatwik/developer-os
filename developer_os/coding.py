"""Coding tracker."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .dates import validate_iso_date
from .storage import JsonStore


def coding_store(path: Path) -> JsonStore:
    return JsonStore(path=path, default={"leetcode": [], "gfg": []})


def add_problem(
    store: JsonStore,
    platform: str,
    name: str,
    difficulty: str,
    topic: str,
    problem_date: str | None = None,
) -> dict[str, Any]:
    entry = {
        "date": validate_iso_date(problem_date),
        "platform": platform,
        "name": name.strip(),
        "difficulty": difficulty.strip(),
        "topic": topic.strip(),
    }

    def mutate(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data or {})
        bucket = data.setdefault(platform, [])
        bucket.append(entry)
        return data

    return store.update(mutate)


def build_stats(data: dict[str, Any]) -> dict[str, Any]:
    data = data or {}
    leetcode = list(data.get("leetcode", []))
    gfg = list(data.get("gfg", []))
    recent = sorted(leetcode + gfg, key=lambda item: item.get("date", ""), reverse=True)[:5]
    by_difficulty = Counter(item.get("difficulty", "unknown") for item in leetcode + gfg)
    return {
        "leetcode_total": len(leetcode),
        "gfg_total": len(gfg),
        "total_problems_solved": len(leetcode) + len(gfg),
        "difficulty_counts": dict(sorted(by_difficulty.items())),
        "recent": recent,
    }


def export_problems(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for platform in ("leetcode", "gfg"):
        for problem in (data or {}).get(platform, []):
            rows.append(
                {
                    "platform": platform,
                    "name": problem.get("name", ""),
                    "difficulty": problem.get("difficulty", ""),
                    "topic": problem.get("topic", ""),
                    "date": problem.get("date", ""),
                }
            )
    return rows
