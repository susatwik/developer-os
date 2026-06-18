from __future__ import annotations

from pathlib import Path

import pytest

from developer_os import cli
from developer_os.csv_utils import CSVImportError, CSVSchema, read_csv_rows


def test_read_csv_rows_validates_headers(tmp_path: Path) -> None:
    path = tmp_path / "notes.csv"
    path.write_text("subject,topic\nmath,graphs\n", encoding="utf-8")

    with pytest.raises(CSVImportError, match="missing required columns"):
        read_csv_rows(path, CSVSchema("notes", ["subject", "topic", "summary", "date"]))


def test_import_export_csv_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    learning_path = tmp_path / "data" / "learning" / "notes.json"
    coding_path = tmp_path / "data" / "coding" / "problems.json"
    jobs_path = tmp_path / "data" / "jobs" / "applications.json"
    monkeypatch.setattr(cli, "LEARNING_PATH", learning_path)
    monkeypatch.setattr(cli, "CODING_PATH", coding_path)
    monkeypatch.setattr(cli, "JOBS_PATH", jobs_path)

    notes_csv = tmp_path / "notes.csv"
    notes_csv.write_text(
        "subject,topic,summary,date\n"
        "dbms,indexing,Learned clustered and non-clustered indexing,2026-06-01\n"
        "systems,caching,Reviewed eviction strategies,2026-06-02\n",
        encoding="utf-8",
    )
    coding_csv = tmp_path / "coding.csv"
    coding_csv.write_text(
        "platform,name,difficulty,topic,date\n"
        "leetcode,Two Sum,easy,arrays,2026-06-01\n"
        "gfg,Binary Search,medium,searching,2026-06-02\n",
        encoding="utf-8",
    )
    jobs_csv = tmp_path / "jobs.csv"
    jobs_csv.write_text(
        "company,role,status,application_date\n"
        "Acme,Backend Engineer,Applied,2026-06-01\n"
        "Beta,SRE,Interview,2026-06-02\n",
        encoding="utf-8",
    )

    assert cli.import_notes_csv(notes_csv) == 2
    assert cli.import_coding_csv(coding_csv) == 2
    assert cli.import_jobs_csv(jobs_csv) == 2

    notes_out = tmp_path / "notes-out.csv"
    coding_out = tmp_path / "coding-out.csv"
    jobs_out = tmp_path / "jobs-out.csv"
    cli.export_notes_csv(notes_out)
    cli.export_coding_csv(coding_out)
    cli.export_jobs_csv(jobs_out)

    assert "dbms" in notes_out.read_text(encoding="utf-8")
    assert "leetcode" in coding_out.read_text(encoding="utf-8")
    assert "Backend Engineer" in jobs_out.read_text(encoding="utf-8")

    cli.generate_templates(tmp_path / "templates")
    assert (tmp_path / "templates" / "learning_notes_template.csv").exists()
    assert (tmp_path / "templates" / "coding_progress_template.csv").exists()
    assert (tmp_path / "templates" / "job_applications_template.csv").exists()


def test_cli_main_routes_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    learning_path = tmp_path / "data" / "learning" / "notes.json"
    coding_path = tmp_path / "data" / "coding" / "problems.json"
    jobs_path = tmp_path / "data" / "jobs" / "applications.json"
    report_dir = tmp_path / "reports"
    readme_path = tmp_path / "README.md"
    report_path = report_dir / "dashboard.md"

    monkeypatch.setattr(cli, "LEARNING_PATH", learning_path)
    monkeypatch.setattr(cli, "CODING_PATH", coding_path)
    monkeypatch.setattr(cli, "JOBS_PATH", jobs_path)
    monkeypatch.setattr(cli, "REPORT_DIR", report_dir)
    monkeypatch.setattr(cli, "README_PATH", readme_path)
    monkeypatch.setattr(cli, "README_REPORT_PATH", report_path)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "TRACKER_DIRS", (tmp_path / "data" / "learning", tmp_path / "data" / "coding", tmp_path / "data" / "jobs", tmp_path / "reports"))
    monkeypatch.setattr(cli, "SNAPSHOTS_DIR", tmp_path / "data" / "snapshots")

    assert cli.main(["add-note", "--subject", "dbms", "--topic", "indexing", "--summary", "Learned indexing"]) == 0
    assert cli.main(["add-problem", "--platform", "leetcode", "--name", "Two Sum", "--difficulty", "easy", "--topic", "arrays"]) == 0
    assert cli.main(["add-application", "--company", "Acme", "--role", "Backend Engineer", "--status", "Applied"]) == 0

    assert cli.main(["generate-csv-templates", "--output-dir", str(tmp_path / "templates")]) == 0

    fake_context = type(
        "Context",
        (),
        {
            "learning_stats": {"total_notes": 1, "subjects": {"dbms": 1}, "recent": []},
            "coding_stats": {"total_problems_solved": 1, "leetcode_total": 1, "gfg_total": 0, "difficulty_counts": {}, "recent": []},
            "job_stats": {
                "total_applications": 1,
                "interviews": 0,
                "offers": 0,
                "status_counts": {"Applied": 1},
                "recent": [],
            },
            "github_stats": {
                "username": "octo",
                "public_repos": 1,
                "stars": 2,
                "followers": 3,
                "contributions_total": 4,
                "recent_repositories": [],
            },
            "leetcode_stats": {
                "username": "learner",
                "total_solved": 5,
                "easy_solved": 2,
                "medium_solved": 2,
                "hard_solved": 1,
                "contest_rating": 1800,
                "recent_repositories": [],
            },
            "github_trend": ["- public repos: 1 (+0 vs previous)"],
            "leetcode_trend": ["- total solved: 5 (+0 vs previous)"],
            "recent_activity": ["Note: dbms"],
            "github_error": None,
            "leetcode_error": None,
        },
    )()

    monkeypatch.setattr(cli, "generate_context", lambda refresh=True: fake_context)
    captured = {}

    def fake_write_dashboard(context: object) -> None:
        captured["dashboard"] = context
        readme_path.write_text("dashboard", encoding="utf-8")

    monkeypatch.setattr(cli, "write_dashboard", fake_write_dashboard)
    monkeypatch.setattr(
        cli,
        "write_report",
        lambda report_name, title, context=None: captured.setdefault("report", (report_name, title, context)),
    )

    assert cli.main(["generate-dashboard", "--report", "weekly"]) == 0
    assert captured["dashboard"] is fake_context
    assert captured["report"][0] == "weekly"
    assert readme_path.exists()

    readme_path.write_text("expected", encoding="utf-8")
    monkeypatch.setattr(cli, "generate_dashboard", lambda context=None: "expected")
    assert cli.main(["check"]) == 0
