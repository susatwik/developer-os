from __future__ import annotations

import io
import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from developer_os.errors import ExternalServiceError, RateLimitError
from developer_os.services.github import GitHubService
from developer_os.services.leetcode import LeetCodeService


class FakeResponse:
    def __init__(self, payload: dict | list) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_github_service_fetches_profile_and_repositories(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        "https://api.github.com/users/octo": FakeResponse({"public_repos": 7, "followers": 11}),
        "https://api.github.com/users/octo/repos?per_page=5&sort=pushed": FakeResponse(
            [
                {"name": "repo-a", "html_url": "https://example.com/a", "stargazers_count": 2, "pushed_at": "2026-06-01"},
                {"name": "repo-b", "html_url": "https://example.com/b", "stargazers_count": 3, "pushed_at": "2026-06-02"},
            ]
        ),
        "https://api.github.com/graphql": FakeResponse(
            {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "contributionCalendar": {
                                "totalContributions": 40,
                                "weeks": [
                                    {"contributionDays": [{"date": "2026-06-01", "contributionCount": 1}]},
                                    {"contributionDays": [{"date": "2026-06-02", "contributionCount": 2}]},
                                ],
                            }
                        }
                    }
                }
            }
        ),
    }

    def fake_urlopen(request: Request, timeout: int = 20) -> FakeResponse:  # noqa: ARG001
        return responses[request.full_url]

    monkeypatch.setattr("developer_os.services.github.urlopen", fake_urlopen)

    stats = GitHubService("octo", token="token").fetch()

    assert stats.public_repos == 7
    assert stats.stars == 5
    assert stats.followers == 11
    assert stats.contributions_total == 40
    assert stats.recent_repositories[0]["name"] == "repo-a"
    assert stats.contribution_days[-1]["date"] == "2026-06-02"


def test_github_service_raises_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    response = io.BytesIO(b'{"message":"rate limit exceeded"}')
    error = HTTPError(
        "https://api.github.com/users/octo",
        403,
        "Forbidden",
        {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "123"},
        response,
    )
    monkeypatch.setattr("developer_os.services.github.urlopen", lambda request, timeout=20: (_ for _ in ()).throw(error))

    with pytest.raises(RateLimitError):
        GitHubService("octo").fetch()


def test_github_service_raises_when_user_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        "https://api.github.com/users/octo": FakeResponse({"public_repos": 7, "followers": 11}),
        "https://api.github.com/users/octo/repos?per_page=5&sort=pushed": FakeResponse([]),
        "https://api.github.com/graphql": FakeResponse({"data": {"user": None}}),
    }

    def fake_urlopen(request: Request, timeout: int = 20) -> FakeResponse:  # noqa: ARG001
        return responses[request.full_url]

    monkeypatch.setattr("developer_os.services.github.urlopen", fake_urlopen)

    with pytest.raises(ExternalServiceError, match="not found"):
        GitHubService("octo").fetch()


def test_leetcode_service_fetches_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "data": {
            "matchedUser": {
                "submitStatsGlobal": {
                    "acSubmissionNum": [
                        {"difficulty": "All", "count": 50},
                        {"difficulty": "Easy", "count": 20},
                        {"difficulty": "Medium", "count": 20},
                        {"difficulty": "Hard", "count": 10},
                    ]
                }
            },
            "userContestRanking": {"rating": 1999.5},
        }
    }

    monkeypatch.setattr("developer_os.services.leetcode.urlopen", lambda request, timeout=20: FakeResponse(payload))  # noqa: ARG001

    stats = LeetCodeService("learner", session_cookie="sid").fetch()

    assert stats.total_solved == 50
    assert stats.easy_solved == 20
    assert stats.medium_solved == 20
    assert stats.hard_solved == 10
    assert stats.contest_rating == 1999.5


def test_leetcode_service_raises_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    error = HTTPError("https://leetcode.com/graphql", 429, "Too Many Requests", {"Retry-After": "60"}, io.BytesIO(b""))
    monkeypatch.setattr("developer_os.services.leetcode.urlopen", lambda request, timeout=20: (_ for _ in ()).throw(error))

    with pytest.raises(RateLimitError):
        LeetCodeService("learner").fetch()


def test_leetcode_service_raises_when_user_missing() -> None:
    with pytest.raises(ExternalServiceError, match="missing"):
        LeetCodeService("").fetch()
