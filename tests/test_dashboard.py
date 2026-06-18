from __future__ import annotations

from developer_os.dashboard import build_dashboard, build_report


def test_build_dashboard_includes_core_sections() -> None:
    text = build_dashboard(
        learning_stats={"total_notes": 2, "subjects": {"dbms": 1, "systems": 1}},
        coding_stats={"total_problems_solved": 3},
        job_stats={"total_applications": 4, "interviews": 2, "offers": 1, "status_counts": {"Applied": 1}},
        github_stats={
            "username": "octo",
            "public_repos": 7,
            "stars": 11,
            "followers": 19,
            "contributions_total": 42,
            "recent_repositories": [{"name": "project", "stars": 5, "url": "https://example.com", "pushed_at": "2026-06-01"}],
        },
        leetcode_stats={
            "username": "learner",
            "total_solved": 120,
            "easy_solved": 60,
            "medium_solved": 45,
            "hard_solved": 15,
            "contest_rating": 1800,
        },
        github_trend=["- Public Repos: 7 (+1 vs previous)"],
        leetcode_trend=["- Total Solved: 120 (+5 vs previous)"],
        recent_activity=["Note: dbms", "Repo: project"],
    )

    assert "# Developer OS" in text
    assert "## GitHub Statistics" in text
    assert "## Coding Statistics" in text
    assert "## Trend Summaries" in text
    assert "## Recent Activity" in text
    assert "## Folder Structure" in text


def test_build_report_wraps_dashboard_text() -> None:
    report = build_report("Weekly Summary", "dashboard body")
    assert report.startswith("# Weekly Summary")
    assert "dashboard body" in report

