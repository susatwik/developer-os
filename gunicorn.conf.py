"""Gunicorn configuration for Developer OS."""

from __future__ import annotations

import multiprocessing
import os

from developer_os.production import load_production_settings

runtime = load_production_settings()

bind = f"{runtime.host}:{runtime.port}"
workers = int(os.getenv("WEB_CONCURRENCY", str(max(2, multiprocessing.cpu_count() // 2))))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = runtime.timeout
keepalive = runtime.keepalive
loglevel = runtime.log_level
accesslog = os.getenv("DEVOS_ACCESS_LOG_FILE", "-")
errorlog = os.getenv("DEVOS_ERROR_LOG_FILE", "-")
capture_output = True
preload_app = False
