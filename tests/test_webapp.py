from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from developer_os.settings import DeveloperOSSettings
from developer_os.webapp import create_app


def _write_json(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _client(tmp_path: Path) -> TestClient:
    learning_path = tmp_path / "data" / "learning" / "notes.json"
    coding_path = tmp_path / "data" / "coding" / "problems.json"
    jobs_path = tmp_path / "data" / "jobs" / "applications.json"
    snapshots_dir = tmp_path / "data" / "snapshots"
    _write_json(learning_path, '{"notes":[{"date":"2026-06-01","subject":"dbms","topic":"indexing","summary":"Clustered indexes"}]}')
    _write_json(coding_path, '{"leetcode":[{"date":"2026-06-02","platform":"leetcode","name":"Two Sum","difficulty":"easy","topic":"arrays"}],"gfg":[]}')
    _write_json(jobs_path, '{"applications":[{"application_date":"2026-06-03","company":"Acme","role":"Backend Engineer","status":"Applied"}]}')

    settings = DeveloperOSSettings(
        github_username="octo",
        github_token=None,
        leetcode_username="learner",
        leetcode_session_cookie=None,
        snapshots_dir=snapshots_dir,
        dashboard_path=tmp_path / "README.md",
        config_path=tmp_path / "config.yaml",
    )
    app = create_app(settings=settings, learning_path=learning_path, coding_path=coding_path, jobs_path=jobs_path)
    return TestClient(app)


def test_dashboard_and_stats_pages_render(tmp_path: Path) -> None:
    client = _client(tmp_path)

    dashboard = client.get("/dashboard")
    stats = client.get("/stats")

    assert dashboard.status_code == 200
    assert "Developer OS" in dashboard.text
    assert "Total Notes" in dashboard.text
    assert "Refresh live data" in dashboard.text
    assert stats.status_code == 200
    assert "Statistics" in stats.text
    assert "GitHub Statistics" in stats.text


def test_web_forms_add_entries_and_search(tmp_path: Path) -> None:
    client = _client(tmp_path)

    note_response = client.post(
        "/notes",
        data={"subject": "systems", "topic": "caching", "summary": "LRU cache", "note_date": "2026-06-04"},
        follow_redirects=True,
    )
    coding_response = client.post(
        "/coding",
        data={"platform": "leetcode", "name": "LRU Cache", "difficulty": "hard", "topic": "design", "problem_date": "2026-06-05"},
        follow_redirects=True,
    )
    job_response = client.post(
        "/applications",
        data={"company": "Beta", "role": "SRE", "status": "Interview", "application_date": "2026-06-06"},
        follow_redirects=True,
    )

    assert note_response.status_code == 200
    assert coding_response.status_code == 200
    assert job_response.status_code == 200
    assert "Total Notes" in job_response.text
    assert "2" in job_response.text

    search = client.get("/search", params={"q": "cache"})
    assert search.status_code == 200
    assert "LRU Cache" in search.text
    assert "LRU cache" in search.text


def test_refresh_route_renders_dashboard(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post("/refresh")

    assert response.status_code == 200
    assert "Live integrations refreshed." in response.text


def test_health_and_version_endpoints(tmp_path: Path) -> None:
    client = _client(tmp_path)

    health = client.get("/health")
    version = client.get("/version")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["service"] == "developer-os"
    assert isinstance(health.json()["uptime_seconds"], int)
    assert version.status_code == 200
    assert "version" in version.json()
