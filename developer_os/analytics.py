"""Analytics orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .coding import build_stats as build_coding_stats
from .coding import coding_store
from .config import CODING_DIR, JOB_DIR, LEARNING_DIR
from .errors import DeveloperOSError
from .jobs import build_stats as build_job_stats
from .jobs import jobs_store
from .learning import build_stats as build_learning_stats
from .learning import learning_store
from .services.github import GitHubService
from .services.leetcode import LeetCodeService
from .settings import DeveloperOSSettings
from .snapshots import SnapshotStore, now_iso


@dataclass(frozen=True)
class IntegrationResult:
    snapshot: dict[str, Any]
    latest: dict[str, Any] | None
    previous: dict[str, Any] | None
    error: str | None


@dataclass(frozen=True)
class AnalyticsContext:
    learning_stats: dict[str, Any]
    coding_stats: dict[str, Any]
    job_stats: dict[str, Any]
    github_stats: dict[str, Any]
    leetcode_stats: dict[str, Any]
    github_trend: list[str]
    leetcode_trend: list[str]
    recent_activity: list[str]
    github_error: str | None = None
    leetcode_error: str | None = None


class DeveloperOSAnalytics:
    def __init__(self, settings: DeveloperOSSettings) -> None:
        self.settings = settings
        self.learning_path = LEARNING_DIR / "notes.json"
        self.coding_path = CODING_DIR / "problems.json"
        self.job_path = JOB_DIR / "applications.json"
        self.github_store = SnapshotStore(self.settings.snapshots_dir / "github.json")
        self.leetcode_store = SnapshotStore(self.settings.snapshots_dir / "leetcode.json")

    def build_context(self, refresh: bool = True) -> AnalyticsContext:
        if refresh:
            github_result = self._refresh_github()
            leetcode_result = self._refresh_leetcode()
        else:
            github_result = self._preview_github()
            leetcode_result = self._preview_leetcode()
        learning_data = learning_store(self.learning_path).read()
        coding_data = coding_store(self.coding_path).read()
        job_data = jobs_store(self.job_path).read()

        learning_stats = build_learning_stats(learning_data)
        coding_stats = build_coding_stats(coding_data)
        job_stats = build_job_stats(job_data)
        recent_activity = self._collect_recent_activity(learning_stats, coding_stats, job_stats, github_result, leetcode_result)

        return AnalyticsContext(
            learning_stats=learning_stats,
            coding_stats=coding_stats,
            job_stats=job_stats,
            github_stats=self._latest_successful_data(github_result),
            leetcode_stats=self._latest_successful_data(leetcode_result),
            github_trend=self._trend_lines(github_result, ("public_repos", "stars", "followers", "contributions_total")),
            leetcode_trend=self._trend_lines(leetcode_result, ("total_solved", "easy_solved", "medium_solved", "hard_solved", "contest_rating")),
            recent_activity=recent_activity,
            github_error=github_result.error,
            leetcode_error=leetcode_result.error,
        )

    def _preview_github(self) -> IntegrationResult:
        empty_snapshot = {
            "username": self.settings.github_username or "",
            "public_repos": 0,
            "stars": 0,
            "followers": 0,
            "contributions_total": 0,
            "recent_repositories": [],
            "contribution_days": [],
        }
        return self._preview_snapshot(
            self.github_store,
            "GitHub",
            self.settings.github_username,
            empty_snapshot,
        )

    def _preview_leetcode(self) -> IntegrationResult:
        empty_snapshot = {
            "username": self.settings.leetcode_username or "",
            "total_solved": 0,
            "easy_solved": 0,
            "medium_solved": 0,
            "hard_solved": 0,
            "contest_rating": None,
        }
        return self._preview_snapshot(
            self.leetcode_store,
            "LeetCode",
            self.settings.leetcode_username,
            empty_snapshot,
        )

    def _refresh_github(self) -> IntegrationResult:
        if not self.settings.github_username:
            return self._missing_username_result(
                self.github_store,
                "GitHub",
                {"username": "", "public_repos": 0, "stars": 0, "followers": 0, "contributions_total": 0, "recent_repositories": [], "contribution_days": []},
            )
        service = GitHubService(self.settings.github_username, self.settings.github_token)
        return self._capture_snapshot(
            self.github_store,
            lambda: service.fetch().__dict__,
            empty_snapshot={"username": self.settings.github_username or "", "public_repos": 0, "stars": 0, "followers": 0, "contributions_total": 0, "recent_repositories": [], "contribution_days": []},
        )

    def _refresh_leetcode(self) -> IntegrationResult:
        if not self.settings.leetcode_username:
            return self._missing_username_result(
                self.leetcode_store,
                "LeetCode",
                {"username": "", "total_solved": 0, "easy_solved": 0, "medium_solved": 0, "hard_solved": 0, "contest_rating": None},
            )
        service = LeetCodeService(self.settings.leetcode_username, self.settings.leetcode_session_cookie)
        return self._capture_snapshot(
            self.leetcode_store,
            lambda: service.fetch().__dict__,
            empty_snapshot={"username": self.settings.leetcode_username or "", "total_solved": 0, "easy_solved": 0, "medium_solved": 0, "hard_solved": 0, "contest_rating": None},
        )

    def _missing_username_result(
        self,
        store: SnapshotStore,
        service_name: str,
        empty_snapshot: dict[str, Any],
    ) -> IntegrationResult:
        timestamp = now_iso()
        message = f"Missing {service_name} username. Set it in config.yaml or the matching DEVOS_* environment variable."
        snapshot = {"fetched_at": timestamp, "status": "error", "error": message, "data": empty_snapshot}
        store.append(snapshot)
        return IntegrationResult(snapshot=snapshot, latest=store.latest_successful(), previous=store.previous_successful(), error=message)

    def _capture_snapshot(
        self,
        store: SnapshotStore,
        fetcher,
        empty_snapshot: dict[str, Any],
    ) -> IntegrationResult:
        timestamp = now_iso()
        try:
            data = dict(fetcher())
            snapshot = {"fetched_at": timestamp, "status": "ok", "data": data}
            store.append(snapshot)
            return IntegrationResult(snapshot=snapshot, latest=store.latest_successful(), previous=store.previous_successful(), error=None)
        except DeveloperOSError as exc:
            snapshot = {"fetched_at": timestamp, "status": "error", "error": str(exc), "data": empty_snapshot}
            store.append(snapshot)
            return IntegrationResult(snapshot=snapshot, latest=store.latest_successful(), previous=store.previous_successful(), error=str(exc))

    def _preview_snapshot(
        self,
        store: SnapshotStore,
        service_name: str,
        username: str | None,
        empty_snapshot: dict[str, Any],
    ) -> IntegrationResult:
        latest = store.latest_successful()
        previous = store.previous_successful()
        if latest:
            snapshot = latest
            error = None
        elif username:
            snapshot = {"fetched_at": now_iso(), "status": "ok", "data": empty_snapshot}
            error = None
        else:
            error = f"Missing {service_name} username. Set it in config.yaml or the matching DEVOS_* environment variable."
            snapshot = {"fetched_at": now_iso(), "status": "error", "error": error, "data": empty_snapshot}
        return IntegrationResult(snapshot=snapshot, latest=latest, previous=previous, error=error)

    def _latest_successful_data(self, result: IntegrationResult) -> dict[str, Any]:
        if result.latest:
            return dict(result.latest.get("data") or {})
        return dict(result.snapshot.get("data") or {})

    def _trend_lines(self, result: IntegrationResult, keys: tuple[str, ...]) -> list[str]:
        latest = self._latest_successful_data(result)
        previous = dict((result.previous or {}).get("data") or {})
        if not latest:
            return ["- No successful snapshots yet."]
        if not previous:
            return ["- No previous snapshot available yet."]
        lines: list[str] = []
        for key in keys:
            current_value = latest.get(key)
            previous_value = previous.get(key)
            if isinstance(current_value, (int, float)) and isinstance(previous_value, (int, float)):
                delta = current_value - previous_value
                sign = "+" if delta >= 0 else ""
                lines.append(f"- {key.replace('_', ' ').title()}: {current_value} ({sign}{delta} vs previous)")
        return lines or ["- No comparable trend data yet."]

    def _collect_recent_activity(
        self,
        learning_stats: dict[str, Any],
        coding_stats: dict[str, Any],
        job_stats: dict[str, Any],
        github_result: IntegrationResult,
        leetcode_result: IntegrationResult,
    ) -> list[str]:
        activity: list[str] = []

        for note in learning_stats.get("recent", []):
            activity.append(
                f"Note: {note.get('date', '')} | {note.get('subject', '')} / {note.get('topic', '')} - {note.get('summary', '')}"
            )
        for problem in coding_stats.get("recent", []):
            activity.append(
                f"Problem: {problem.get('date', '')} | {problem.get('platform', '')} / {problem.get('topic', '')} - {problem.get('name', '')} ({problem.get('difficulty', '')})"
            )
        for application in job_stats.get("recent", []):
            activity.append(
                f"Application: {application.get('application_date', '')} | {application.get('company', '')} - {application.get('role', '')} [{application.get('status', '')}]"
            )
        github_data = self._latest_successful_data(github_result)
        for repo in github_data.get("recent_repositories", [])[:3]:
            activity.append(f"Repo: {repo.get('name', '')} - pushed {repo.get('pushed_at', '')}")
        leetcode_data = self._latest_successful_data(leetcode_result)
        if leetcode_data.get("total_solved"):
            activity.append(f"LeetCode: {leetcode_data.get('total_solved')} total solved")
        return activity[:10]
