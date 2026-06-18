"""Date helpers."""

from __future__ import annotations

from datetime import date, datetime


def today_iso() -> str:
    return date.today().isoformat()


def validate_iso_date(value: str | None) -> str:
    if value is None:
        return today_iso()
    datetime.strptime(value, "%Y-%m-%d")
    return value

