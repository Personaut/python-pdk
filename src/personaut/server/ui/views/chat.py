"""Chat interface views for the web UI.

Thin view layer — all persona-engine business logic lives in
``chat_engine.py``.  This module contains only the Flask Blueprint,
route handlers, and request / response translation.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from flask import Blueprint, current_app, jsonify, redirect, request, url_for
from werkzeug.wrappers import Response as WerkzeugResponse

from personaut.server.ui.views import chat_engine as engine
from personaut.server.ui.views.api_helpers import api_delete as _api_delete
from personaut.server.ui.views.api_helpers import api_get as _api_get
from personaut.server.ui.views.api_helpers import api_patch as _api_patch
from personaut.server.ui.views.api_helpers import api_post as _api_post


bp = Blueprint("chat", __name__, url_prefix="/chat")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@bp.route("/")
def select_session() -> str:
    """Select or create a chat session."""
    from flask import render_template

    sess_data = _api_get("/sessions")
    sessions = sess_data.get("sessions", []) if sess_data else []

    return render_template("chat_select.html", sessions=sessions)


@bp.route("/new", methods=["GET", "POST"])
def new_session() -> str | WerkzeugResponse:
    """Create new chat session."""
    if request.method == "POST":
        individual_id = request.form.get("individual", "")
        situation_id = request.form.get("situation", "")

        # Speaker profile: existing or new
        profile_id = request.form.get("speaker_profile", "")
        new_title = request.form.get("new_speaker_title", "").strip()
        new_context = request.form.get("new_speaker_context", "").strip()

        speaker_context = {"title": "Stranger", "context": ""}
        if new_title:
            # Save new profile
            import hashlib
            import time

            pid = "sp_" + hashlib.md5(f"{new_title}{time.time()}".encode()).hexdigest()[:8]
            new_profile = {"id": pid, "title": new_title, "context": new_context}
            engine.saved_speaker_profiles.append(new_profile)
            speaker_context = {"title": new_title, "context": new_context}
        elif profile_id:
            # Use existing profile
            for p in engine.saved_speaker_profiles:
                if p["id"] == profile_id:
                    speaker_context = {"title": p["title"], "context": p["context"]}
                    break

        if individual_id and situation_id:
            result = _api_post(
                "/sessions",
                {
                    "individual_ids": [individual_id],
                    "situation_id": situation_id,
                },
            )
            if result:
                engine.session_speaker_contexts[result["id"]] = speaker_context
                return redirect(url_for("chat.session_view", id=result["id"]))

        return redirect(url_for("chat.select_session"))

    from flask import render_template

    ind_data = _api_get("/individuals")
    individuals = ind_data.get("individuals", []) if ind_data else []

    sit_data = _api_get("/situations")
    situations = sit_data.get("situations", []) if sit_data else []

    return render_template(
        "chat_new.html",
        individuals=individuals,
        situations=situations,
        profiles=engine.saved_speaker_profiles,
        profiles_json=json.dumps(engine.saved_speaker_profiles),
    )


@bp.route("/<id>")
def session_view(id: str) -> str:
    """View chat session."""
    session = _api_get(f"/sessions/{id}")
    individual_name = "Character"
    radar_data: list[dict[str, Any]] = []

    if session and session.get("individual_ids"):
        for ind_id in session["individual_ids"]:
            ind = _api_get(f"/individuals/{ind_id}")
            if ind:
                individual_name = ind.get("name", "Character")
                radar_data.append(engine.get_individual_radar_data(ind))

    msg_data = _api_get(f"/sessions/{id}/messages")
    messages = msg_data.get("messages", []) if msg_data else []

    # Check LLM status for badge
    llm = engine.get_llm()
    llm_active = llm is not None
    llm_label = getattr(llm, "model", "LLM") if llm else "Persona Engine"
    badge_class = "active" if llm_active else "fallback"
    badge_text = f"🟢 {llm_label}" if llm_active else f"🟡 {llm_label}"

    from flask import render_template

    # Get cumulative token totals for this session
    totals = engine.session_token_usage.get(id, {})

    # Get memories, masks, triggers for the individual
    memories_list = []
    masks_list = []
    triggers_list = []
    individual_id = ""
    physical_features: dict[str, Any] = {}
    portrait_url = ""
    if session and session.get("individual_ids"):
        individual_id = session["individual_ids"][0]
        mem_data = _api_get(f"/individuals/{individual_id}/memories")
        if mem_data and mem_data.get("memories"):
            memories_list = mem_data["memories"]
        mask_data = _api_get(f"/individuals/{individual_id}/masks")
        if mask_data and mask_data.get("masks"):
            masks_list = mask_data["masks"]
        trig_data = _api_get(f"/individuals/{individual_id}/triggers")
        if trig_data and trig_data.get("triggers"):
            triggers_list = trig_data["triggers"]
        # Physical features
        ind_detail = _api_get(f"/individuals/{individual_id}")
        if ind_detail:
            physical_features = ind_detail.get("physical_features", {}) or {}
            portrait_url = ind_detail.get("portrait_url", "") or ""

    return render_template(
        "chat_session.html",
        session_id=id,
        messages=messages,
        individual_name=individual_name,
        individual_id=individual_id,
        badge_class=badge_class,
        badge_text=badge_text,
        total_tokens=f"{totals.get('total_tokens', 0):,}",
        total_prompt=f"{totals.get('prompt_tokens', 0):,}",
        total_completion=f"{totals.get('completion_tokens', 0):,}",
        radar_data=radar_data,
        radar_json=json.dumps(radar_data),
        cat_colors_json=json.dumps(engine.CATEGORY_COLORS),
        memories=memories_list,
        masks=masks_list,
        triggers=triggers_list,
        physical_features=physical_features,
        portrait_url=portrait_url,
    )


@bp.route("/<session_id>/send", methods=["POST"])
def send_chat_message(session_id: str) -> Any:
    """Proxy: send human message, generate in-character reply using PDK."""
    data = request.get_json()
    content = data.get("content", "")
    if not content:
        return jsonify({"error": "No content"}), 400

    # 1. Post human message to FastAPI
    human_msg = _api_post(f"/sessions/{session_id}/messages", {"content": content})
    if not human_msg:
        return jsonify({"error": "Failed to send message"}), 500

    # 2. Look up the individual (raw dict from API)
    session = _api_get(f"/sessions/{session_id}")
    if not session or not session.get("individual_ids"):
        return jsonify({"error": "Session not found"}), 404

    individual_id = session["individual_ids"][0]
    individual_data = _api_get(f"/individuals/{individual_id}")
    if not individual_data:
        return jsonify({"error": "Individual not found"}), 404

    # 3. Hydrate into PDK objects
    individual = engine.hydrate_individual(individual_data)

    situation = None
    situation_id = session.get("situation_id")
    if situation_id:
        situation_data = _api_get(f"/situations/{situation_id}")
        if situation_data:
            situation = engine.hydrate_situation(situation_data)

    # 4. Get speaker context for this session
    speaker_ctx = engine.session_speaker_contexts.get(session_id, {})
    speaker_role = speaker_ctx.get("context", "")

    # 5. Generate personality-driven reply using PDK Individual + PromptBuilder
    #    Now includes mask/trigger evaluation and semantic memory search
    reply_text, usage, activation_info = engine.generate_reply(
        individual,
        content,
        session_id,
        situation=situation,
        speaker_role=speaker_role,
    )
    individual_name = individual.name

    # 5b. Analyze emotions and apply realistic emotional dynamics
    emotion_updates = engine.analyze_emotions(individual, content, reply_text)

    emotional_state = individual.get_emotional_state()

    # ── Step A: Natural decay — emotions fade between turns ──
    emotional_state.decay(turns_elapsed=1)

    if emotion_updates:
        # ── Step B: Trait-modulated application ──
        # Instead of blindly overwriting, apply the LLM's analysis
        # through the personality filter: high emotional_stability
        # dampens shifts, high sensitivity amplifies them, etc.
        trait_dict = individual.traits.to_dict() if individual.traits else None
        emotional_state.apply_trait_modulated_change(
            emotion_updates,
            trait_profile=trait_dict,
        )
        logger.info(
            "Applied trait-modulated emotions for %s (reactivity: %s)",
            individual.name,
            "personality-shaped" if trait_dict else "unmodulated",
        )

    # ── Step C: Antagonistic suppression ──
    # Contradictory emotions (cheerful↔depressed, trusting↔hostile)
    # naturally suppress each other - the stronger wins.
    emotional_state.apply_antagonism(strength=0.3)

    # ── Step D: Mood baseline adaptation ──
    # Repeated emotional patterns shift the resting baseline.
    # If someone has been anxious for many turns, their baseline
    # anxiety rises — they become a more anxious person.
    emotional_state.update_mood_baseline(learning_rate=0.08)

    # Persist the processed emotions back
    final_emotions = emotional_state.to_dict()
    non_zero = {k: round(v, 3) for k, v in final_emotions.items() if v > 0.01}
    if non_zero:
        _api_patch(
            f"/individuals/{individual_id}/emotions",
            {"emotions": non_zero},
        )
        # Update the in-memory individual
        for emotion, value in final_emotions.items():
            try:
                individual.set_emotion(emotion, value)
            except Exception as e:
                logger.debug("Skipping emotion %s: %s", emotion, e)

    # Compute updated radar data from the live individual
    updated_emotions = individual.get_emotional_state().to_dict()
    radar = engine.compute_emotion_radar(updated_emotions)
    mood_volatility = emotional_state.get_emotional_volatility()
    updated_radar = {
        "name": individual_name,
        "categories": list(radar.keys()),
        "values": list(radar.values()),
        "emotions": {k: round(v, 2) for k, v in updated_emotions.items() if v > 0},
        "mood_volatility": round(mood_volatility, 3),
    }

    # 6. Store the reply in the API
    _api_post(
        f"/sessions/{session_id}/messages",
        {
            "content": reply_text,
            "sender_id": individual_id,
        },
    )

    return jsonify(
        {
            "reply": reply_text,
            "reply_sender": individual_name,
            "usage": usage,
            "session_totals": engine.session_token_usage.get(session_id, {}),
            "radar": updated_radar,
            "activation": activation_info,
        }
    )


@bp.route("/<id>/messages")
def get_messages(id: str) -> str:
    data = _api_get(f"/sessions/{id}/messages")
    return json.dumps(data or {"messages": []})


# ---------------------------------------------------------------------------
# Memory management proxy routes
# ---------------------------------------------------------------------------


def _get_individual_id_for_session(session_id: str) -> str | None:
    """Resolve the individual_id from a session."""
    session = _api_get(f"/sessions/{session_id}")
    if session and session.get("individual_ids"):
        return str(session["individual_ids"][0])
    return None


@bp.route("/<session_id>/memories/add", methods=["POST"])
def add_memory(session_id: str) -> Any:
    """Add a memory to the session's individual."""
    individual_id = _get_individual_id_for_session(session_id)
    if not individual_id:
        return jsonify({"error": "Session or individual not found"}), 404

    data = request.get_json()
    result = _api_post(f"/individuals/{individual_id}/memories", data)
    if not result:
        return jsonify({"error": "Failed to create memory"}), 500

    # Invalidate the individual cache so new memories are included
    # in the system prompt on the next message
    engine.individual_cache.pop(individual_id, None)

    return jsonify(result)


@bp.route("/<session_id>/memories/<memory_id>/delete", methods=["POST"])
def remove_memory(session_id: str, memory_id: str) -> Any:
    """Delete a memory from the session's individual."""
    individual_id = _get_individual_id_for_session(session_id)
    if not individual_id:
        return jsonify({"error": "Session not found"}), 404

    success = _api_delete(f"/individuals/{individual_id}/memories/{memory_id}")
    if success:
        # Invalidate cache so the memory is removed from system prompt
        engine.individual_cache.pop(individual_id, None)
        return jsonify({"ok": True})
    return jsonify({"error": "Memory not found"}), 404


@bp.route("/<session_id>/memories/search", methods=["POST"])
def search_memories(session_id: str) -> Any:
    """Search memories for the session's individual."""
    individual_id = _get_individual_id_for_session(session_id)
    if not individual_id:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    result = _api_post(f"/individuals/{individual_id}/memories/search", data)
    return jsonify(result or {"query": data.get("query", ""), "results": [], "total": 0})


# ---------------------------------------------------------------------------
# Mask management proxy routes
# ---------------------------------------------------------------------------


@bp.route("/<session_id>/masks/add", methods=["POST"])
def add_mask(session_id: str) -> Any:
    """Add a mask to the session's individual."""
    individual_id = _get_individual_id_for_session(session_id)
    if not individual_id:
        return jsonify({"error": "Session or individual not found"}), 404

    data = request.get_json()
    result = _api_post(f"/individuals/{individual_id}/masks", data)
    if not result:
        return jsonify({"error": "Failed to create mask"}), 500

    engine.individual_cache.pop(individual_id, None)
    return jsonify(result)


@bp.route("/<session_id>/masks/<mask_id>/delete", methods=["POST"])
def remove_mask(session_id: str, mask_id: str) -> Any:
    """Delete a mask from the session's individual."""
    individual_id = _get_individual_id_for_session(session_id)
    if not individual_id:
        return jsonify({"error": "Session not found"}), 404

    success = _api_delete(f"/individuals/{individual_id}/masks/{mask_id}")
    if success:
        engine.individual_cache.pop(individual_id, None)
        return jsonify({"ok": True})
    return jsonify({"error": "Mask not found"}), 404


# ---------------------------------------------------------------------------
# Trigger management proxy routes
# ---------------------------------------------------------------------------


@bp.route("/<session_id>/triggers/add", methods=["POST"])
def add_trigger(session_id: str) -> Any:
    """Add a trigger to the session's individual."""
    individual_id = _get_individual_id_for_session(session_id)
    if not individual_id:
        return jsonify({"error": "Session or individual not found"}), 404

    data = request.get_json()
    result = _api_post(f"/individuals/{individual_id}/triggers", data)
    if not result:
        return jsonify({"error": "Failed to create trigger"}), 500

    engine.individual_cache.pop(individual_id, None)
    return jsonify(result)


@bp.route("/<session_id>/triggers/<trigger_id>/toggle", methods=["POST"])
def toggle_trigger_route(session_id: str, trigger_id: str) -> Any:
    """Toggle a trigger's active state."""
    individual_id = _get_individual_id_for_session(session_id)
    if not individual_id:
        return jsonify({"error": "Session not found"}), 404

    result = _api_patch(f"/individuals/{individual_id}/triggers/{trigger_id}/toggle", {})
    if result:
        engine.individual_cache.pop(individual_id, None)
        return jsonify(result)
    return jsonify({"error": "Trigger not found"}), 404


@bp.route("/<session_id>/triggers/<trigger_id>/delete", methods=["POST"])
def remove_trigger(session_id: str, trigger_id: str) -> Any:
    """Delete a trigger from the session's individual."""
    individual_id = _get_individual_id_for_session(session_id)
    if not individual_id:
        return jsonify({"error": "Session not found"}), 404

    success = _api_delete(f"/individuals/{individual_id}/triggers/{trigger_id}")
    if success:
        engine.individual_cache.pop(individual_id, None)
        return jsonify({"ok": True})
    return jsonify({"error": "Trigger not found"}), 404


@bp.route("/<session_id>/generate-video", methods=["POST"])
def generate_video_view(session_id: str) -> WerkzeugResponse | tuple[WerkzeugResponse, int]:
    """Proxy video generation to the FastAPI backend.

    Veo video generation can take 1-6 minutes, so we use a long timeout.
    """
    base = current_app.config.get("API_BASE_URL", "http://localhost:8000/api")
    try:
        req = urllib.request.Request(
            f"{base}/sessions/{session_id}/video",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=360) as resp:
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
        logger.error("Video generation proxy failed: %s", e)
        return jsonify({"detail": f"Video generation failed: {e}"}), 500


__all__ = ["bp"]
