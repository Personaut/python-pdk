"""Relationship management views for the web UI."""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for
from werkzeug.wrappers import Response as WerkzeugResponse


bp = Blueprint("relationships", __name__, url_prefix="/relationships")


@bp.route("/")
def list_view() -> str:
    """List relationships."""
    return render_template("relationships_list.html")


@bp.route("/create", methods=["GET", "POST"])
def create_view() -> str | WerkzeugResponse:
    """Create relationship."""
    if request.method == "POST":
        return redirect(url_for("relationships.list_view"))
    return render_template("relationships_create.html")


@bp.route("/<id>")
def detail_view(id: str) -> str:
    """View relationship."""
    return render_template("relationships_detail.html", id=id)


@bp.route("/<id>/edit", methods=["GET", "POST"])
def edit_view(id: str) -> str | WerkzeugResponse:
    """Edit relationship."""
    if request.method == "POST":
        return redirect(url_for("relationships.detail_view", id=id))
    return render_template("relationships_edit.html", id=id)


__all__ = ["bp"]
