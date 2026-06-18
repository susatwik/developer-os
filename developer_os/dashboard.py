"""README/dashboard generation."""

from __future__ import annotations


def _format_mapping(title: str, mapping: dict[str, object]) -> list[str]:
    lines = [f"### {title}"]
    if mapping:
        for key, value in mapping.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- None yet")
    return lines


def _format_activity(items: list[str]) -> list[str]:
    if not items:
        return ["- No activity yet"]
    return [f"- {item}" for item in items]


def _format_repos(repos: list[dict[str, object]]) -> list[str]:
    if not repos:
        return ["- No recent repositories yet."]
    lines: list[str] = []
    for repo in repos[:5]:
        name = repo.get("name", "")
        url = repo.get("url", "")
        stars = repo.get("stars", 0)
        pushed_at = repo.get("pushed_at", "")
        lines.append(f"- {name} ({stars} stars) {url} {pushed_at}".strip())
    return lines


def build_dashboard(
    learning_stats: dict[str, object],
    coding_stats: dict[str, object],
    job_stats: dict[str, object],
    github_stats: dict[str, object],
    leetcode_stats: dict[str, object],
    github_trend: list[str],
    leetcode_trend: list[str],
    recent_activity: list[str],
    github_error: str | None = None,
    leetcode_error: str | None = None,
) -> str:
    lines: list[str] = [
        "# Developer OS",
        "",
        "[![Build Status](https://img.shields.io/github/actions/workflow/status/susatwik/developer-os/ci.yml?branch=main)](https://github.com/susatwik/developer-os/actions)",
        "[![Coverage](https://img.shields.io/badge/coverage-89.2%25-brightgreen)](./coverage.xml)",
        "[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)",
        "[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)",
        "",
        "Developer OS is a production-style developer analytics platform for tracking learning, coding, job search progress, and live profile stats in one place.",
        "",
        "## Project Overview",
        "",
        "Developer OS combines a lightweight Python CLI, JSON-backed manual tracking, CSV import/export, live integrations for LeetCode and GitHub, and GitHub Actions automation to create a maintainable personal analytics hub.",
        "",
        "## Features",
        "",
        "- Learning tracker for daily notes organized by subject and topic.",
        "- Coding tracker for LeetCode and GeeksforGeeks progress.",
        "- Job application tracker for applications, OA rounds, interviews, and offers.",
        "- CSV import and export with sample templates and validation.",
        "- Lightweight FastAPI web dashboard for viewing stats and adding entries.",
        "- Live LeetCode integration with historical snapshots.",
        "- Live GitHub integration for profile and repository analytics.",
        "- Automated README dashboard generation from the latest data.",
        "- Scheduled GitHub Actions workflows for daily, weekly, and monthly refreshes.",
        "",
        "## Architecture Diagram",
        "",
        "```mermaid",
        "flowchart TD",
        "  A[Developer OS CLI]",
        "  B[JSON Storage]",
        "  C[CSV Import / Export]",
        "  D[LeetCode Service]",
        "  E[GitHub Service]",
        "  F[Snapshot Store]",
        "  G[Dashboard Generator]",
        "  H[README.md]",
        "  I[GitHub Actions]",
        "  A --> B",
        "  A --> C",
        "  A --> D",
        "  A --> E",
        "  D --> F",
        "  E --> F",
        "  B --> G",
        "  F --> G",
        "  G --> H",
        "  I --> A",
        "```",
        "",
        "## Installation",
        "",
        "```bash",
        "python3 -m pip install -e '.[web]'",
        "developer-os --help",
        "developer-os-web",
        "```",
        "",
        "## Usage Examples",
        "",
        "```bash",
        "developer-os add-note --subject dbms --topic indexing --summary \"Learned clustered and non-clustered indexing\"",
        "developer-os add-problem --platform leetcode --name \"Two Sum\" --difficulty easy --topic arrays",
        "developer-os add-application --company \"Acme\" --role \"Backend Engineer\" --status Applied",
        "developer-os import-notes --file templates/learning_notes_template.csv",
        "developer-os import-coding --file templates/coding_progress_template.csv",
        "developer-os import-jobs --file templates/job_applications_template.csv",
        "developer-os generate-csv-templates",
        "developer-os generate-dashboard",
        "developer-os-web",
        "```",
        "",
        "## Dashboard Screenshot Placeholder",
        "",
        "![Dashboard Screenshot Placeholder](assets/dashboard-screenshot-placeholder.svg)",
        "",
        "> Replace the placeholder above with a real screenshot of your generated dashboard when you have one.",
        "",
        "## Roadmap",
        "",
        "- Add charts for weekly and monthly trends.",
        "- Add filtering by subject, company, platform, and status.",
        "- Add optional SQLite storage for larger histories.",
        "- Add richer dashboard rendering for trend summaries.",
        "- Add auth-aware GitHub integrations for private profile data.",
        "",
        "## Technologies Used",
        "",
        "- Python 3.10+",
        "- Standard library JSON and CSV tooling",
        "- GitHub API",
        "- LeetCode GraphQL API",
        "- GitHub Actions",
        "- Mermaid for architecture documentation",
        "",
        "## Overview",
        "",
        f"- Total Notes: {learning_stats.get('total_notes', 0)}",
        f"- Total Problems Solved: {coding_stats.get('total_problems_solved', 0)}",
        f"- Applications Sent: {job_stats.get('total_applications', 0)}",
        f"- Interviews: {job_stats.get('interviews', 0)}",
        f"- Offers: {job_stats.get('offers', 0)}",
        "",
        "## GitHub Statistics",
        "",
        f"- Username: {github_stats.get('username') or 'Not configured'}",
        f"- Public Repositories: {github_stats.get('public_repos', 0)}",
        f"- Stars: {github_stats.get('stars', 0)}",
        f"- Followers: {github_stats.get('followers', 0)}",
        f"- Contributions This Year: {github_stats.get('contributions_total', 0)}",
    ]

    if github_error:
        lines.extend(["- Status: unavailable", f"- Error: {github_error}"])
    else:
        lines.append("- Status: healthy")
    lines.extend(["", "### Recent Repositories"])
    lines.extend(_format_repos(github_stats.get("recent_repositories", [])))

    lines.extend(
        [
            "",
            "## Coding Statistics",
            "",
            f"- Username: {leetcode_stats.get('username') or 'Not configured'}",
            f"- Total Solved: {leetcode_stats.get('total_solved', 0)}",
            f"- Easy Solved: {leetcode_stats.get('easy_solved', 0)}",
            f"- Medium Solved: {leetcode_stats.get('medium_solved', 0)}",
            f"- Hard Solved: {leetcode_stats.get('hard_solved', 0)}",
        f"- Contest Rating: {leetcode_stats.get('contest_rating') or 'N/A'}",
        ]
    )
    if leetcode_error:
        lines.extend(["- Status: unavailable", f"- Error: {leetcode_error}"])
    else:
        lines.append("- Status: healthy")

    lines.extend(
        [
            "",
            "## Trend Summaries",
            "",
            "### GitHub",
        ]
    )
    lines.extend(github_trend or ["- No trend data yet."])
    lines.extend(["", "### LeetCode", ""])
    lines.extend(leetcode_trend or ["- No trend data yet."])
    lines.extend(
        [
            "",
            "## Recent Activity",
            "",
        ]
    )
    lines.extend(_format_activity(recent_activity))
    lines.extend(
        [
            "",
            "## Learning Tracker",
            "",
        ]
    )
    lines.extend(_format_mapping("By subject", learning_stats.get("subjects", {})))
    lines.extend(
        [
            "",
            "## Job Application Tracker",
            "",
        ]
    )
    lines.extend(_format_mapping("Status counts", job_stats.get("status_counts", {})))
    lines.extend(
        [
            "",
        "## Configuration",
        "",
        "- `config.yaml` stores usernames, tokens, and storage paths.",
        "- Environment variables override config values.",
        "- Supported environment variables: `DEVOS_GITHUB_USERNAME`, `DEVOS_GITHUB_TOKEN`, `DEVOS_LEETCODE_USERNAME`, `DEVOS_LEETCODE_SESSION_COOKIE`, `DEVOS_CONFIG_PATH`, `DEVOS_SNAPSHOTS_DIR`, `DEVOS_DASHBOARD_PATH`.",
        "- Repository docs: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, and `.github/` templates.",
        "",
        "## Open Source",
        "",
        "- Contribution guide: `CONTRIBUTING.md`.",
        "- Community rules: `CODE_OF_CONDUCT.md`.",
        "- Security policy: `SECURITY.md`.",
        "- Release notes: `CHANGELOG.md`.",
        "",
        "## Folder Structure",
            "",
            "```text",
            "developer-os/",
            "├── developer_os/           # Python package",
            "├── scripts/                # CLI wrapper",
            "├── templates/              # Sample CSV templates",
            "├── data/                   # JSON storage, snapshots, and reports",
            "├── config.yaml             # Local configuration",
            "├── .github/workflows/      # Scheduled automation",
            "├── pyproject.toml          # Project metadata",
            "└── README.md               # Generated dashboard",
            "```",
            "",
        "## Automation",
        "",
        "- Daily workflow refreshes `README.md` and `data/reports/dashboard.md`.",
        "- Weekly workflow refreshes the dashboard snapshot and the weekly report.",
        "- Monthly workflow refreshes the dashboard snapshot and the monthly report.",
        "",
        "## Web Dashboard",
        "",
        "- Start the web app with `developer-os-web` or `uvicorn developer_os.webapp:app --reload`.",
        "- Use the dashboard to view stats, add notes, add coding entries, add job applications, search entries, and inspect analytics.",
        "",
        "## Deployment",
        "",
        "- Docker image, compose setup, and provider instructions live in `docs/deployment.md`.",
        "- Production endpoints: `/health` and `/version`.",
        "",
        "## CSV Templates",
            "",
            "- `templates/learning_notes_template.csv`",
            "- `templates/coding_progress_template.csv`",
            "- `templates/job_applications_template.csv`",
            "",
            "## CSV Export",
            "",
            "- `export-notes` writes learning notes to a CSV file.",
            "- `export-coding` writes coding progress to a CSV file.",
            "- `export-jobs` writes job applications to a CSV file.",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def build_report(report_title: str, dashboard_text: str) -> str:
    return "\n".join([f"# {report_title}", "", dashboard_text.rstrip(), ""]).strip() + "\n"
