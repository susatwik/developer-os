"""Developer OS command-line interface."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from developer_os.analytics import DeveloperOSAnalytics
from developer_os.coding import add_problem, coding_store, export_problems
from developer_os.config import (
    CODING_DIR,
    JOB_DIR,
    LEARNING_DIR,
    README_PATH,
    REPORT_DIR,
    ROOT,
    SNAPSHOTS_DIR,
    TRACKER_DIRS,
)
from developer_os.csv_utils import (
    CSVImportError,
    CSVSchema,
    read_csv_rows,
    write_csv_rows,
    write_sample_csv,
)
from developer_os.dashboard import build_dashboard, build_report
from developer_os.dates import validate_iso_date
from developer_os.errors import DeveloperOSError
from developer_os.jobs import (
    add_application,
    export_applications,
    jobs_store,
    normalize_status,
)
from developer_os.learning import add_note, export_notes, learning_store
from developer_os.settings import load_settings

LEARNING_PATH = LEARNING_DIR / "notes.json"
CODING_PATH = CODING_DIR / "problems.json"
JOBS_PATH = JOB_DIR / "applications.json"
README_REPORT_PATH = REPORT_DIR / "dashboard.md"

REQUIRED_README_ASSETS = (
    "assets/hero-banner.png",
    "assets/dashboard.png",
    "assets/statistics.png",
    "assets/search.png",
    "assets/mobile-view.png",
    "assets/demo.gif",
    "assets/logo.png",
)
BRANDING_ASSETS = (
    "assets/social-preview.png",
    "assets/favicon.png",
    "assets/icon.png",
)
EXPECTED_API_ENDPOINT_COUNT = 9

NOTE_SCHEMA = CSVSchema("learning notes", ["subject", "topic", "summary", "date"])
CODING_SCHEMA = CSVSchema("coding progress", ["platform", "name", "difficulty", "topic", "date"])
JOBS_SCHEMA = CSVSchema("job applications", ["company", "role", "status", "application_date"])

STATUS_CHOICES = ["Applied", "OA", "Interview", "Rejected", "Offer"]


def ensure_layout() -> None:
    for directory in TRACKER_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_context(refresh: bool = True):
    settings = load_settings()
    return DeveloperOSAnalytics(settings).build_context(refresh=refresh)


def generate_dashboard(context=None) -> str:
    if context is None:
        context = generate_context()
    return build_dashboard(
        context.learning_stats,
        context.coding_stats,
        context.job_stats,
        context.github_stats,
        context.leetcode_stats,
        context.github_trend,
        context.leetcode_trend,
        context.recent_activity,
        context.github_error,
        context.leetcode_error,
    )


def write_dashboard(context=None) -> None:
    dashboard = generate_dashboard(context)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    README_REPORT_PATH.write_text(dashboard, encoding="utf-8")


def write_report(report_name: str, title: str, context=None) -> None:
    dashboard = generate_dashboard(context)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"{report_name}.md"
    report_path.write_text(build_report(title, dashboard), encoding="utf-8")


def _extract_section(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        return []

    section: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## ") and line.strip() != heading:
            break
        section.append(line)
    return section


def _readme_validation_errors(readme_text: str) -> list[str]:
    errors: list[str] = []
    normalized = readme_text.casefold()

    if not readme_text.strip():
        errors.append("README.md is missing or empty.")
        return errors

    for asset in REQUIRED_README_ASSETS:
        if asset not in readme_text:
            errors.append(f"README.md is missing the asset reference `{asset}`.")
        elif not (ROOT / asset).exists():
            errors.append(f"Referenced asset `{asset}` is missing from the repository.")

    for asset in BRANDING_ASSETS:
        if not (ROOT / asset).exists():
            errors.append(f"Branding asset `{asset}` is missing from the repository.")

    if "dashboard-screenshot-placeholder.svg" in readme_text:
        errors.append("README.md still references the placeholder screenshot asset.")

    match = re.search(r"api-(\d+)(?:%20|\s)+routes", normalized)
    if not match:
        errors.append("README.md is missing the API routes badge.")
        api_badge_count = None
    else:
        api_badge_count = int(match.group(1))
        if api_badge_count != EXPECTED_API_ENDPOINT_COUNT:
            errors.append(
                f"README.md API badge reports {api_badge_count} routes, expected {EXPECTED_API_ENDPOINT_COUNT}."
            )

    api_section = _extract_section(readme_text, "## API Reference")
    endpoint_rows = [
        line
        for line in api_section
        if line.startswith("| `GET` |") or line.startswith("| `POST` |")
    ]
    if len(endpoint_rows) != EXPECTED_API_ENDPOINT_COUNT:
        errors.append(
            f"README.md API reference lists {len(endpoint_rows)} endpoints, expected {EXPECTED_API_ENDPOINT_COUNT}."
        )
    elif api_badge_count is not None and len(endpoint_rows) != api_badge_count:
        errors.append(
            f"README.md API badge and API reference disagree: badge shows {api_badge_count}, table lists {len(endpoint_rows)}."
        )

    return errors


def _require_text(row: dict[str, str], field: str, row_number: int, schema_name: str) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        raise CSVImportError(f"{schema_name} row {row_number}: '{field}' is required")
    return value


def _require_date(row: dict[str, str], field: str, row_number: int, schema_name: str) -> str:
    value = (row.get(field) or "").strip()
    try:
        return validate_iso_date(value or None)
    except ValueError as exc:
        raise CSVImportError(f"{schema_name} row {row_number}: '{field}' must use YYYY-MM-DD format") from exc


def import_notes_csv(path: Path) -> int:
    rows = read_csv_rows(path, NOTE_SCHEMA)
    store = learning_store(LEARNING_PATH)
    entries: list[dict[str, Any]] = []
    for row in rows:
        row_number = int(row["__row__"])
        entries.append(
            {
                "date": _require_date(row, "date", row_number, NOTE_SCHEMA.name),
                "subject": _require_text(row, "subject", row_number, NOTE_SCHEMA.name),
                "topic": _require_text(row, "topic", row_number, NOTE_SCHEMA.name),
                "summary": _require_text(row, "summary", row_number, NOTE_SCHEMA.name),
            }
        )

    def mutate(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data or {})
        data.setdefault("notes", [])
        data["notes"].extend(entries)
        return data

    store.update(mutate)
    return len(entries)


def import_coding_csv(path: Path) -> int:
    rows = read_csv_rows(path, CODING_SCHEMA)
    store = coding_store(CODING_PATH)
    entries_by_platform: dict[str, list[dict[str, Any]]] = {"leetcode": [], "gfg": []}

    for row in rows:
        row_number = int(row["__row__"])
        platform = _require_text(row, "platform", row_number, CODING_SCHEMA.name).casefold()
        if platform not in entries_by_platform:
            raise CSVImportError(
                f"{CODING_SCHEMA.name} row {row_number}: invalid platform '{row.get('platform', '')}'. Expected leetcode or gfg"
            )
        entries_by_platform[platform].append(
            {
                "date": _require_date(row, "date", row_number, CODING_SCHEMA.name),
                "platform": platform,
                "name": _require_text(row, "name", row_number, CODING_SCHEMA.name),
                "difficulty": _require_text(row, "difficulty", row_number, CODING_SCHEMA.name),
                "topic": _require_text(row, "topic", row_number, CODING_SCHEMA.name),
            }
        )

    def mutate(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data or {})
        data.setdefault("leetcode", [])
        data.setdefault("gfg", [])
        for platform, entries in entries_by_platform.items():
            data[platform].extend(entries)
        return data

    store.update(mutate)
    return sum(len(entries) for entries in entries_by_platform.values())


def import_jobs_csv(path: Path) -> int:
    rows = read_csv_rows(path, JOBS_SCHEMA)
    store = jobs_store(JOBS_PATH)
    entries: list[dict[str, Any]] = []
    for row in rows:
        row_number = int(row["__row__"])
        entries.append(
            {
                "application_date": _require_date(row, "application_date", row_number, JOBS_SCHEMA.name),
                "company": _require_text(row, "company", row_number, JOBS_SCHEMA.name),
                "role": _require_text(row, "role", row_number, JOBS_SCHEMA.name),
                "status": normalize_status(_require_text(row, "status", row_number, JOBS_SCHEMA.name)),
            }
        )

    def mutate(data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data or {})
        data.setdefault("applications", [])
        data["applications"].extend(entries)
        return data

    store.update(mutate)
    return len(entries)


def export_notes_csv(path: Path) -> None:
    rows = export_notes(learning_store(LEARNING_PATH).read())
    write_csv_rows(path, NOTE_SCHEMA.headers, rows)


def export_coding_csv(path: Path) -> None:
    rows = export_problems(coding_store(CODING_PATH).read())
    write_csv_rows(path, CODING_SCHEMA.headers, rows)


def export_jobs_csv(path: Path) -> None:
    rows = export_applications(jobs_store(JOBS_PATH).read())
    write_csv_rows(path, JOBS_SCHEMA.headers, rows)


def generate_templates(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_sample_csv(
        output_dir / "learning_notes_template.csv",
        NOTE_SCHEMA.headers,
        [
            {
                "subject": "dbms",
                "topic": "indexing",
                "summary": "Learned clustered and non-clustered indexing",
                "date": "2026-06-18",
            }
        ],
    )
    write_sample_csv(
        output_dir / "coding_progress_template.csv",
        CODING_SCHEMA.headers,
        [
            {
                "platform": "leetcode",
                "name": "Two Sum",
                "difficulty": "easy",
                "topic": "arrays",
                "date": "2026-06-18",
            }
        ],
    )
    write_sample_csv(
        output_dir / "job_applications_template.csv",
        JOBS_SCHEMA.headers,
        [
            {
                "company": "Acme",
                "role": "Backend Engineer",
                "status": "Applied",
                "application_date": "2026-06-18",
            }
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="developer-os", description="Developer OS CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    note = subparsers.add_parser("add-note", help="store a learning note")
    note.add_argument("--subject", required=True)
    note.add_argument("--topic", required=True)
    note.add_argument("--summary", required=True)
    note.add_argument("--date")

    problem = subparsers.add_parser("add-problem", help="store coding progress")
    problem.add_argument("--platform", choices=["leetcode", "gfg"], required=True)
    problem.add_argument("--name", required=True)
    problem.add_argument("--difficulty", required=True)
    problem.add_argument("--topic", required=True)
    problem.add_argument("--date")

    application = subparsers.add_parser("add-application", help="store a job application")
    application.add_argument("--company", required=True)
    application.add_argument("--role", required=True)
    application.add_argument("--status", choices=STATUS_CHOICES, required=True)
    application.add_argument("--application-date")

    import_notes = subparsers.add_parser("import-notes", help="import learning notes from CSV")
    import_notes.add_argument("--file", required=True, type=Path)

    import_coding = subparsers.add_parser("import-coding", help="import coding progress from CSV")
    import_coding.add_argument("--file", required=True, type=Path)

    import_jobs = subparsers.add_parser("import-jobs", help="import job applications from CSV")
    import_jobs.add_argument("--file", required=True, type=Path)

    export_notes = subparsers.add_parser("export-notes", help="export learning notes to CSV")
    export_notes.add_argument("--output", required=True, type=Path)

    export_coding = subparsers.add_parser("export-coding", help="export coding progress to CSV")
    export_coding.add_argument("--output", required=True, type=Path)

    export_jobs = subparsers.add_parser("export-jobs", help="export job applications to CSV")
    export_jobs.add_argument("--output", required=True, type=Path)

    templates = subparsers.add_parser("generate-csv-templates", help="generate sample CSV templates")
    templates.add_argument("--output-dir", type=Path, default=ROOT / "templates")

    generate = subparsers.add_parser("generate-dashboard", help="refresh dashboard reports")
    generate.add_argument("--report", choices=["daily", "weekly", "monthly"])

    subparsers.add_parser("check", help="verify README.md and release assets")

    return parser


def _run_import(handler, path: Path, label: str) -> int:
    try:
        count = handler(path)
    except CSVImportError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    print(f"Imported {count} {label}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ensure_layout()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "add-note":
        add_note(
            learning_store(LEARNING_PATH),
            subject=args.subject,
            topic=args.topic,
            summary=args.summary,
            note_date=validate_iso_date(args.date),
        )
        print("Added learning note.")
        return 0

    if args.command == "add-problem":
        add_problem(
            coding_store(CODING_PATH),
            platform=args.platform,
            name=args.name,
            difficulty=args.difficulty,
            topic=args.topic,
            problem_date=validate_iso_date(args.date),
        )
        print("Added coding problem.")
        return 0

    if args.command == "add-application":
        add_application(
            jobs_store(JOBS_PATH),
            company=args.company,
            role=args.role,
            status=args.status,
            application_date=validate_iso_date(args.application_date),
        )
        print("Added job application.")
        return 0

    if args.command == "import-notes":
        return _run_import(import_notes_csv, args.file, "learning notes")

    if args.command == "import-coding":
        return _run_import(import_coding_csv, args.file, "coding problems")

    if args.command == "import-jobs":
        return _run_import(import_jobs_csv, args.file, "job applications")

    if args.command == "export-notes":
        export_notes_csv(args.output)
        print(f"Exported learning notes to {args.output}")
        return 0

    if args.command == "export-coding":
        export_coding_csv(args.output)
        print(f"Exported coding progress to {args.output}")
        return 0

    if args.command == "export-jobs":
        export_jobs_csv(args.output)
        print(f"Exported job applications to {args.output}")
        return 0

    if args.command == "generate-csv-templates":
        generate_templates(args.output_dir)
        print(f"Generated CSV templates in {args.output_dir}")
        return 0

    if args.command == "generate-dashboard":
        try:
            context = generate_context(refresh=True)
            write_dashboard(context)
            if args.report:
                report_titles = {
                    "daily": "Developer OS Daily Report",
                    "weekly": "Developer OS Weekly Summary",
                    "monthly": "Developer OS Monthly Report",
                }
                write_report(args.report, report_titles[args.report], context)
            print(f"Updated {README_REPORT_PATH.relative_to(ROOT)}")
            return 0
        except DeveloperOSError as exc:
            print(f"Generation failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "check":
        try:
            current = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
            errors = _readme_validation_errors(current)
            if errors:
                print("README.md validation failed:")
                for error in errors:
                    print(f"- {error}")
                return 1
            print("README.md is valid and release assets are aligned.")
            return 0
        except OSError as exc:
            print(f"Check failed: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
