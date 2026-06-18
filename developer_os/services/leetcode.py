"""LeetCode analytics service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..errors import ExternalServiceError, RateLimitError
from ..snapshots import now_iso

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"


@dataclass(frozen=True)
class LeetCodeStats:
    username: str
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    contest_rating: float | None
    fetched_at: str


class LeetCodeService:
    def __init__(self, username: str, session_cookie: str | None = None, timeout: int = 20) -> None:
        self.username = username.strip()
        self.session_cookie = session_cookie.strip() if session_cookie else None
        self.timeout = timeout

    def fetch(self) -> LeetCodeStats:
        if not self.username:
            raise ExternalServiceError("LeetCode username is missing.")

        payload = {
            "query": """
                query userProfile($username: String!) {
                  matchedUser(username: $username) {
                    submitStatsGlobal {
                      acSubmissionNum {
                        difficulty
                        count
                      }
                    }
                  }
                  userContestRanking(username: $username) {
                    rating
                  }
                }
            """,
            "variables": {"username": self.username},
        }
        data = self._post_json(LEETCODE_GRAPHQL_URL, payload)
        if data.get("errors"):
            raise ExternalServiceError(f"LeetCode API error: {data['errors'][0].get('message', 'Unknown error')}")

        matched_user = (data.get("data") or {}).get("matchedUser") or {}
        submit_stats = (((matched_user.get("submitStatsGlobal") or {}).get("acSubmissionNum")) or [])
        counts = {item.get("difficulty", "").lower(): int(item.get("count", 0)) for item in submit_stats}
        contest_ranking = ((data.get("data") or {}).get("userContestRanking") or {}).get("rating")
        contest_rating = float(contest_ranking) if contest_ranking is not None else None
        if (data.get("data") or {}).get("matchedUser") is None:
            raise ExternalServiceError(f"LeetCode user '{self.username}' was not found or is not public.")

        return LeetCodeStats(
            username=self.username,
            total_solved=counts.get("all", 0),
            easy_solved=counts.get("easy", 0),
            medium_solved=counts.get("medium", 0),
            hard_solved=counts.get("hard", 0),
            contest_rating=contest_rating,
            fetched_at=now_iso(),
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Developer-OS",
            "Origin": "https://leetcode.com",
            "Referer": "https://leetcode.com",
        }
        if self.session_cookie:
            headers["Cookie"] = self.session_cookie
        return headers

    def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, headers=self._headers())
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
                data = json.loads(content) if content else {}
                data["fetched_at"] = data.get("fetched_at") or ""
                return data
        except HTTPError as exc:
            self._raise_http_error(exc)
        except URLError as exc:
            raise ExternalServiceError(f"LeetCode API request failed: {exc.reason}") from exc
        raise ExternalServiceError("LeetCode API request failed unexpectedly.")

    def _raise_http_error(self, exc: HTTPError) -> None:
        body = exc.read().decode("utf-8", errors="replace")
        headers = {key.lower(): value for key, value in exc.headers.items()} if exc.headers else {}
        message = body or exc.reason or "Unknown LeetCode API error"
        if exc.code == 429 or "rate limit" in message.lower():
            retry_after = headers.get("retry-after")
            raise RateLimitError(f"LeetCode rate limit reached. Retry after {retry_after or 'later'}.") from exc
        raise ExternalServiceError(f"LeetCode API error ({exc.code}): {message}") from exc
