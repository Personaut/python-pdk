"""Individual management views for the web UI."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from werkzeug.wrappers import Response as WerkzeugResponse

from personaut.server.ui.views.api_helpers import api_get as _api_get
from personaut.server.ui.views.api_helpers import api_patch as _api_patch
from personaut.server.ui.views.api_helpers import api_post as _api_post


logger = logging.getLogger(__name__)

bp = Blueprint("individuals", __name__, url_prefix="/individuals")

# ---------------------------------------------------------------------------
# PDK trait / emotion names (used by forms)
# ---------------------------------------------------------------------------

TRAIT_NAMES = [
    "warmth",
    "reasoning",
    "emotional_stability",
    "dominance",
    "humility",
    "liveliness",
    "rule_consciousness",
    "social_boldness",
    "sensitivity",
    "vigilance",
    "abstractedness",
    "privateness",
    "apprehension",
    "openness_to_change",
    "self_reliance",
    "perfectionism",
    "tension",
]

# Human-readable labels for the 17 traits
TRAIT_LABELS = {
    "warmth": ("Warmth", "Reserved ↔ Warm & attentive"),
    "reasoning": ("Reasoning", "Concrete ↔ Abstract thinker"),
    "emotional_stability": ("Emotional Stability", "Reactive ↔ Emotionally stable"),
    "dominance": ("Dominance", "Deferential ↔ Dominant"),
    "humility": ("Humility", "Self-assured ↔ Humble"),
    "liveliness": ("Liveliness", "Restrained ↔ Lively & animated"),
    "rule_consciousness": ("Rule Consciousness", "Flexible ↔ Rule-following"),
    "social_boldness": ("Social Boldness", "Shy ↔ Socially bold"),
    "sensitivity": ("Sensitivity", "Tough-minded ↔ Sensitive"),
    "vigilance": ("Vigilance", "Trusting ↔ Vigilant"),
    "abstractedness": ("Abstractedness", "Grounded ↔ Imaginative"),
    "privateness": ("Privateness", "Open & forthright ↔ Private"),
    "apprehension": ("Apprehension", "Self-assured ↔ Apprehensive"),
    "openness_to_change": ("Openness to Change", "Traditional ↔ Open to change"),
    "self_reliance": ("Self-Reliance", "Group-oriented ↔ Self-reliant"),
    "perfectionism": ("Perfectionism", "Easygoing ↔ Perfectionist"),
    "tension": ("Tension", "Relaxed ↔ Tense"),
}

# Emotionally useful subset (grouped by valence) — all 36 emotions available
# but we show the most relevant ones in the creation form and hide the rest
# behind an "advanced" toggle.
PRIMARY_EMOTIONS = [
    "cheerful",
    "excited",
    "hopeful",
    "content",
    "creative",
    "proud",
    "anxious",
    "angry",
    "depressed",
    "lonely",
    "confused",
    "guilty",
]

ALL_EMOTIONS = [
    "hostile",
    "hurt",
    "angry",
    "selfish",
    "hateful",
    "critical",
    "guilty",
    "ashamed",
    "depressed",
    "lonely",
    "bored",
    "apathetic",
    "rejected",
    "confused",
    "submissive",
    "insecure",
    "anxious",
    "helpless",
    "excited",
    "sensual",
    "energetic",
    "cheerful",
    "creative",
    "hopeful",
    "proud",
    "respected",
    "appreciated",
    "important",
    "faithful",
    "satisfied",
    "content",
    "thoughtful",
    "intimate",
    "loving",
    "trusting",
    "nurturing",
]

# Metadata keys that the chat engine expects
METADATA_FIELDS = [
    ("occupation", "Occupation", "e.g. barista, software engineer, nurse", "text"),
    ("interests", "Interests", "e.g. coffee, latte art, indie music, hiking", "text"),
    ("speaking_style", "Speaking Style", "e.g. casual and warm, uses slang, tends toward long explanations", "text"),
]


def _fmt_trait(name: str) -> str:
    """Format a trait name for display. e.g. 'openness_to_change' → 'Openness to Change'"""
    return TRAIT_LABELS.get(name, (name.replace("_", " ").title(), ""))[0]


def _trait_hint(name: str) -> str:
    """Get the low↔high hint for a trait."""
    return TRAIT_LABELS.get(name, ("", ""))[1]


# ============================================================================
# Routes
# ============================================================================


@bp.route("/")
def list_view() -> str:
    """Render the individuals list page."""
    data = _api_get("/individuals")
    individuals = data.get("individuals", []) if data else []

    return render_template(
        "individuals_list.html",
        individuals=individuals,
        trait_fmt=_fmt_trait,
    )


def _collect_form_traits() -> dict[str, float]:
    """Collect trait values from form data."""
    traits: dict[str, float] = {}
    for trait in TRAIT_NAMES:
        raw = request.form.get(f"trait_{trait}", "50")
        traits[trait] = int(raw) / 100.0
    return traits


def _collect_form_emotions() -> dict[str, float]:
    """Collect non-zero emotion values from form data."""
    emotions: dict[str, float] = {}
    for emotion in ALL_EMOTIONS:
        raw = request.form.get(f"emotion_{emotion}", "0")
        val = int(raw) / 100.0
        if val > 0:
            emotions[emotion] = val
    return emotions


def _collect_form_metadata() -> dict[str, str]:
    """Collect metadata key-value pairs from form data."""
    metadata: dict[str, str] = {}
    for key, _label, _ph, _type in METADATA_FIELDS:
        meta_val = request.form.get(f"meta_{key}", "").strip()
        if meta_val:
            metadata[key] = meta_val
    return metadata


def _collect_form_physical_features() -> dict[str, Any]:
    """Collect physical feature fields from form data."""
    physical_features: dict[str, Any] = {}
    for pf_key in [
        "height",
        "build",
        "hair",
        "eyes",
        "skin_tone",
        "age_appearance",
        "facial_features",
        "clothing_style",
        "other",
    ]:
        pf_val = request.form.get(f"phys_{pf_key}", "").strip()
        if pf_val:
            physical_features[pf_key] = pf_val
    # List fields
    for pf_list_key in ["distinguishing_features", "accessories"]:
        pf_list_val = request.form.get(f"phys_{pf_list_key}", "").strip()
        if pf_list_val:
            physical_features[pf_list_key] = [v.strip() for v in pf_list_val.split(",") if v.strip()]
    return physical_features


def _process_memories(ind_id: str) -> None:
    """Process and store memory entries from form data."""
    mem_descriptions = request.form.getlist("memory_description[]")
    mem_saliences = request.form.getlist("memory_salience[]")
    mem_emotions_list = request.form.getlist("memory_emotions[]")

    for i, desc in enumerate(mem_descriptions):
        desc = desc.strip()
        if not desc:
            continue
        salience = 0.5
        if i < len(mem_saliences):
            try:
                salience = float(mem_saliences[i])
            except (ValueError, TypeError):
                salience = 0.5

        # Parse the stored emotional state JSON
        emo_state = None
        if i < len(mem_emotions_list):
            try:
                emo_state = json.loads(mem_emotions_list[i])
                if not isinstance(emo_state, dict):
                    emo_state = None
            except (json.JSONDecodeError, TypeError):
                emo_state = None

        mem_payload: dict[str, Any] = {
            "description": desc,
            "salience": salience,
            "emotional_state": emo_state,
            "metadata": {},
        }
        _api_post(f"/individuals/{ind_id}/memories", mem_payload)


def _process_masks(ind_id: str) -> dict[str, dict[str, Any]]:
    """Process mask entries from form data and persist via the API.

    Returns created mask dicts keyed by name (needed by trigger processing
    to resolve mask-activation responses).
    """
    from personaut.masks.mask import create_mask

    mask_data_list = request.form.getlist("mask_data[]")
    created_masks: dict[str, dict[str, Any]] = {}

    for mask_json in mask_data_list:
        try:
            md = json.loads(mask_json)
        except (json.JSONDecodeError, TypeError):
            continue
        mask_name = (md.get("name") or "").strip()
        if not mask_name:
            continue

        mask = create_mask(
            name=mask_name,
            emotional_modifications=md.get("emotional_modifications", {}),
            trigger_situations=md.get("trigger_situations", []),
            active_by_default=md.get("active_by_default", False),
            description=md.get("description", ""),
        )
        mask_dict = mask.to_dict()
        created_masks[mask_name] = mask_dict

        # Create mask via the API (handles in-memory state + DB persistence)
        _api_post(
            f"/individuals/{ind_id}/masks",
            {
                "name": mask_dict.get("name", mask_name),
                "description": mask_dict.get("description", ""),
                "emotional_modifications": mask_dict.get("emotional_modifications", {}),
                "trigger_situations": mask_dict.get("trigger_situations", []),
                "active_by_default": mask_dict.get("active_by_default", False),
            },
        )

    return created_masks


def _process_triggers(ind_id: str, created_masks: dict[str, dict[str, Any]]) -> None:
    """Process trigger entries from form data and persist via the API."""
    from personaut.masks.mask import Mask
    from personaut.triggers.emotional import create_emotional_trigger

    trigger_data_list = request.form.getlist("trigger_data[]")

    for trigger_json in trigger_data_list:
        try:
            td = json.loads(trigger_json)
        except (json.JSONDecodeError, TypeError):
            continue
        desc_t = (td.get("description") or "").strip()
        rules_raw = td.get("rules", [])
        if not desc_t and not rules_raw:
            continue

        # Build response — currently supports mask activation
        response = None
        resp_data = td.get("response")
        if resp_data and resp_data.get("type") == "mask":
            mask_name = resp_data.get("name", "")
            if mask_name in created_masks:
                response = Mask.from_dict(created_masks[mask_name])

        trigger = create_emotional_trigger(
            description=desc_t,
            rules=rules_raw,
            response=response,
            match_all=td.get("match_all", True),
        )
        trigger_dict = trigger.to_dict()

        # Normalise rule dicts for the API schema
        api_rules = [
            {
                "field": r.get("field", ""),
                "threshold": r.get("threshold", 0.0),
                "operator": r.get("operator", ">"),
            }
            for r in trigger_dict.get("rules", rules_raw)
        ]

        # Determine response fields for the API
        response_type = "modifications"
        response_data = None
        pdk_resp = trigger_dict.get("response")
        if pdk_resp and isinstance(pdk_resp, dict):
            response_type = pdk_resp.get("type", "modifications")
            response_data = pdk_resp.get("data")

        # Create trigger via the API (handles in-memory state + DB persistence)
        _api_post(
            f"/individuals/{ind_id}/triggers",
            {
                "description": trigger_dict.get("description", desc_t),
                "trigger_type": trigger_dict.get("type", td.get("trigger_type", "emotional")),
                "rules": api_rules,
                "match_all": trigger_dict.get("match_all", True),
                "active": trigger_dict.get("active", True),
                "priority": trigger_dict.get("priority", 0),
                "keyword_triggers": trigger_dict.get("keyword_triggers", []),
                "response_type": response_type,
                "response_data": response_data,
            },
        )


@bp.route("/create", methods=["GET", "POST"])
def create_view() -> str | WerkzeugResponse:
    """Render the create individual form with traits, emotions, and metadata."""
    if request.method == "POST":
        name = request.form.get("name", "")
        description = request.form.get("description", "")
        individual_type = request.form.get("individual_type", "simulated")

        traits = _collect_form_traits()
        emotions = _collect_form_emotions()
        metadata = _collect_form_metadata()
        physical_features = _collect_form_physical_features()
        generate_portrait = request.form.get("generate_portrait") == "on"

        payload = {
            "name": name,
            "description": description,
            "individual_type": individual_type,
            "initial_emotions": emotions if emotions else None,
            "initial_traits": traits,
            "physical_features": physical_features if physical_features else None,
            "generate_portrait": generate_portrait and bool(physical_features),
            "metadata": metadata if metadata else None,
        }

        result = _api_post("/individuals", payload)
        if result:
            ind_id = result["id"]
            _process_memories(ind_id)
            created_masks = _process_masks(ind_id)
            _process_triggers(ind_id, created_masks)

            return redirect(url_for("individuals.detail_view", id=ind_id))
        return redirect(url_for("individuals.list_view"))

    # GET — build the form
    from personaut.masks.defaults import DEFAULT_MASKS

    preset_masks_data = [m.to_dict() for m in DEFAULT_MASKS]

    return render_template(
        "individuals_create.html",
        traits=TRAIT_NAMES,
        trait_labels=TRAIT_LABELS,
        primary_emotions=PRIMARY_EMOTIONS,
        all_emotions=ALL_EMOTIONS,
        metadata_fields=METADATA_FIELDS,
        preset_masks=DEFAULT_MASKS,
        preset_masks_json=json.dumps(preset_masks_data),
        all_emotions_json=json.dumps(list(ALL_EMOTIONS)),
    )


@bp.route("/<id>")
def detail_view(id: str) -> str:
    """Render individual detail page with full traits, emotions, and metadata."""
    data = _api_get(f"/individuals/{id}")

    if not data:
        return render_template("individuals_not_found.html", id=id)

    return render_template(
        "individuals_detail.html",
        ind=data,
        trait_fmt=_fmt_trait,
    )


@bp.route("/<id>/edit", methods=["GET", "POST"])
def edit_view(id: str) -> str | WerkzeugResponse:
    """Render individual edit form pre-populated with current values."""
    if request.method == "POST":
        # Collect trait values
        traits: dict[str, float] = {}
        for trait in TRAIT_NAMES:
            raw = request.form.get(f"trait_{trait}", "50")
            traits[trait] = int(raw) / 100.0

        # Collect emotion values
        emotions: dict[str, float] = {}
        for emotion in ALL_EMOTIONS:
            raw = request.form.get(f"emotion_{emotion}", "0")
            val = int(raw) / 100.0
            emotions[emotion] = val

        # Collect metadata
        metadata: dict[str, str] = {}
        for key, _label, _ph, _type in METADATA_FIELDS:
            meta_val = request.form.get(f"meta_{key}", "").strip()
            if meta_val:
                metadata[key] = meta_val

        # Collect physical features
        physical_features: dict[str, Any] = {}
        for pf_key in [
            "height",
            "build",
            "hair",
            "eyes",
            "skin_tone",
            "age_appearance",
            "facial_features",
            "clothing_style",
            "other",
        ]:
            pf_val = request.form.get(f"phys_{pf_key}", "").strip()
            if pf_val:
                physical_features[pf_key] = pf_val
        for pf_list_key in ["distinguishing_features", "accessories"]:
            pf_list_val = request.form.get(f"phys_{pf_list_key}", "").strip()
            if pf_list_val:
                physical_features[pf_list_key] = [v.strip() for v in pf_list_val.split(",") if v.strip()]

        # Update via API
        name = request.form.get("name", "")
        description = request.form.get("description", "")

        _api_patch(
            f"/individuals/{id}",
            {
                "name": name,
                "description": description,
                "physical_features": physical_features,
                "metadata": metadata,
            },
        )

        # Update emotions via emotions endpoint
        _api_post(f"/individuals/{id}/emotions", {"emotions": emotions})

        # Update traits via traits endpoint
        _api_post(f"/individuals/{id}/traits", {"traits": traits})

        return redirect(url_for("individuals.detail_view", id=id))

    # GET — load current data
    data = _api_get(f"/individuals/{id}")
    if not data:
        return render_template("individuals_not_found.html", id=id)

    current_traits = data.get("trait_profile", {}) or {}
    current_emotions = data.get("emotional_state", {}) or {}
    current_metadata = data.get("metadata", {}) or {}
    current_physical = data.get("physical_features", {}) or {}

    return render_template(
        "individuals_edit.html",
        ind=data,
        traits=TRAIT_NAMES,
        trait_labels=TRAIT_LABELS,
        all_emotions=ALL_EMOTIONS,
        current_traits=current_traits,
        current_emotions=current_emotions,
        current_metadata=current_metadata,
        current_physical=current_physical,
        metadata_fields=METADATA_FIELDS,
    )


@bp.route("/<id>/emotions", methods=["GET", "POST"])
def emotions_view(id: str) -> str | WerkzeugResponse:
    """Render emotions management page."""
    if request.method == "POST":
        return redirect(url_for("individuals.detail_view", id=id))
    return redirect(url_for("individuals.edit_view", id=id))


@bp.route("/<id>/traits", methods=["GET", "POST"])
def traits_view(id: str) -> str | WerkzeugResponse:
    """Render trait management page."""
    if request.method == "POST":
        return redirect(url_for("individuals.detail_view", id=id))
    return redirect(url_for("individuals.edit_view", id=id))


@bp.route("/<id>/triggers", methods=["GET", "POST"])
def triggers_view(id: str) -> str | WerkzeugResponse:
    """Render triggers and masks configuration page."""
    if request.method == "POST":
        return redirect(url_for("individuals.detail_view", id=id))
    return redirect(url_for("individuals.edit_view", id=id))


# ---------------------------------------------------------------------------
# AJAX endpoint — generate emotional state for a memory
# ---------------------------------------------------------------------------


@bp.route("/generate-memory-emotions", methods=["POST"])
def generate_memory_emotions() -> WerkzeugResponse | tuple[WerkzeugResponse, int]:
    """Generate a trait-modulated emotional state for a memory description.

    Delegates to the PDK's ``generate_memory_emotional_state()`` function
    which handles LLM prompting, JSON parsing, validation, and trait
    modulation via ``EmotionalState.apply_trait_modulated_change()``.
    """
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    trait_profile: dict[str, float] = data.get("traits") or {}
    ind_name: str = data.get("name") or "this person"

    if not description:
        return jsonify({"error": "No memory description provided"}), 400

    try:
        from personaut.memory import generate_memory_emotional_state

        state = generate_memory_emotional_state(
            description=description,
            trait_profile=trait_profile if trait_profile else None,
            individual_name=ind_name,
        )

        # Return only non-zero emotions for a cleaner response
        emotions = {k: round(v, 2) for k, v in state.to_dict().items() if v > 0.01}
        return jsonify({"emotions": emotions})

    except Exception as e:
        logger.warning("Memory emotion generation failed: %s", e)
        return jsonify({"error": str(e)}), 500


@bp.route("/<id>/generate-portrait", methods=["POST"])
def generate_portrait_view(id: str) -> WerkzeugResponse | tuple[WerkzeugResponse, int]:
    """Proxy portrait generation request to the FastAPI backend.

    This route exists because the JS frontend calls Flask (port 5000),
    but the actual generation endpoint is on FastAPI (port 8000).
    Uses a longer timeout since image generation takes 15-30s.
    """
    base = current_app.config.get("API_BASE_URL", "http://localhost:8000/api")
    try:
        req = urllib.request.Request(
            f"{base}/individuals/{id}/portrait",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return jsonify(result)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else "{}"
        try:
            detail = json.loads(body)
        except Exception:
            detail = {"detail": body}
        return jsonify(detail), e.code
    except Exception as e:
        logger.error("Portrait generation proxy failed: %s", e)
        return jsonify({"detail": f"Portrait generation failed: {e}"}), 500


__all__ = ["bp"]
