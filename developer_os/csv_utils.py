"""CSV import/export helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CSVSchema:
    name: str
    headers: list[str]


class CSVImportError(ValueError):
    """Raised when CSV input cannot be imported safely."""


def read_csv_rows(path: Path, schema: CSVSchema) -> list[dict[str, str]]:
    if not path.exists():
        raise CSVImportError(f"{schema.name}: file not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise CSVImportError(f"{schema.name}: CSV file is missing a header row")

        missing = [header for header in schema.headers if header not in reader.fieldnames]
        extra = [header for header in reader.fieldnames if header not in schema.headers]
        if missing:
            raise CSVImportError(f"{schema.name}: missing required columns: {', '.join(missing)}")
        if extra:
            raise CSVImportError(f"{schema.name}: unexpected columns: {', '.join(extra)}")

        rows: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            cleaned = {key: (value or "").strip() for key, value in row.items() if key is not None}
            if not any(cleaned.values()):
                continue
            cleaned["__row__"] = str(row_number)
            rows.append(cleaned)
        return rows


def write_csv_rows(path: Path, headers: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def write_sample_csv(path: Path, headers: list[str], sample_rows: list[dict[str, str]]) -> None:
    write_csv_rows(path, headers, sample_rows)

