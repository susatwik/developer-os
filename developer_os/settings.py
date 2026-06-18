"""Configuration loading for Developer OS."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DATA_DIR, ROOT

DEFAULT_CONFIG_PATH = ROOT / "config.yaml"
DEFAULT_SNAPSHOTS_DIR = DATA_DIR / "snapshots"
DEFAULT_DASHBOARD_PATH = ROOT / "README.md"


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"Invalid config line: {raw_line}")

        indent = len(line) - len(line.lstrip(" "))
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if value == "":
            node: dict[str, Any] = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            parent[key] = _strip_quotes(value)

    return root


def _get_path(value: Any, default: Path) -> Path:
    if not value:
        return default
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _get_text(mapping: dict[str, Any], *keys: str) -> str | None:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if current is None:
        return None
    text = str(current).strip()
    return text or None


@dataclass(frozen=True)
class DeveloperOSSettings:
    github_username: str | None
    github_token: str | None
    leetcode_username: str | None
    leetcode_session_cookie: str | None
    snapshots_dir: Path
    dashboard_path: Path
    config_path: Path


def load_settings(env: os._Environ[str] | None = None, config_path: Path | None = None) -> DeveloperOSSettings:
    env = env or os.environ
    resolved_config_path = Path(env.get("DEVOS_CONFIG_PATH", str(config_path or DEFAULT_CONFIG_PATH)))
    config = load_simple_yaml(resolved_config_path)

    github_username = env.get("DEVOS_GITHUB_USERNAME") or _get_text(config, "github", "username")
    github_token = env.get("DEVOS_GITHUB_TOKEN") or _get_text(config, "github", "token")
    leetcode_username = env.get("DEVOS_LEETCODE_USERNAME") or _get_text(config, "leetcode", "username")
    leetcode_session_cookie = env.get("DEVOS_LEETCODE_SESSION_COOKIE") or _get_text(config, "leetcode", "session_cookie")

    snapshots_dir = _get_path(
        env.get("DEVOS_SNAPSHOTS_DIR") or _get_text(config, "storage", "snapshots_dir"),
        DEFAULT_SNAPSHOTS_DIR,
    )
    dashboard_path = _get_path(
        env.get("DEVOS_DASHBOARD_PATH") or _get_text(config, "storage", "dashboard_path"),
        DEFAULT_DASHBOARD_PATH,
    )

    return DeveloperOSSettings(
        github_username=github_username,
        github_token=github_token,
        leetcode_username=leetcode_username,
        leetcode_session_cookie=leetcode_session_cookie,
        snapshots_dir=snapshots_dir,
        dashboard_path=dashboard_path,
        config_path=resolved_config_path,
    )
