"""Situation management views for the web UI."""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for
from werkzeug.wrappers import Response as WerkzeugResponse

from personaut.server.ui.views.api_helpers import api_get as _api_get
from personaut.server.ui.views.api_helpers import api_patch as _api_patch
from personaut.server.ui.views.api_helpers import api_post as _api_post


bp = Blueprint("situations", __name__, url_prefix="/situations")

# ---------------------------------------------------------------------------
# Modality metadata
# ---------------------------------------------------------------------------

MODALITIES = [
    {
        "value": "in_person",
        "label": "In Person",
        "icon": "👥",
        "desc": "Face-to-face interaction with visual & audio cues",
        "sync": True,
        "visual": True,
        "audio": True,
        "formality": "casual",
    },
    {
        "value": "text_message",
        "label": "Text Message",
        "icon": "💬",
        "desc": "Asynchronous texting — casual, short replies",
        "sync": False,
        "visual": False,
        "audio": False,
        "formality": "casual",
    },
    {
        "value": "email",
        "label": "Email",
        "icon": "📧",
        "desc": "Semi-formal written communication",
        "sync": False,
        "visual": False,
        "audio": False,
        "formality": "semi-formal",
    },
    {
        "value": "phone_call",
        "label": "Phone Call",
        "icon": "📞",
        "desc": "Real-time voice-only conversation",
        "sync": True,
        "visual": False,
        "audio": True,
        "formality": "semi-formal",
    },
    {
        "value": "video_call",
        "label": "Video Call",
        "icon": "📹",
        "desc": "Real-time video & audio interaction",
        "sync": True,
        "visual": True,
        "audio": True,
        "formality": "semi-formal",
    },
    {
        "value": "survey",
        "label": "Survey",
        "icon": "📋",
        "desc": "Formal questionnaire / structured interaction",
        "sync": False,
        "visual": False,
        "audio": False,
        "formality": "formal",
    },
]

MODALITY_ICONS = {m["value"]: m["icon"] for m in MODALITIES}
MODALITY_LABELS = {m["value"]: m["label"] for m in MODALITIES}

# Suggested context keys (shown as pre-built fields in the form)
CONTEXT_PRESETS = [
    ("time_of_day", "Time of Day", "e.g. morning, afternoon, late night"),
    ("weather", "Weather", "e.g. sunny, rainy, cold"),
    ("noise_level", "Noise Level", "e.g. quiet, moderate, loud / crowded"),
    ("mood", "General Mood", "e.g. casual, tense, celebratory"),
    ("occasion", "Occasion", "e.g. first meeting, work shift, birthday party"),
    ("relationship_context", "Relationship Context", "e.g. co-workers, strangers, old friends"),
]


# ============================================================================
# Routes
# ============================================================================


@bp.route("/")
def list_view() -> str:
    """Render the situations list page."""
    data = _api_get("/situations")
    situations = data.get("situations", []) if data else []

    return render_template(
        "situations_list.html",
        situations=situations,
        modality_icons=MODALITY_ICONS,
        modality_labels=MODALITY_LABELS,
    )


@bp.route("/create", methods=["GET", "POST"])
def create_view() -> str | WerkzeugResponse:
    """Render the create situation form."""
    if request.method == "POST":
        description = request.form.get("description", "")
        modality = request.form.get("modality", "in_person")
        location = request.form.get("location", "")

        # Collect context values
        context: dict[str, str] = {}
        for key, _label, _ph in CONTEXT_PRESETS:
            val = request.form.get(f"ctx_{key}", "").strip()
            if val:
                context[key] = val

        # Collect custom context keys
        custom_keys = request.form.getlist("custom_ctx_key")
        custom_vals = request.form.getlist("custom_ctx_val")
        for k, v in zip(custom_keys, custom_vals):
            k, v = k.strip(), v.strip()
            if k and v:
                context[k] = v

        payload = {
            "description": description,
            "modality": modality,
            "location": location or None,
            "context": context if context else None,
        }

        result = _api_post("/situations", payload)
        if result:
            return redirect(url_for("situations.detail_view", id=result["id"]))
        return redirect(url_for("situations.list_view"))

    # GET — render the form
    return render_template(
        "situations_create.html",
        modalities=MODALITIES,
        context_presets=CONTEXT_PRESETS,
    )


@bp.route("/<id>")
def detail_view(id: str) -> str:
    """Render situation detail page."""
    data = _api_get(f"/situations/{id}")

    if not data:
        return render_template("situations_not_found.html", id=id)

    modality = data.get("modality", "text_message")
    icon = MODALITY_ICONS.get(modality, "📍")
    label = MODALITY_LABELS.get(modality, modality)
    # Find full modality info
    mod_info = next((m for m in MODALITIES if m["value"] == modality), None)

    return render_template(
        "situations_detail.html",
        sit=data,
        icon=icon,
        label=label,
        mod_info=mod_info,
    )


@bp.route("/<id>/edit", methods=["GET", "POST"])
def edit_view(id: str) -> str | WerkzeugResponse:
    """Render situation edit form pre-populated with current values."""
    if request.method == "POST":
        description = request.form.get("description", "")
        modality = request.form.get("modality", "in_person")
        location = request.form.get("location", "")

        # Collect context values
        context: dict[str, str] = {}
        for key, _label, _ph in CONTEXT_PRESETS:
            val = request.form.get(f"ctx_{key}", "").strip()
            if val:
                context[key] = val

        # Custom context
        custom_keys = request.form.getlist("custom_ctx_key")
        custom_vals = request.form.getlist("custom_ctx_val")
        for k, v in zip(custom_keys, custom_vals):
            k, v = k.strip(), v.strip()
            if k and v:
                context[k] = v

        _api_patch(
            f"/situations/{id}",
            {
                "description": description,
                "modality": modality,
                "location": location or None,
                "context": context if context else None,
            },
        )

        return redirect(url_for("situations.detail_view", id=id))

    # GET — load current data
    data = _api_get(f"/situations/{id}")
    if not data:
        return render_template("situations_not_found.html", id=id)

    current_context = data.get("context", {}) or {}
    current_modality = data.get("modality", "in_person")

    # Separate preset keys from custom keys
    preset_keys = {k for k, _, _ in CONTEXT_PRESETS}
    custom_context = {k: v for k, v in current_context.items() if k not in preset_keys}

    return render_template(
        "situations_edit.html",
        sit=data,
        modalities=MODALITIES,
        context_presets=CONTEXT_PRESETS,
        current_modality=current_modality,
        current_context=current_context,
        custom_context=custom_context,
    )


__all__ = ["bp"]
