# Contributing to Developer OS

Thanks for helping improve Developer OS.

## Getting Started

1. Fork or clone the repository.
2. Create a virtual environment.
3. Install the project with development dependencies:

```bash
python3 -m pip install -e '.[dev,web]'
```

4. Run the test suite before opening a pull request:

```bash
python3 -m pytest
```

## Development Workflow

- Keep changes small and focused.
- Add or update tests for behavior changes.
- Run `ruff check developer_os scripts tests` before committing.
- Regenerate the README when dashboard output changes:

```bash
python3 scripts/update.py generate-dashboard
```

## Pull Request Expectations

- Describe the problem and the solution.
- Link related issues if available.
- Mention any migration or deployment impact.
- Include screenshots for web UI changes when helpful.

## Local Validation

Recommended checks:

```bash
python3 -m ruff check developer_os scripts tests
python3 -m pytest
python3 -m build --no-isolation
```
