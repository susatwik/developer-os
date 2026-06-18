# Interview Talking Points

## Problem Solved

Developer OS helps a developer keep learning notes, coding progress, job applications, and live GitHub / LeetCode stats in one place.

## Why It Matters

- Reduces context switching
- Makes progress visible over time
- Automates recurring updates
- Keeps personal career tracking organized

## Technical Highlights

- Python CLI with clean tracker modules
- FastAPI + Jinja2 web dashboard
- JSON-backed storage with historical snapshots
- GitHub and LeetCode API integration
- Scheduled GitHub Actions automation
- Docker and production deployment support

## Design Decisions

- Kept the architecture simple and maintainable.
- Reused the same storage across CLI, web, and automation.
- Chose historical snapshots for trend summaries without adding a database dependency.
- Used environment variables and `config.yaml` for reproducible configuration.

## Tradeoffs

- JSON storage is simple, but not ideal for large-scale multi-user usage.
- The first web version is intentionally server-rendered rather than SPA-based.
- GitHub and LeetCode live data depend on upstream rate limits and availability.

## Questions To Expect

- How is data persisted?
- How do CLI and web stay in sync?
- How do you handle API failures?
- How do you deploy it?
- How would you scale it later?

## Strong Close

“The project shows that I can take a personal productivity idea, turn it into a maintainable full-stack tool, and ship it with automation, tests, and production deployment in mind.”
