# Project Walkthrough

## Overview

Developer OS is a Python-based developer analytics platform that combines manual tracking, live API integrations, automated reports, a web dashboard, and deployment-ready packaging.

## Architecture

1. CLI commands write learning notes, coding problems, and job applications into JSON-backed stores.
2. The analytics layer builds dashboard data, trends, and activity summaries.
3. The FastAPI web app renders a browser dashboard and search pages from the same stores.
4. GitHub Actions regenerate scheduled reports without touching the checked-in README.
5. Docker and Gunicorn support public deployment.

## Main Entry Points

- `developer-os`
- `developer-os-web`
- `python3 scripts/update.py generate-dashboard`

## Data Flow

1. A user adds a note, coding entry, or application.
2. The store writes the data to `data/`.
3. The dashboard generator reads the stores and creates the dashboard report.
4. The web app reads the same data for the live UI.

## Key Files

- `developer_os/cli.py`
- `developer_os/webapp.py`
- `developer_os/analytics.py`
- `developer_os/dashboard.py`
- `developer_os/services/github.py`
- `developer_os/services/leetcode.py`
- `docs/deployment.md`

## What To Highlight In A Review

- Simple architecture
- Shared storage between CLI and web app
- Historical snapshots for trend reporting
- Deployment readiness
- Test coverage and CI validation

## Suggested Story

“Developer OS started as a personal tracker and became a production-ready analytics platform with a CLI, web dashboard, live coding and GitHub integrations, automated reporting, and deployment support.”
