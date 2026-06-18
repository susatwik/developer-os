from __future__ import annotations

from pathlib import Path

from developer_os.settings import load_settings, load_simple_yaml
from developer_os.snapshots import SnapshotStore, now_iso


def test_load_simple_yaml_and_settings_override(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "github:\n"
        "  username: config-user\n"
        "  token: config-token\n"
        "leetcode:\n"
        "  username: config-leet\n"
        "  session_cookie: config-cookie\n"
        "storage:\n"
        "  snapshots_dir: data/snapshots\n"
        "  dashboard_path: README.md\n",
        encoding="utf-8",
    )

    parsed = load_simple_yaml(config_path)
    assert parsed["github"]["username"] == "config-user"
    assert parsed["storage"]["snapshots_dir"] == "data/snapshots"

    monkeypatch.setenv("DEVOS_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DEVOS_GITHUB_USERNAME", "env-user")
    monkeypatch.setenv("DEVOS_DASHBOARD_PATH", str(tmp_path / "custom-readme.md"))
    settings = load_settings()

    assert settings.github_username == "env-user"
    assert settings.github_token == "config-token"
    assert settings.leetcode_username == "config-leet"
    assert settings.dashboard_path == tmp_path / "custom-readme.md"


def test_snapshot_store_tracks_history(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path / "snapshots.json")
    first = {"fetched_at": now_iso(), "status": "ok", "data": {"value": 1}}
    second = {"fetched_at": now_iso(), "status": "error", "error": "boom", "data": {"value": 2}}
    third = {"fetched_at": now_iso(), "status": "ok", "data": {"value": 3}}

    store.append(first)
    store.append(second)
    store.append(third)

    assert store.history() == [first, second, third]
    assert store.successful() == [first, third]
    assert store.latest_successful() == third
    assert store.previous_successful() == first

