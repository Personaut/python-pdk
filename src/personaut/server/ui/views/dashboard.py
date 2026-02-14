"""Dashboard view for the web UI."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, render_template

from personaut.server.ui.views.api_helpers import api_get as _api_get


bp = Blueprint("dashboard", __name__)


# ============================================================================
# Routes
# ============================================================================


@bp.route("/")
def index() -> str:
    """Render the main dashboard."""
    stats = {
        "individuals": 0,
        "situations": 0,
        "relationships": 0,
        "sessions": 0,
    }

    recent_individuals: list[dict[str, Any]] = []

    # Fetch live data from the FastAPI backend
    ind_data = _api_get("/individuals")
    if ind_data:
        stats["individuals"] = ind_data.get("total", 0)
        recent_individuals = ind_data.get("individuals", [])

    sit_data = _api_get("/situations")
    if sit_data:
        stats["situations"] = sit_data.get("total", 0)

    sess_data = _api_get("/sessions")
    if sess_data:
        stats["sessions"] = sess_data.get("total", 0)

    rel_data = _api_get("/relationships")
    if rel_data:
        stats["relationships"] = rel_data.get("total", 0)

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_individuals=recent_individuals,
    )


__all__ = ["bp"]
