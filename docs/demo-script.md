# Demo Script

## 1. Open the Dashboard

```bash
developer-os-web
```

Open `http://localhost:8000/dashboard`.

## 2. Show the Core Metrics

- Total notes
- Total coding problems solved
- Applications sent
- Interviews
- Offers
- GitHub and LeetCode summaries

## 3. Add a Learning Note

```bash
developer-os add-note --subject dbms --topic indexing --summary "Learned clustered and non-clustered indexing"
```

Explain that the CLI writes to the same JSON store the web app reads.

## 4. Add a Coding Entry

```bash
developer-os add-problem --platform leetcode --name "Two Sum" --difficulty easy --topic arrays
```

Refresh the dashboard to show the new entry.

## 5. Add a Job Application

```bash
developer-os add-application --company "Acme" --role "Backend Engineer" --status Applied
```

Show the job tracker section updating.

## 6. Search Data

Use the web search box to find `dbms`, `leetcode`, or `Acme`.

## 7. Show Production Readiness

- Open `/health`
- Open `/version`
- Mention Docker, Compose, Render, Railway, and Fly.io support

## 8. Close With Value

Summarize that Developer OS is a single system for learning logs, coding progress, and job search analytics with automation, dashboards, and deployment support.
