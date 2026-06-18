from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from developer_os import analytics
from developer_os.settings import DeveloperOSSettings


@dataclass
class FakeGithubService:
    username: str
    token: str | None

    def fetch(self) -> SimpleNamespace:
        return SimpleNamespace(
            username=self.username,
            public_repos=5,
            stars=8,
            followers=13,
            contributions_total=21,
            recent_repositories=[{"name": "repo-a", "pushed_at": "2026-06-02"}],
            contribution_days=[{"date": "2026-06-02", "contributions": 4}],
        )


@dataclass
class FakeLeetCodeService:
    username: str
    session_cookie: str | None

    def fetch(self) -> SimpleNamespace:
        return SimpleNamespace(
            username=self.username,
            total_solved=30,
            easy_solved=12,
            medium_solved=14,
            hard_solved=4,
            contest_rating=1750,
        )


def _write_json(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_context_refreshes_and_creates_snapshots(tmp_path: Path, monkeypatch) -> None:
    learning_dir = tmp_path / "learning"
    coding_dir = tmp_path / "coding"
    job_dir = tmp_path / "jobs"
    snapshots_dir = tmp_path / "snapshots"
    _write_json(
        learning_dir / "notes.json",
        '{"notes":[{"date":"2026-06-01","subject":"dbms","topic":"indexing","summary":"Learned indexing"}]}',
    )
    _write_json(
        coding_dir / "problems.json",
        '{"leetcode":[{"date":"2026-06-02","platform":"leetcode","name":"Two Sum","difficulty":"easy","topic":"arrays"}],"gfg":[]}',
    )
    _write_json(
        job_dir / "applications.json",
        '{"applications":[{"application_date":"2026-06-03","company":"Acme","role":"Backend Engineer","status":"Interview"}]}',
    )
    monkeypatch.setattr(analytics, "LEARNING_DIR", learning_dir)
    monkeypatch.setattr(analytics, "CODING_DIR", coding_dir)
    monkeypatch.setattr(analytics, "JOB_DIR", job_dir)
    monkeypatch.setattr(analytics, "GitHubService", FakeGithubService)
    monkeypatch.setattr(analytics, "LeetCodeService", FakeLeetCodeService)

    settings = DeveloperOSSettings(
        github_username="octo",
        github_token="token",
        leetcode_username="learner",
        leetcode_session_cookie="cookie",
        snapshots_dir=snapshots_dir,
        dashboard_path=tmp_path / "README.md",
        config_path=tmp_path / "config.yaml",
    )

    context = analytics.DeveloperOSAnalytics(settings).build_context(refresh=True)

    assert context.learning_stats["total_notes"] == 1
    assert context.coding_stats["total_problems_solved"] == 1
    assert context.job_stats["interviews"] == 1
    assert context.github_stats["public_repos"] == 5
    assert context.leetcode_stats["total_solved"] == 30
    assert context.github_trend == ["- No previous snapshot available yet."]
    assert context.leetcode_trend == ["- No previous snapshot available yet."]
    assert "Repo: repo-a" in "\n".join(context.recent_activity)
    assert (snapshots_dir / "github.json").exists()
    assert (snapshots_dir / "leetcode.json").exists()


def test_build_context_preview_does_not_append_snapshots(tmp_path: Path, monkeypatch) -> None:
    learning_dir = tmp_path / "learning"
    coding_dir = tmp_path / "coding"
    job_dir = tmp_path / "jobs"
    snapshots_dir = tmp_path / "snapshots"
    _write_json(learning_dir / "notes.json", '{"notes":[]}')
    _write_json(coding_dir / "problems.json", '{"leetcode":[],"gfg":[]}')
    _write_json(job_dir / "applications.json", '{"applications":[]}')
    monkeypatch.setattr(analytics, "LEARNING_DIR", learning_dir)
    monkeypatch.setattr(analytics, "CODING_DIR", coding_dir)
    monkeypatch.setattr(analytics, "JOB_DIR", job_dir)
    monkeypatch.setattr(analytics, "GitHubService", FakeGithubService)
    monkeypatch.setattr(analytics, "LeetCodeService", FakeLeetCodeService)

    settings = DeveloperOSSettings(
        github_username="octo",
        github_token="token",
        leetcode_username="learner",
        leetcode_session_cookie="cookie",
        snapshots_dir=snapshots_dir,
        dashboard_path=tmp_path / "README.md",
        config_path=tmp_path / "config.yaml",
    )
    analytics_obj = analytics.DeveloperOSAnalytics(settings)

    first = analytics_obj.build_context(refresh=True)
    github_store = snapshots_dir / "github.json"
    before = github_store.read_text(encoding="utf-8")
    second = analytics_obj.build_context(refresh=False)
    after = github_store.read_text(encoding="utf-8")

    assert before == after
    assert first.github_stats == second.github_stats
    assert second.github_error is None


def test_build_context_handles_missing_usernames(tmp_path: Path, monkeypatch) -> None:
    learning_dir = tmp_path / "learning"
    coding_dir = tmp_path / "coding"
    job_dir = tmp_path / "jobs"
    snapshots_dir = tmp_path / "snapshots"
    _write_json(learning_dir / "notes.json", '{"notes":[]}')
    _write_json(coding_dir / "problems.json", '{"leetcode":[],"gfg":[]}')
    _write_json(job_dir / "applications.json", '{"applications":[]}')
    monkeypatch.setattr(analytics, "LEARNING_DIR", learning_dir)
    monkeypatch.setattr(analytics, "CODING_DIR", coding_dir)
    monkeypatch.setattr(analytics, "JOB_DIR", job_dir)

    settings = DeveloperOSSettings(
        github_username=None,
        github_token=None,
        leetcode_username=None,
        leetcode_session_cookie=None,
        snapshots_dir=snapshots_dir,
        dashboard_path=tmp_path / "README.md",
        config_path=tmp_path / "config.yaml",
    )

    context = analytics.DeveloperOSAnalytics(settings).build_context(refresh=True)

    assert context.github_error is not None
    assert context.leetcode_error is not None
    assert context.github_stats["public_repos"] == 0
    assert context.leetcode_stats["total_solved"] == 0
