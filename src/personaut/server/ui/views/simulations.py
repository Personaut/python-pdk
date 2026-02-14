"""Simulation views for the web UI.

Thin view layer — all simulation-engine business logic lives in
``simulation_engine.py``.  This module contains the Flask Blueprint,
route handlers, and simulation runner orchestration.

Supports three PDK simulation modes:
  - CONVERSATION: Multi-turn dialogue between 2+ individuals
  - SURVEY: Questionnaire responses from 1+ individuals
  - OUTCOME TRACKING: Goal-oriented conversations with correlation analysis
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

# ── PDK imports ──
from personaut.individuals import Individual
from personaut.server.ui.views import simulation_engine as engine
from personaut.server.ui.views.api_helpers import api_get as _api_get
from personaut.situations import Situation, create_situation


bp = Blueprint("simulations", __name__, url_prefix="/simulations")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Persistent simulation storage (JSON files)
# ---------------------------------------------------------------------------


def _sim_dir() -> Path:
    """Return the simulations storage directory, creating it if needed."""
    base = os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db")
    sim_path = Path(base).resolve().parent / "simulations"
    sim_path.mkdir(parents=True, exist_ok=True)
    return sim_path


def _save_simulation(result: dict[str, Any]) -> str:
    """Persist a simulation result to disk and return its ID."""
    sim_id = f"sim_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()

    # Build metadata envelope
    envelope: dict[str, Any] = {
        "id": sim_id,
        "created_at": now,
        "mode": result.get("mode", "unknown"),
        "result": result,
    }

    # Derive a human-readable title
    mode = result.get("mode", "unknown")
    if mode == "conversation":
        variations = result.get("variations", [])
        if variations:
            speakers = set()
            for turn in variations[0].get("turns", []):
                speakers.add(turn.get("speaker", "?"))
            envelope["title"] = " & ".join(sorted(speakers))
        else:
            envelope["title"] = "Conversation"
        envelope["summary"] = f"{result.get('turn_count', 0)} turns · {len(variations)} variation(s)"
    elif mode == "survey":
        envelope["title"] = f"Survey ({result.get('question_count', 0)} questions)"
        envelope["summary"] = (
            f"{result.get('respondent_count', 0)} respondent(s) · {len(result.get('variations', []))} variation(s)"
        )
    elif mode == "outcome":
        trials = result.get("trials", [])
        success = sum(1 for t in trials if t.get("outcome", {}).get("achieved"))
        envelope["title"] = result.get("outcome_description", "Outcome Tracking")[:60]
        envelope["summary"] = f"{success}/{len(trials)} success · Agent: {result.get('agent_name', '?')}"
    else:
        envelope["title"] = mode.title()
        envelope["summary"] = ""

    filepath = _sim_dir() / f"{sim_id}.json"
    filepath.write_text(json.dumps(envelope, indent=2, default=str))
    logger.info("Saved simulation %s → %s", sim_id, filepath)
    return sim_id


def _list_simulations() -> list[dict[str, Any]]:
    """List all saved simulations (metadata only, no full results)."""
    sims: list[dict[str, Any]] = []
    sim_path = _sim_dir()
    for fp in sorted(sim_path.glob("sim_*.json"), reverse=True):
        try:
            data = json.loads(fp.read_text())
            sims.append(
                {
                    "id": data.get("id", fp.stem),
                    "mode": data.get("mode", "unknown"),
                    "title": data.get("title", "Untitled"),
                    "summary": data.get("summary", ""),
                    "created_at": data.get("created_at", ""),
                }
            )
        except (json.JSONDecodeError, OSError):
            logger.warning("Skipping corrupt simulation file: %s", fp)
    return sims


def _get_simulation(sim_id: str) -> dict[str, Any] | None:
    """Load a full simulation result by ID."""
    fp = _sim_dir() / f"{sim_id}.json"
    if not fp.exists():
        return None
    try:
        result: dict[str, Any] = json.loads(fp.read_text())
        return result
    except (json.JSONDecodeError, OSError):
        return None


def _delete_simulation(sim_id: str) -> bool:
    """Delete a simulation by ID."""
    fp = _sim_dir() / f"{sim_id}.json"
    if fp.exists():
        fp.unlink()
        return True
    return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@bp.route("/")
def index() -> str:
    """Simulation landing page."""
    from flask import render_template

    individuals_resp = _api_get("/individuals?page_size=100") or {}
    situations_resp = _api_get("/situations?page_size=100") or {}

    # API returns paginated responses: { "individuals": [...], "total": N, ... }
    individuals = individuals_resp.get("individuals", []) if isinstance(individuals_resp, dict) else individuals_resp
    situations = situations_resp.get("situations", []) if isinstance(situations_resp, dict) else situations_resp

    llm = engine.get_llm()
    llm_model = getattr(llm, "model", None) if llm else None

    # Load simulation history for the sidebar
    sim_history = _list_simulations()

    return render_template(
        "simulations.html",
        individuals=individuals,
        situations=situations,
        individuals_json=json.dumps(individuals),
        situations_json=json.dumps(situations),
        llm_model=llm_model,
        sim_history=sim_history,
        sim_history_json=json.dumps(sim_history),
    )


@bp.route("/run", methods=["POST"])
def run_simulation() -> Any:
    """Execute a simulation and return results as JSON."""
    data = request.get_json()
    mode = data.get("mode")
    individual_ids = data.get("individual_ids", [])
    situation_id = data.get("situation_id")
    variations = data.get("variations", 1)

    if not individual_ids:
        return jsonify({"error": "No individuals selected"}), 400

    # Fetch and hydrate individuals
    individuals: list[Individual] = []
    for ind_id in individual_ids:
        ind_data = _api_get(f"/individuals/{ind_id}")
        if ind_data:
            individuals.append(engine.hydrate_individual(ind_data))

    if not individuals:
        return jsonify({"error": "Could not load individuals"}), 400

    # Fetch and hydrate situation (optional)
    situation = None
    if situation_id:
        sit_data = _api_get(f"/situations/{situation_id}")
        if sit_data:
            situation = engine.hydrate_situation(sit_data)

    # Default situation
    if situation is None:
        situation = create_situation(
            modality="in_person",
            description="A casual conversation",
        )

    if mode == "conversation":
        response = _run_conversation(individuals, situation, data, variations)
    elif mode == "survey":
        response = _run_survey(individuals, situation, data, variations)
    elif mode == "outcome":
        response = _run_outcome_tracking(individuals, situation, data)
    else:
        return jsonify({"error": f"Unknown mode: {mode}"}), 400

    # Auto-save the simulation result
    try:
        result_data = response.get_json()
        if result_data and "error" not in result_data:
            sim_id = _save_simulation(result_data)
            result_data["sim_id"] = sim_id
            return jsonify(result_data)
    except Exception:
        logger.exception("Failed to save simulation result")

    return response


# ---------------------------------------------------------------------------
# History routes
# ---------------------------------------------------------------------------


@bp.route("/history")
def history_list() -> Any:
    """Return simulation history as JSON."""
    sims = _list_simulations()
    return jsonify({"simulations": sims, "total": len(sims)})


@bp.route("/history/<sim_id>")
def history_detail(sim_id: str) -> Any:
    """Return a full simulation result by ID."""
    sim = _get_simulation(sim_id)
    if sim is None:
        return jsonify({"error": "Simulation not found"}), 404
    return jsonify(sim)


@bp.route("/history/<sim_id>", methods=["DELETE"])
def history_delete(sim_id: str) -> Any:
    """Delete a simulation by ID."""
    if _delete_simulation(sim_id):
        return "", 204
    return jsonify({"error": "Simulation not found"}), 404


# ---------------------------------------------------------------------------
# Simulation runners (orchestrate engine functions, return jsonify)
# ---------------------------------------------------------------------------


def _run_conversation(
    individuals: list[Individual],
    situation: Situation,
    config: dict[str, Any],
    num_variations: int,
) -> Any:
    """Run a conversation simulation with LLM."""
    if len(individuals) < 2:
        return jsonify({"error": "Need at least 2 individuals for a conversation"}), 400

    max_turns = config.get("max_turns", 10)
    all_variations = []

    for _var_idx in range(num_variations):
        history: list[dict[str, Any]] = []
        speaker_idx = 0

        for turn_num in range(max_turns):
            speaker = individuals[speaker_idx]

            # Build prompt
            prompt = engine.build_conversation_prompt(
                individuals,
                situation,
                turn_num,
                speaker,
                history,
            )

            # Generate
            response = engine.generate_llm_response(prompt, max_tokens=200)

            if response is None:
                # Fallback
                if turn_num == 0:
                    response = f"Hi, I'm {speaker.name}. Nice to meet you."
                else:
                    response = "That's interesting. Tell me more about that."

            # Clean response
            name_prefix = f"{speaker.name}:"
            if response.startswith(name_prefix):
                response = response[len(name_prefix) :].strip()

            # Remove any spurious extra speaker lines (LLM sometimes generates the other person)
            lines = response.split("\n")
            clean_lines = []
            other_names = [ind.name for ind in individuals if ind.name != speaker.name]
            for line in lines:
                if any(line.strip().startswith(f"{n}:") for n in other_names):
                    break
                clean_lines.append(line)
            response = "\n".join(clean_lines).strip()

            # ── Emotional dynamics: analyze and update ──
            emotion_updates = engine.analyze_simulation_emotions(
                speaker,
                [i for i in individuals if i.name != speaker.name],
                response,
                history,
            )
            engine.update_speaker_emotions(speaker, emotion_updates)

            # Now compute radar AFTER emotional state has been updated
            radar_data = engine.get_emotion_radar_data(speaker)

            history.append(
                {
                    "speaker": speaker.name,
                    "content": response,
                    "turn": turn_num,
                    "radar": radar_data,
                }
            )

            # Next speaker
            speaker_idx = (speaker_idx + 1) % len(individuals)

        all_variations.append({"turns": history})

    return jsonify(
        {
            "mode": "conversation",
            "variations": all_variations,
            "turn_count": max_turns,
            "participant_count": len(individuals),
        }
    )


def _run_survey(
    individuals: list[Individual],
    situation: Situation,
    config: dict[str, Any],
    num_variations: int,
) -> Any:
    """Run a survey simulation with LLM."""
    survey_questions = config.get("questions", [])
    if not survey_questions:
        return jsonify({"error": "No questions provided"}), 400

    # Image data (optional)
    image_base64 = config.get("image_base64")
    image_mime = config.get("image_mime", "image/png")
    image_description = config.get("image_description", "")
    has_image = bool(image_base64)

    all_variations = []

    for _var_idx in range(num_variations):
        respondents_data = []

        for individual in individuals:
            answers = []

            for question in survey_questions:
                # Build prompt (with image context if available)
                prompt = engine.build_survey_prompt(
                    individual,
                    question,
                    situation,
                    has_image=has_image,
                    image_description=image_description,
                )

                # Generate — use multimodal if image, else text-only
                if has_image:
                    response = engine.generate_llm_response_multimodal(
                        prompt,
                        image_base64=image_base64,
                        image_mime=image_mime,
                        max_tokens=300,
                    )
                else:
                    response = engine.generate_llm_response(prompt, max_tokens=250)

                q_type = question.get("type", "open_ended")
                answer: dict[str, Any] = {
                    "question": question.get("text", ""),
                    "type": q_type,
                }

                if response:
                    # Try to parse structured responses
                    if q_type.startswith("likert"):
                        # Extract number rating
                        nums = re.findall(r"\b(\d)\b", response[:20])
                        if nums:
                            answer["rating"] = int(nums[0])
                        answer["response"] = response
                    elif q_type == "yes_no":
                        resp_lower = response.lower().strip()
                        if resp_lower.startswith("yes"):
                            answer["rating"] = "Yes"
                        elif resp_lower.startswith("no"):
                            answer["rating"] = "No"
                        answer["response"] = response
                    elif q_type == "multiple_choice":
                        answer["response"] = response
                    else:
                        answer["response"] = response
                else:
                    # Fallback
                    answer["response"] = engine.survey_fallback(individual, question)

                answers.append(answer)

            respondents_data.append(
                {
                    "name": individual.name,
                    "id": getattr(individual, "id", ""),
                    "answers": answers,
                }
            )

        all_variations.append({"respondents": respondents_data})

    return jsonify(
        {
            "mode": "survey",
            "variations": all_variations,
            "question_count": len(survey_questions),
            "respondent_count": len(individuals),
            "has_image": has_image,
        }
    )


def _run_outcome_tracking(
    individuals: list[Individual],
    situation: Situation,
    config: dict[str, Any],
) -> Any:
    """Run outcome tracking simulation with controlled variation.

    Depending on `vary_by`, randomizes one dimension (traits, emotions,
    or situation) while holding the other two constant. Then correlates
    the varied dimension with outcome success.
    """
    outcome_desc = config.get("outcome", "")
    if not outcome_desc:
        return jsonify({"error": "No outcome description provided"}), 400

    if not individuals:
        return jsonify({"error": "No agent individual selected"}), 400

    agent = individuals[0]  # The agent pursuing the outcome
    num_trials = int(config.get("num_trials") or 5)
    max_turns = int(config.get("max_turns") or 6)
    vary_by = config.get("vary_by", "traits")
    scenario_context = config.get("scenario_context", "").strip()

    # Build fixed baselines for controlled variables
    from personaut.traits.trait import ALL_TRAITS

    fixed_traits = None if vary_by == "traits" else dict.fromkeys(ALL_TRAITS, 0.5)
    fixed_emotions = None if vary_by == "emotions" else {"content": 0.5, "thoughtful": 0.4}

    all_trials = []

    for trial_idx in range(num_trials):
        customer = engine.generate_random_individual(
            trial_idx,
            vary_by=vary_by,
            fixed_traits=fixed_traits,
            fixed_emotions=fixed_emotions,
        )
        logger.info(
            "Outcome trial %d/%d (vary=%s): %s (agent) vs %s (customer)",
            trial_idx + 1, num_trials, vary_by, agent.name, customer.name,
        )

        # Build situation pair (agent gets outcome goal, customer does not)
        trial_situation, situation_params = (
            engine.generate_random_situation() if vary_by == "situation" else (situation, {})
        )
        enhanced_sit, grounded_sit = _build_trial_situations(
            trial_situation, outcome_desc, scenario_context,
        )

        history = _run_trial_conversation(
            [agent, customer], enhanced_sit, grounded_sit, agent, max_turns,
        )

        trial_data = _collect_trial_data(
            trial_idx, customer, history, outcome_desc, vary_by, situation_params,
        )
        all_trials.append(trial_data)

    return jsonify(_build_outcome_response(
        agent, outcome_desc, scenario_context, vary_by, max_turns, all_trials,
    ))


def _build_trial_situations(
    base_situation: Situation,
    outcome_desc: str,
    scenario_context: str,
) -> tuple[Situation, Situation]:
    """Create the enhanced (agent) and grounded (customer) situations for a trial."""
    base_desc = base_situation.description or "A conversation"
    context_block = f" Context: {scenario_context}." if scenario_context else ""

    modality_val = (
        base_situation.modality.value
        if hasattr(base_situation.modality, "value")
        else str(base_situation.modality)
    )
    location = getattr(base_situation, "location", None)

    enhanced = create_situation(
        modality=modality_val,
        description=(
            f"{base_desc}.{context_block} "
            f"Your goal is to achieve this outcome: {outcome_desc}. "
            f"Be natural and persuasive, not pushy."
        ),
        location=location,
    )

    if scenario_context:
        grounded = create_situation(
            modality=modality_val,
            description=f"{base_desc}.{context_block}",
            location=location,
        )
    else:
        grounded = base_situation

    return enhanced, grounded


def _run_trial_conversation(
    trial_individuals: list[Individual],
    enhanced_situation: Situation,
    grounded_situation: Situation,
    agent: Individual,
    max_turns: int,
) -> list[dict[str, Any]]:
    """Run a multi-turn conversation for one outcome trial."""
    history: list[dict[str, Any]] = []
    speaker_idx = 0

    for turn_num in range(max_turns):
        speaker = trial_individuals[speaker_idx]
        prompt = engine.build_conversation_prompt(
            trial_individuals,
            enhanced_situation if speaker == agent else grounded_situation,
            turn_num,
            speaker,
            history,
        )
        response = engine.generate_llm_response(prompt, max_tokens=200)

        if response is None:
            response = f"Hi there, I'm {speaker.name}." if turn_num == 0 else "Tell me more about that."

        # Clean response
        response = _clean_speaker_response(response, speaker.name, trial_individuals)
        history.append({"speaker": speaker.name, "content": response, "turn": turn_num})
        speaker_idx = (speaker_idx + 1) % 2

    return history


def _clean_speaker_response(response: str, speaker_name: str, all_individuals: list[Individual]) -> str:
    """Strip speaker prefix and truncate at other speakers' lines."""
    name_prefix = f"{speaker_name}:"
    if response.startswith(name_prefix):
        response = response[len(name_prefix):].strip()

    lines = response.split("\n")
    clean_lines = []
    other_names = [ind.name for ind in all_individuals if ind.name != speaker_name]
    for line in lines:
        if any(line.strip().startswith(f"{n}:") for n in other_names):
            break
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()


def _collect_trial_data(
    trial_idx: int,
    customer: Individual,
    history: list[dict[str, Any]],
    outcome_desc: str,
    vary_by: str,
    situation_params: dict[str, str],
) -> dict[str, Any]:
    """Evaluate outcome and collect all dimensions for a single trial."""
    outcome_result = engine.evaluate_outcome(outcome_desc, history, customer.name, customer)

    customer_traits = customer.traits.to_dict() if customer.traits else {}
    customer_emotions = customer.get_emotional_state().to_dict() if customer.get_emotional_state() else {}

    trial_data: dict[str, Any] = {
        "trial_idx": trial_idx,
        "customer_name": customer.name,
        "customer_traits": {k: round(v, 3) for k, v in customer_traits.items()},
        "customer_emotions": {k: round(v, 3) for k, v in customer_emotions.items() if v > 0},
        "customer_metadata": customer.metadata or {},
        "outcome": outcome_result,
        "conversation": history,
    }
    if vary_by == "situation":
        trial_data["situation_params"] = situation_params
    return trial_data


def _build_outcome_response(
    agent: Individual,
    outcome_desc: str,
    scenario_context: str,
    vary_by: str,
    max_turns: int,
    all_trials: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the final response dict with correlations."""
    response_data: dict[str, Any] = {
        "mode": "outcome",
        "vary_by": vary_by,
        "scenario_context": scenario_context,
        "outcome_description": outcome_desc,
        "agent_name": agent.name,
        "trials": all_trials,
        "turns_per_trial": max_turns,
        "total_trials": len(all_trials),
    }

    if vary_by == "traits":
        response_data["trait_correlations"] = engine.compute_trait_correlations(all_trials)
    elif vary_by == "emotions":
        response_data["emotion_correlations"] = engine.compute_emotion_correlations(all_trials)
    elif vary_by == "situation":
        response_data["situation_correlations"] = engine.compute_situation_correlations(all_trials)

    return response_data


__all__ = ["bp"]

