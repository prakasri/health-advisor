"""F5.2 PDF rendering with WeasyPrint from templates/report.html (same order as the web view)."""

import sys
from datetime import datetime
from functools import cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.safety.fallback import report_text
from app.schemas import Report

TEMPLATES = Path(__file__).parent / "templates"
_HOMEBREW_LIB = Path("/opt/homebrew/lib")


def _allow_homebrew_libraries() -> None:
    """Local macOS dev only: Pango installed by Homebrew lives outside dyld's default search path.

    WeasyPrint loads libraries by bare name through cffi; retry with the Homebrew path when the
    bare name fails. No effect on Linux (the Docker image installs Pango system-wide)."""
    if sys.platform != "darwin" or not _HOMEBREW_LIB.is_dir():
        return
    import cffi

    if getattr(cffi.FFI.dlopen, "_homebrew_fallback", False):
        return
    original = cffi.FFI.dlopen

    def dlopen(self, name, flags=0):
        try:
            return original(self, name, flags)
        except OSError:
            candidate = _HOMEBREW_LIB / name
            if isinstance(name, str) and candidate.exists():
                return original(self, str(candidate), flags)
            raise

    dlopen._homebrew_fallback = True
    cffi.FFI.dlopen = dlopen


@cache
def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    env.filters["hba1c"] = lambda v: f"{v:.1f}%"
    env.filters["thousands"] = lambda v: f"{v:,}"
    return env


def render_html(report: Report) -> str:
    created = report.meta.created_at
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    return (
        _env()
        .get_template("report.html")
        .render(
            r=report,
            created=created.strftime("%d %B %Y"),
            ai_label=report_text()["ai_label"],
            fallback_note=report_text()["fallback_note"],
            no_comorbidities=report_text()["no_comorbidities"],
        )
    )


def render_pdf(report: Report) -> bytes:
    _allow_homebrew_libraries()
    from weasyprint import HTML  # imported lazily: needs Pango at runtime

    return HTML(string=render_html(report), base_url=str(TEMPLATES)).write_pdf()


def pdf_filename(report: Report) -> str:
    created = report.meta.created_at
    day = created.date().isoformat() if hasattr(created, "date") else str(created)[:10]
    return f"health-report-{day}.pdf"


def warm_up() -> None:
    """Load Pango and fonts at start-up so the first user's PDF meets the 5 s target (NFR-3)."""
    try:
        _allow_homebrew_libraries()
        from weasyprint import HTML

        HTML(string="<p>warm-up</p>").write_pdf()
    except OSError:
        pass  # PDF libraries missing (e.g. a dev machine without Pango): API still starts
