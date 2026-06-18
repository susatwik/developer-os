"""Production runtime settings for Developer OS."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionSettings:
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 2
    log_level: str = "info"
    access_log: bool = True
    error_log: str | None = None
    timeout: int = 60
    keepalive: int = 5


def _as_int(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    return int(value)


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().casefold() not in {"0", "false", "no", "off"}


def load_production_settings(env: os._Environ[str] | None = None) -> ProductionSettings:
    env = env or os.environ
    return ProductionSettings(
        host=env.get("DEVOS_HOST", "0.0.0.0"),
        port=_as_int(env.get("DEVOS_PORT"), 8000),
        workers=_as_int(env.get("WEB_CONCURRENCY"), 2),
        log_level=env.get("DEVOS_LOG_LEVEL", "info"),
        access_log=_as_bool(env.get("DEVOS_ACCESS_LOG"), True),
        error_log=env.get("DEVOS_ERROR_LOG"),
        timeout=_as_int(env.get("DEVOS_TIMEOUT"), 60),
        keepalive=_as_int(env.get("DEVOS_KEEPALIVE"), 5),
    )
