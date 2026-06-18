"""Learning tracker."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .dates import validate_iso_date
from .storage import JsonStore


def learning_store(path: Path) -> JsonStore:
    return JsonStore(path=path, default={"notes": []})


def add_note(
    store: JsonStore,
    subject: str,
    topic: str,
    summary: str,
    note_date: str | None = None,
) -> dict[str, Any]:
    entry = {
        "date": validate_iso_date(note_date),
        "subject": subject.strip(),
        "topic": topic.strip(),
        "summary": summary.strip(),
    }

    def mutate(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data or {})
        data.setdefault("notes", [])
        data["notes"].append(entry)
        return data

    return store.update(mutate)


def build_stats(data: dict[str, Any]) -> dict[str, Any]:
    notes = list((data or {}).get("notes", []))
    by_subject = Counter(note.get("subject", "General") for note in notes)
    recent = sorted(notes, key=lambda item: item.get("date", ""), reverse=True)[:5]
    return {
        "total_notes": len(notes),
        "subjects": dict(sorted(by_subject.items())),
        "recent": recent,
    }


def export_notes(data: dict[str, Any]) -> list[dict[str, Any]]:
    notes = list((data or {}).get("notes", []))
    return [
        {
            "subject": note.get("subject", ""),
            "topic": note.get("topic", ""),
            "summary": note.get("summary", ""),
            "date": note.get("date", ""),
        }
        for note in notes
    ]
