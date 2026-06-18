"""Job application tracker."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .dates import validate_iso_date
from .storage import JsonStore


def jobs_store(path: Path) -> JsonStore:
    return JsonStore(path=path, default={"applications": []})


def normalize_status(status: str) -> str:
    normalized = status.strip().casefold()
    allowed = {
        "applied": "Applied",
        "oa": "OA",
        "interview": "Interview",
        "rejected": "Rejected",
        "offer": "Offer",
    }
    if normalized not in allowed:
        raise ValueError(
            f"Invalid job status: {status}. Expected one of: Applied, OA, Interview, Rejected, Offer."
        )
    return allowed[normalized]


def add_application(
    store: JsonStore,
    company: str,
    role: str,
    status: str,
    application_date: str | None = None,
) -> dict[str, Any]:
    entry = {
        "application_date": validate_iso_date(application_date),
        "company": company.strip(),
        "role": role.strip(),
        "status": normalize_status(status),
    }

    def mutate(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data or {})
        data.setdefault("applications", [])
        data["applications"].append(entry)
        return data

    return store.update(mutate)


def build_stats(data: dict[str, Any]) -> dict[str, Any]:
    applications = list((data or {}).get("applications", []))
    status_counts = Counter(item.get("status", "unknown") for item in applications)
    recent = sorted(applications, key=lambda item: item.get("application_date", ""), reverse=True)[:5]
    return {
        "total_applications": len(applications),
        "interviews": status_counts.get("Interview", 0),
        "offers": status_counts.get("Offer", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "recent": recent,
    }


def export_applications(data: dict[str, Any]) -> list[dict[str, Any]]:
    applications = list((data or {}).get("applications", []))
    return [
        {
            "company": application.get("company", ""),
            "role": application.get("role", ""),
            "status": application.get("status", ""),
            "application_date": application.get("application_date", ""),
        }
        for application in applications
    ]
