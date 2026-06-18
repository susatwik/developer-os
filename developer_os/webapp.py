"""FastAPI web interface for Developer OS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .analytics import DeveloperOSAnalytics
from .coding import add_problem, coding_store
from .config import CODING_DIR, JOB_DIR, LEARNING_DIR
from .dates import validate_iso_date
from .jobs import add_application, jobs_store, normalize_status
from .learning import add_note, learning_store
from .production import load_production_settings
from .settings import DeveloperOSSettings, load_settings
from .version import get_version

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"

DEFAULT_LEARNING_PATH = LEARNING_DIR / "notes.json"
DEFAULT_CODING_PATH = CODING_DIR / "problems.json"
DEFAULT_JOBS_PATH = JOB_DIR / "applications.json"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@dataclass(frozen=True)
class SearchResults:
    query: str
    notes: list[dict[str, Any]]
    problems: list[dict[str, Any]]
    applications: list[dict[str, Any]]

    @property
    def total(self) -> int:
        return len(self.notes) + len(self.problems) + len(self.applications)


def _store_paths(
    learning_path: Path | None = None,
    coding_path: Path | None = None,
    jobs_path: Path | None = None,
) -> tuple[Path, Path, Path]:
    return (
        learning_path or DEFAULT_LEARNING_PATH,
        coding_path or DEFAULT_CODING_PATH,
        jobs_path or DEFAULT_JOBS_PATH,
    )


def _context(settings: DeveloperOSSettings, refresh: bool = False) -> Any:
    return DeveloperOSAnalytics(settings).build_context(refresh=refresh)


def _search_text(*values: object) -> str:
    return " ".join(str(value or "") for value in values).casefold()


def _match_entries(query: str, learning_path: Path, coding_path: Path, jobs_path: Path) -> SearchResults:
    term = query.strip().casefold()
    if not term:
        return SearchResults(query=query, notes=[], problems=[], applications=[])

    learning_data = learning_store(learning_path).read()
    coding_data = coding_store(coding_path).read()
    job_data = jobs_store(jobs_path).read()

    notes = [
        note
        for note in learning_data.get("notes", [])
        if term in _search_text(note.get("subject"), note.get("topic"), note.get("summary"), note.get("date"))
    ]
    problems = [
        problem
        for bucket in ("leetcode", "gfg")
        for problem in coding_data.get(bucket, [])
        if term in _search_text(
            problem.get("platform"),
            problem.get("name"),
            problem.get("difficulty"),
            problem.get("topic"),
            problem.get("date"),
        )
    ]
    applications = [
        application
        for application in job_data.get("applications", [])
        if term in _search_text(
            application.get("company"),
            application.get("role"),
            application.get("status"),
            application.get("application_date"),
        )
    ]
    return SearchResults(query=query, notes=notes, problems=problems, applications=applications)


def create_app(
    settings: DeveloperOSSettings | None = None,
    learning_path: Path | None = None,
    coding_path: Path | None = None,
    jobs_path: Path | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    learning_file, coding_file, jobs_file = _store_paths(learning_path, coding_path, jobs_path)
    app = FastAPI(title="Developer OS", description="Lightweight web dashboard for developer analytics.")
    app.state.started_at = datetime.now(timezone.utc)
    app.state.settings = settings
    app.state.learning_path = learning_file
    app.state.coding_path = coding_file
    app.state.jobs_path = jobs_file

    def render(template_name: str, request: Request, **context: Any) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            template_name,
            {
                "settings": settings,
                "today": date.today().isoformat(),
                **context,
            },
        )

    @app.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse(url="/dashboard", status_code=303)

    @app.get("/health", response_class=JSONResponse, include_in_schema=False)
    def health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "service": "developer-os",
                "version": get_version(),
                "uptime_seconds": int((datetime.now(timezone.utc) - app.state.started_at).total_seconds()),
            }
        )

    @app.get("/version", response_class=JSONResponse, include_in_schema=False)
    def version() -> JSONResponse:
        return JSONResponse({"version": get_version()})

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request, message: str | None = None, live: bool = False) -> HTMLResponse:
        context = _context(settings, refresh=live)
        return render(
            "dashboard.html",
            request,
            context=context,
            message=message,
            search=_match_entries("", learning_file, coding_file, jobs_file),
        )

    @app.post("/refresh", response_class=HTMLResponse)
    def refresh_dashboard(request: Request) -> HTMLResponse:
        context = _context(settings, refresh=True)
        return render(
            "dashboard.html",
            request,
            context=context,
            message="Live integrations refreshed.",
            search=_match_entries("", learning_file, coding_file, jobs_file),
            live=True,
        )

    @app.post("/notes")
    def add_learning_note(
        subject: str = Form(...),
        topic: str = Form(...),
        summary: str = Form(...),
        note_date: str | None = Form(None),
    ) -> RedirectResponse:
        add_note(
            learning_store(learning_file),
            subject=subject,
            topic=topic,
            summary=summary,
            note_date=validate_iso_date(note_date),
        )
        return RedirectResponse(url=f"/dashboard?message={quote_plus('Learning note added.')}", status_code=303)

    @app.post("/coding")
    def add_coding_entry(
        platform: str = Form(...),
        name: str = Form(...),
        difficulty: str = Form(...),
        topic: str = Form(...),
        problem_date: str | None = Form(None),
    ) -> RedirectResponse:
        add_problem(
            coding_store(coding_file),
            platform=platform,
            name=name,
            difficulty=difficulty,
            topic=topic,
            problem_date=validate_iso_date(problem_date),
        )
        return RedirectResponse(url=f"/dashboard?message={quote_plus('Coding entry added.')}", status_code=303)

    @app.post("/applications")
    def add_job_application(
        company: str = Form(...),
        role: str = Form(...),
        status: str = Form(...),
        application_date: str | None = Form(None),
    ) -> RedirectResponse:
        add_application(
            jobs_store(jobs_file),
            company=company,
            role=role,
            status=normalize_status(status),
            application_date=validate_iso_date(application_date),
        )
        return RedirectResponse(url=f"/dashboard?message={quote_plus('Job application added.')}", status_code=303)

    @app.get("/search", response_class=HTMLResponse)
    def search(request: Request, q: str = "") -> HTMLResponse:
        results = _match_entries(q, learning_file, coding_file, jobs_file)
        return render("search.html", request, results=results)

    @app.get("/stats", response_class=HTMLResponse)
    def stats(request: Request) -> HTMLResponse:
        context = _context(settings, refresh=False)
        return render("stats.html", request, context=context)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    runtime = load_production_settings()
    uvicorn.run(
        "developer_os.webapp:app",
        host=runtime.host,
        port=runtime.port,
        reload=False,
        log_level=runtime.log_level,
        access_log=runtime.access_log,
    )
