# Release Checklist

Use this checklist before tagging `v1.0.0`.

## Code and Tests

- [x] Run `ruff check developer_os scripts tests`
- [x] Run `pytest`
- [x] Run `python -m build --no-isolation`
- [x] Confirm test coverage is above 80%

## Documentation

- [x] README badges point to the correct repository
- [x] Installation instructions are current
- [x] Deployment instructions cover Docker, Render, Railway, and Fly.io
- [x] Contributing, code of conduct, security, and changelog files exist
- [x] Demo and interview docs exist

## Packaging and Versioning

- [x] `VERSION` file is set to `1.0.0`
- [x] `pyproject.toml` version matches `VERSION`
- [x] `developer_os.version.get_version()` falls back to `1.0.0`
- [x] Package metadata uses the public repository URL

## Deployment

- [x] Dockerfile builds successfully
- [x] Docker Compose starts the app
- [x] `/health` endpoint is available
- [x] `/version` endpoint is available

## GitHub Hygiene

- [x] Issue templates exist
- [x] Pull request template exists
- [x] GitHub Actions workflows are present
- [x] Repository metadata is complete

## Final Sign-Off

- [x] Repository is ready for public release
