"""GitHub analytics service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..errors import ExternalServiceError, RateLimitError
from ..snapshots import now_iso

GITHUB_API_VERSION = "2026-03-10"
GITHUB_REST_BASE = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


@dataclass(frozen=True)
class GitHubStats:
    username: str
    public_repos: int
    stars: int
    followers: int
    contributions_total: int
    recent_repositories: list[dict[str, Any]]
    contribution_days: list[dict[str, Any]]
    fetched_at: str


class GitHubService:
    def __init__(self, username: str, token: str | None = None, timeout: int = 20) -> None:
        self.username = username.strip()
        self.token = token.strip() if token else None
        self.timeout = timeout

    def fetch(self) -> GitHubStats:
        if not self.username:
            raise ExternalServiceError("GitHub username is missing.")

        profile = self._get_json(f"{GITHUB_REST_BASE}/users/{self.username}")
        repos = self._get_json(f"{GITHUB_REST_BASE}/users/{self.username}/repos?per_page=5&sort=pushed")
        graphql = self._post_graphql(
            {
                "query": """
                    query($login: String!) {
                      user(login: $login) {
                        contributionsCollection {
                          contributionCalendar {
                            totalContributions
                            weeks {
                              contributionDays {
                                date
                                contributionCount
                              }
                            }
                          }
                        }
                      }
                    }
                """,
                "variables": {"login": self.username},
            }
        )
        if graphql.get("errors"):
            raise ExternalServiceError(f"GitHub GraphQL error: {graphql['errors'][0].get('message', 'Unknown error')}")

        recent_repositories = [
            {
                "name": repo.get("name", ""),
                "url": repo.get("html_url", ""),
                "stars": repo.get("stargazers_count", 0),
                "pushed_at": repo.get("pushed_at", ""),
            }
            for repo in repos[:5]
        ]

        contribution_calendar = (
            (((graphql.get("data") or {}).get("user") or {}).get("contributionsCollection") or {}).get("contributionCalendar")
            or {}
        )
        if (graphql.get("data") or {}).get("user") is None:
            raise ExternalServiceError(f"GitHub user '{self.username}' was not found or is not public.")
        contribution_days: list[dict[str, Any]] = []
        for week in contribution_calendar.get("weeks", []):
            contribution_days.extend(week.get("contributionDays", []))

        return GitHubStats(
            username=self.username,
            public_repos=int(profile.get("public_repos", 0)),
            stars=sum(int(repo.get("stargazers_count", 0)) for repo in repos),
            followers=int(profile.get("followers", 0)),
            contributions_total=int(contribution_calendar.get("totalContributions", 0)),
            recent_repositories=recent_repositories,
            contribution_days=contribution_days[-14:],
            fetched_at=now_iso(),
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "Developer-OS",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get_json(self, url: str) -> dict[str, Any] | list[dict[str, Any]]:
        request = Request(url, headers=self._headers())
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload) if payload else {}
        except HTTPError as exc:
            self._raise_http_error(exc)
        except URLError as exc:
            raise ExternalServiceError(f"GitHub API request failed: {exc.reason}") from exc
        raise ExternalServiceError("GitHub API request failed unexpectedly.")

    def _post_graphql(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(GITHUB_GRAPHQL_URL, data=body, headers={**self._headers(), "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
                data = json.loads(content) if content else {}
                data["fetched_at"] = data.get("fetched_at") or ""
                return data
        except HTTPError as exc:
            self._raise_http_error(exc)
        except URLError as exc:
            raise ExternalServiceError(f"GitHub GraphQL request failed: {exc.reason}") from exc
        raise ExternalServiceError("GitHub GraphQL request failed unexpectedly.")

    def _raise_http_error(self, exc: HTTPError) -> None:
        body = exc.read().decode("utf-8", errors="replace")
        headers = {key.lower(): value for key, value in exc.headers.items()} if exc.headers else {}
        message = body or exc.reason or "Unknown GitHub API error"
        if exc.code == 403 and (
            "rate limit" in message.lower() or headers.get("x-ratelimit-remaining") == "0"
        ):
            reset = headers.get("x-ratelimit-reset")
            raise RateLimitError(f"GitHub rate limit reached. Reset at {reset or 'unknown time'}.") from exc
        raise ExternalServiceError(f"GitHub API error ({exc.code}): {message}") from exc
