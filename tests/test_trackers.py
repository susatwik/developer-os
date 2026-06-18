from __future__ import annotations

from pathlib import Path

import pytest

from developer_os.coding import add_problem, coding_store, export_problems
from developer_os.coding import build_stats as build_coding_stats
from developer_os.jobs import (
    add_application,
    export_applications,
    jobs_store,
    normalize_status,
)
from developer_os.jobs import build_stats as build_job_stats
from developer_os.learning import add_note, export_notes, learning_store
from developer_os.learning import build_stats as build_learning_stats


def test_learning_tracker_adds_notes_and_builds_stats(tmp_path: Path) -> None:
    store = learning_store(tmp_path / "notes.json")

    add_note(store, subject="dbms", topic="indexing", summary="Clustered and non-clustered", note_date="2026-06-01")
    add_note(store, subject="systems", topic="caching", summary="LRU and write-through", note_date="2026-06-03")
    add_note(store, subject="dbms", topic="transactions", summary="ACID refresh", note_date="2026-06-02")

    data = store.read()
    stats = build_learning_stats(data)

    assert stats["total_notes"] == 3
    assert stats["subjects"] == {"dbms": 2, "systems": 1}
    assert [item["date"] for item in stats["recent"]] == ["2026-06-03", "2026-06-02", "2026-06-01"]
    assert export_notes(data) == [
        {"subject": "dbms", "topic": "indexing", "summary": "Clustered and non-clustered", "date": "2026-06-01"},
        {"subject": "systems", "topic": "caching", "summary": "LRU and write-through", "date": "2026-06-03"},
        {"subject": "dbms", "topic": "transactions", "summary": "ACID refresh", "date": "2026-06-02"},
    ]


def test_coding_tracker_counts_platforms_and_exports(tmp_path: Path) -> None:
    store = coding_store(tmp_path / "problems.json")

    add_problem(store, platform="leetcode", name="Two Sum", difficulty="easy", topic="arrays", problem_date="2026-06-01")
    add_problem(store, platform="gfg", name="Binary Search", difficulty="medium", topic="searching", problem_date="2026-06-03")
    add_problem(store, platform="leetcode", name="LRU Cache", difficulty="hard", topic="design", problem_date="2026-06-02")

    data = store.read()
    stats = build_coding_stats(data)

    assert stats["leetcode_total"] == 2
    assert stats["gfg_total"] == 1
    assert stats["total_problems_solved"] == 3
    assert stats["difficulty_counts"] == {"easy": 1, "hard": 1, "medium": 1}
    assert [item["date"] for item in stats["recent"]] == ["2026-06-03", "2026-06-02", "2026-06-01"]
    assert export_problems(data) == [
        {"platform": "leetcode", "name": "Two Sum", "difficulty": "easy", "topic": "arrays", "date": "2026-06-01"},
        {"platform": "leetcode", "name": "LRU Cache", "difficulty": "hard", "topic": "design", "date": "2026-06-02"},
        {"platform": "gfg", "name": "Binary Search", "difficulty": "medium", "topic": "searching", "date": "2026-06-03"},
    ]


def test_job_tracker_validates_status_and_exports(tmp_path: Path) -> None:
    store = jobs_store(tmp_path / "applications.json")

    add_application(store, company="Acme", role="Backend Engineer", status="applied", application_date="2026-06-01")
    add_application(store, company="Beta", role="SRE", status="Interview", application_date="2026-06-03")
    add_application(store, company="Gamma", role="Platform", status="Offer", application_date="2026-06-02")

    data = store.read()
    stats = build_job_stats(data)

    assert normalize_status("oa") == "OA"
    assert stats["total_applications"] == 3
    assert stats["interviews"] == 1
    assert stats["offers"] == 1
    assert stats["status_counts"] == {"Applied": 1, "Interview": 1, "Offer": 1}
    assert [item["application_date"] for item in stats["recent"]] == ["2026-06-03", "2026-06-02", "2026-06-01"]
    assert export_applications(data) == [
        {"company": "Acme", "role": "Backend Engineer", "status": "Applied", "application_date": "2026-06-01"},
        {"company": "Beta", "role": "SRE", "status": "Interview", "application_date": "2026-06-03"},
        {"company": "Gamma", "role": "Platform", "status": "Offer", "application_date": "2026-06-02"},
    ]


def test_job_tracker_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        normalize_status("pending")
