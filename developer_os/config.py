"""Central configuration for Developer OS."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LEARNING_DIR = DATA_DIR / "learning"
CODING_DIR = DATA_DIR / "coding"
JOB_DIR = DATA_DIR / "jobs"
REPORT_DIR = DATA_DIR / "reports"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
CONFIG_PATH = ROOT / "config.yaml"
README_PATH = ROOT / "README.md"

TRACKER_DIRS = (LEARNING_DIR, CODING_DIR, JOB_DIR, REPORT_DIR)
