"""Simulation business-logic layer.

All simulation-engine functionality lives here — LLM management, PDK
hydration, emotion radar computation, emotional dynamics, random persona
generation, prompt construction, LLM response generation, outcome
evaluation, and correlation analysis.  The companion ``simulations.py``
module contains only Flask route handlers that delegate to this engine.
"""

from __future__ import annotations

import json
import logging
import random
import re
from typing import Any

# ── PDK imports ──
from personaut.individuals import Individual, create_individual
from personaut.situations import Situation, create_situation
from personaut.types import Modality


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# LLM singleton (lazy-init once)
# ═══════════════════════════════════════════════════════════════════════════
_llm_instance: Any = None
_llm_checked: bool = False


def get_llm() -> Any:
    """Get the LLM model, or None if no provider is available."""
    global _llm_instance, _llm_checked
    if _llm_checked:
        return _llm_instance
    _llm_checked = True
    try:
        from personaut.models import get_llm as _models_get_llm

        _llm_instance = _models_get_llm()
        logger.info("Simulations: LLM provider detected: %s", getattr(_llm_instance, "model", "unknown"))
    except Exception as e:
        logger.info("Simulations: No LLM provider (%s) — using fallback", e)
        _llm_instance = None
    return _llm_instance


# ═══════════════════════════════════════════════════════════════════════════
# PDK hydration helpers
# ═══════════════════════════════════════════════════════════════════════════


def hydrate_individual(data: dict[str, Any]) -> Individual:
    """Convert API dict → PDK Individual."""
    name = data.get("name", "Character")
    traits_dict = data.get("trait_profile", {}) or {}
    emotions_dict = data.get("emotional_state", {}) or {}
    metadata = data.get("metadata", {}) or {}
    individual = create_individual(
        name=name,
        traits=traits_dict,
        emotional_state=emotions_dict,
        metadata=metadata,
    )
    individual.id = data.get("id", "")
    desc = data.get("description", "")
    if desc:
        individual.metadata["description"] = desc
    return individual


def hydrate_situation(data: dict[str, Any]) -> Situation:
    """Convert API dict → PDK Situation."""
    return create_situation(
        modality=data.get("modality", "in_person"),
        description=data.get("description", ""),
        location=data.get("location"),
        context=data.get("context", {}),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Emotion Radar computation (same categories as chat_engine)
# ═══════════════════════════════════════════════════════════════════════════

EMOTION_CATEGORIES: dict[str, list[str]] = {
    "Joy": ["excited", "sensual", "energetic", "cheerful", "creative", "hopeful"],
    "Powerful": ["proud", "respected", "appreciated", "important", "faithful", "satisfied"],
    "Peaceful": ["content", "thoughtful", "intimate", "loving", "trusting", "nurturing"],
    "Anger": ["hostile", "hurt", "angry", "selfish", "hateful", "critical"],
    "Sad": ["guilty", "ashamed", "depressed", "lonely", "bored", "apathetic"],
    "Fear": ["rejected", "confused", "submissive", "insecure", "anxious", "helpless"],
}

CATEGORY_COLORS: dict[str, str] = {
    "Joy": "#facc15",
    "Powerful": "#f97316",
    "Peaceful": "#34d399",
    "Anger": "#ef4444",
    "Sad": "#60a5fa",
    "Fear": "#a78bfa",
}


def compute_emotion_radar(emotions: dict[str, float]) -> dict[str, float]:
    """Compute 6-category max intensities for the radar chart."""
    result = {}
    for category, emotion_list in EMOTION_CATEGORIES.items():
        values = [emotions.get(e, 0.0) for e in emotion_list]
        active = [v for v in values if v > 0]
        result[category] = max(values) if active else 0.0
    return result


def get_emotion_radar_data(individual: Individual) -> dict[str, Any]:
    """Build radar data dict from a PDK Individual."""
    es = individual.get_emotional_state()
    emotions = es.to_dict() if es else {}
    radar = compute_emotion_radar(emotions)
    return {
        "categories": list(radar.keys()),
        "values": list(radar.values()),
        "emotions": {k: round(v, 3) for k, v in emotions.items() if v > 0},
    }


# ═══════════════════════════════════════════════════════════════════════════
# Emotional dynamics for simulations
# (mirrors the chat_engine pipeline: LLM analysis → decay → trait mod →
#  antagonism)
# ═══════════════════════════════════════════════════════════════════════════


def analyze_simulation_emotions(
    speaker: Individual,
    other_speakers: list[Individual],
    response_text: str,
    recent_history: list[dict[str, Any]],
) -> dict[str, float]:
    """Ask the LLM to analyze emotional shifts from a conversation exchange.

    Returns a dict of emotion→target_value representing what the speaker
    should now feel after their exchange. These raw values will be processed
    through the PDK emotional dynamics pipeline.
    """
    from personaut.emotions.emotion import ALL_EMOTIONS

    llm = get_llm()
    if llm is None:
        return {}

    # Current emotional state description
    es = speaker.get_emotional_state()
    current = es.to_dict() if es else {}
    active = {k: round(v, 2) for k, v in current.items() if v > 0}

    # Last few exchanges for context
    recent = recent_history[-4:] if len(recent_history) > 4 else recent_history
    context_lines = []
    for turn in recent:
        context_lines.append(f"{turn['speaker']}: {turn['content']}")
    context_lines.append(f"{speaker.name}: {response_text}")
    conversation_context = "\n".join(context_lines)

    # Trait context
    trait_dict = speaker.traits.to_dict() if speaker.traits else {}
    trait_summary = ""
    if trait_dict:
        high = [(t, v) for t, v in trait_dict.items() if v >= 0.7]
        low = [(t, v) for t, v in trait_dict.items() if v <= 0.3]
        parts = []
        if high:
            parts.append("High: " + ", ".join(f"{t} ({v:.1f})" for t, v in sorted(high, key=lambda x: -x[1])))
        if low:
            parts.append("Low: " + ", ".join(f"{t} ({v:.1f})" for t, v in sorted(low, key=lambda x: x[1])))
        if parts:
            trait_summary = " | ".join(parts)

    valid_emotions = ", ".join(ALL_EMOTIONS)

    prompt = f"""You are a psychological emotion analysis engine.

Character: {speaker.name}
{f"Personality: {trait_summary}" if trait_summary else ""}
Current emotions: {json.dumps(active) if active else "none active"}

Recent conversation:
{conversation_context}

Analyze how {speaker.name} feels NOW after this exchange. Consider:
1. How the conversation topic affects their emotions
2. Their personality traits shaping their reactions
3. Emotional contagion from other speakers
4. Natural emotional flow (emotions shift gradually, not randomly)

Provide COMPLETE updated emotional state with realistic values (0.0-1.0).
Include both updated existing emotions and any NEW emotions triggered.

Valid emotion names: {valid_emotions}

Respond with ONLY a JSON object:
{{"cheerful": 0.7, "excited": 0.5, "content": 0.6, "anxious": 0.1}}"""

    try:
        result = llm.generate(prompt, temperature=0.3, max_tokens=200)
        text = result.text.strip() if hasattr(result, "text") else str(result).strip()

        json_match = re.search(r"\{[^}]+\}", text)
        if not json_match:
            logger.debug("Sim emotion analysis: no JSON in: %s", text[:80])
            return {}

        emotions = json.loads(json_match.group())

        valid: dict[str, float] = {}
        for k, v in emotions.items():
            if k in ALL_EMOTIONS and isinstance(v, (int, float)):
                valid[k] = max(0.0, min(1.0, float(v)))

        if valid:
            logger.info("Sim emotion update for %s: %d emotions", speaker.name, len(valid))
        return valid

    except Exception as e:
        logger.debug("Sim emotion analysis failed: %s", e)
        return {}


def update_speaker_emotions(
    speaker: Individual,
    emotion_updates: dict[str, float],
) -> None:
    """Apply the full PDK emotional dynamics pipeline to a speaker.

    Steps (same as chat_engine):
    1. Decay — emotions fade between turns
    2. Trait-modulated change — personality shapes reaction strength
    3. Antagonistic suppression — contradictory emotions fight
    4. Mood baseline — repeated patterns shift resting state
    5. Persist back to the Individual object
    """
    emotional_state = speaker.get_emotional_state()
    if not emotional_state:
        return

    # Step 1: Natural decay
    emotional_state.decay(turns_elapsed=1)

    if emotion_updates:
        # Step 2: Trait-modulated application
        trait_dict = speaker.traits.to_dict() if speaker.traits else None
        emotional_state.apply_trait_modulated_change(
            emotion_updates,
            trait_profile=trait_dict,
        )

    # Step 3: Antagonistic suppression
    emotional_state.apply_antagonism(strength=0.3)

    # Step 4: Mood baseline adaptation
    emotional_state.update_mood_baseline(learning_rate=0.08)

    # Step 5: Persist back into the in-memory Individual
    final = emotional_state.to_dict()
    for emotion, value in final.items():
        try:
            speaker.set_emotion(emotion, value)
        except Exception as e:
            logger.debug("Skipping emotion %s: %s", emotion, e)


# ═══════════════════════════════════════════════════════════════════════════
# Random persona generation for outcome tracking
# ═══════════════════════════════════════════════════════════════════════════

_RANDOM_FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Maya",
    "Sam",
    "Jamie",
    "Casey",
    "Morgan",
    "Quinn",
    "Avery",
    "Riley",
    "Taylor",
    "Dakota",
    "Reese",
    "Skyler",
    "Drew",
    "Sage",
    "Blake",
    "Rowan",
    "Harper",
    "Emery",
    "Kai",
    "Logan",
    "Parker",
    "Ellis",
]
_RANDOM_LAST_NAMES = [
    "Rivera",
    "Chen",
    "Patel",
    "Kim",
    "Okafor",
    "Russo",
    "Nakamura",
    "Singh",
    "Torres",
    "Andersen",
    "Yusuf",
    "Volkov",
    "Dubois",
    "Park",
    "Ortega",
    "Shah",
]
_RANDOM_OCCUPATIONS = [
    "software engineer",
    "teacher",
    "nurse",
    "barista",
    "marketing manager",
    "graphic designer",
    "accountant",
    "freelance writer",
    "mechanic",
    "retail associate",
    "data analyst",
    "project manager",
    "student",
    "small business owner",
    "real estate agent",
    "HR specialist",
]
_RANDOM_STYLES = [
    "direct and matter-of-fact",
    "warm and chatty",
    "reserved and thoughtful",
    "enthusiastic and animated",
    "skeptical but polite",
    "casual and laid-back",
    "formal and precise",
    "friendly but guarded",
    "blunt with dry humor",
]


def generate_random_individual(
    idx: int,
    vary_by: str = "traits",
    fixed_traits: dict[str, float] | None = None,
    fixed_emotions: dict[str, float] | None = None,
) -> Individual:
    """Create a randomized Individual with controlled variation.

    Args:
        idx: Persona index for metadata.
        vary_by: Which dimension to randomize - 'traits', 'emotions', or 'situation'.
        fixed_traits: When vary_by != 'traits', use these fixed trait values.
        fixed_emotions: When vary_by != 'emotions', use these fixed emotion values.
    """
    from personaut.traits.trait import ALL_TRAITS

    name = f"{random.choice(_RANDOM_FIRST_NAMES)} {random.choice(_RANDOM_LAST_NAMES)}"
    occupation = random.choice(_RANDOM_OCCUPATIONS)
    style = random.choice(_RANDOM_STYLES)

    # --- Traits ---
    if vary_by == "traits" or fixed_traits is None:
        # Randomize traits: cluster some high, some low, rest mid-range
        traits: dict[str, float] = {}
        high_count = random.randint(3, 6)
        low_count = random.randint(2, 4)
        shuffled_traits = list(ALL_TRAITS)
        random.shuffle(shuffled_traits)
        for i, trait in enumerate(shuffled_traits):
            if i < high_count:
                traits[trait] = round(random.uniform(0.65, 0.95), 2)
            elif i < high_count + low_count:
                traits[trait] = round(random.uniform(0.1, 0.35), 2)
            else:
                traits[trait] = round(random.uniform(0.35, 0.65), 2)
    else:
        traits = dict(fixed_traits)

    # --- Emotions ---
    all_pos_emotions = ["cheerful", "content", "hopeful", "excited", "satisfied", "creative"]
    all_neg_emotions = ["anxious", "insecure", "lonely", "critical", "apathetic"]
    all_neutral_emotions = ["thoughtful", "trusting", "energetic"]

    if vary_by == "emotions":
        # Fully randomize emotions: pick 3-6 emotions from all pools
        all_emo_pool = all_pos_emotions + all_neg_emotions + all_neutral_emotions
        emo_count = random.randint(3, 6)
        emotions: dict[str, float] = {}
        for emo in random.sample(all_emo_pool, min(len(all_emo_pool), emo_count)):
            emotions[emo] = round(random.uniform(0.2, 0.85), 2)
    elif fixed_emotions is not None:
        emotions = dict(fixed_emotions)
    else:
        # Default: derive emotions from personality
        emotions = {}
        warmth = traits.get("warmth", 0.5)
        stability = traits.get("emotional_stability", 0.5)
        if warmth > 0.6 and stability > 0.5:
            pool = all_pos_emotions
        elif stability < 0.4:
            pool = all_neg_emotions + all_pos_emotions[:2]
        else:
            pool = all_neutral_emotions + all_pos_emotions[:2] + all_neg_emotions[:1]
        for emo in random.sample(pool, min(len(pool), random.randint(2, 4))):
            emotions[emo] = round(random.uniform(0.3, 0.75), 2)

    individual = create_individual(
        name=name,
        traits=traits,
        emotional_state=emotions,
        metadata={
            "occupation": occupation,
            "speaking_style": style,
            "persona_idx": idx,
        },
    )
    return individual


_RANDOM_LOCATIONS = [
    "coffee shop",
    "office lobby",
    "retail store",
    "trade show booth",
    "restaurant",
    "coworking space",
    "airport lounge",
    "hotel lobby",
    "phone (cold call)",
    "virtual meeting room",
    "outdoor market",
    "gym reception",
    "bookstore",
    "car dealership",
]

_RANDOM_MODALITIES = ["in_person", "text_message", "phone_call", "video_call", "email"]


def generate_random_situation() -> tuple[Situation, dict[str, Any]]:
    """Create a randomized Situation with varied modality and location."""
    modality = random.choice(_RANDOM_MODALITIES)
    location = random.choice(_RANDOM_LOCATIONS)
    sit = create_situation(
        modality=modality,
        description=f"A conversation at {location}",
        location=location,
    )
    params = {"modality": modality, "location": location}
    return sit, params


# ═══════════════════════════════════════════════════════════════════════════
# Outcome evaluation
# ═══════════════════════════════════════════════════════════════════════════


def evaluate_outcome(
    outcome_description: str,
    conversation_history: list[dict[str, Any]],
    speaker_name: str,
    individual: Individual,
) -> dict[str, Any]:
    """Use LLM to evaluate whether a target outcome was achieved."""
    llm = get_llm()
    if llm is None:
        return {"achieved": False, "confidence": 0.0, "reasoning": "No LLM available"}

    conv_text = "\n".join(f"{t['speaker']}: {t['content']}" for t in conversation_history)

    traits = individual.traits.to_dict() if individual.traits else {}
    high_traits = [(k, v) for k, v in sorted(traits.items(), key=lambda x: -x[1]) if v > 0.6]
    trait_desc = ", ".join(f"{k} ({v:.0%})" for k, v in high_traits[:5]) if high_traits else "balanced"

    prompt = f"""You are evaluating whether a target outcome was achieved in a conversation.

TARGET OUTCOME: {outcome_description}

The outcome is evaluated from the perspective of the first speaker (the agent/seller/host).
The customer/respondent is: {speaker_name} (personality: {trait_desc})

CONVERSATION:
{conv_text}

Analyze the conversation and determine:
1. Was the target outcome achieved? (yes/no)
2. How confident are you? (0.0-1.0)
3. Brief reasoning (1-2 sentences)

Respond with ONLY a JSON object:
{{"achieved": true, "confidence": 0.85, "reasoning": "The customer agreed to..."}}"""

    try:
        result = llm.generate(prompt, temperature=0.2, max_tokens=200)
        text = result.text.strip() if hasattr(result, "text") else str(result).strip()
        json_match = re.search(r"\{[^}]+\}", text)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "achieved": bool(parsed.get("achieved", False)),
                "confidence": float(parsed.get("confidence", 0.5)),
                "reasoning": str(parsed.get("reasoning", "")),
            }
    except Exception as e:
        logger.warning("Outcome evaluation failed: %s", e)

    return {"achieved": False, "confidence": 0.0, "reasoning": "Evaluation failed"}


# ═══════════════════════════════════════════════════════════════════════════
# Correlation analysis
# ═══════════════════════════════════════════════════════════════════════════


def compute_trait_correlations(
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze which personality traits correlate with outcome success."""
    from personaut.traits.trait import ALL_TRAITS

    success_traits: dict[str, list[float]] = {t: [] for t in ALL_TRAITS}
    failure_traits: dict[str, list[float]] = {t: [] for t in ALL_TRAITS}

    for trial in trials:
        traits = trial.get("customer_traits", {})
        achieved = trial.get("outcome", {}).get("achieved", False)
        bucket = success_traits if achieved else failure_traits
        for trait, value in traits.items():
            if trait in bucket:
                bucket[trait].append(value)

    correlations: dict[str, dict[str, Any]] = {}
    for trait in ALL_TRAITS:
        s_vals = success_traits[trait]
        f_vals = failure_traits[trait]
        s_avg = sum(s_vals) / len(s_vals) if s_vals else 0.5
        f_avg = sum(f_vals) / len(f_vals) if f_vals else 0.5
        diff = s_avg - f_avg

        if len(s_vals) + len(f_vals) < 2:
            continue

        correlations[trait] = {
            "success_avg": round(s_avg, 3),
            "failure_avg": round(f_avg, 3),
            "difference": round(diff, 3),
            "sample_size": len(s_vals) + len(f_vals),
        }

    # Sort by absolute difference
    sorted_corr = dict(sorted(correlations.items(), key=lambda x: abs(x[1]["difference"]), reverse=True))
    return sorted_corr


def compute_emotion_correlations(
    trials: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Compute correlation between customer emotions and outcome success."""
    success_trials = [t for t in trials if t.get("outcome", {}).get("achieved")]
    failure_trials = [t for t in trials if not t.get("outcome", {}).get("achieved")]

    if not success_trials or not failure_trials:
        return {}

    all_emotions: set[str] = set()
    for t in trials:
        all_emotions.update(t.get("customer_emotions", {}).keys())

    correlations: dict[str, dict[str, Any]] = {}
    for emo in all_emotions:
        s_vals = [t["customer_emotions"].get(emo, 0.0) for t in success_trials]
        f_vals = [t["customer_emotions"].get(emo, 0.0) for t in failure_trials]
        s_avg = sum(s_vals) / len(s_vals)
        f_avg = sum(f_vals) / len(f_vals)
        diff = s_avg - f_avg
        correlations[emo] = {
            "success_avg": round(s_avg, 3),
            "failure_avg": round(f_avg, 3),
            "difference": round(diff, 3),
            "sample_size": len(s_vals) + len(f_vals),
        }

    sorted_corr = dict(sorted(correlations.items(), key=lambda x: abs(x[1]["difference"]), reverse=True))
    return sorted_corr


def compute_situation_correlations(
    trials: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Compute correlation between situation parameters and outcome success."""
    if not trials:
        return {}

    # Group by each categorical parameter
    result: dict[str, dict[str, Any]] = {}
    for param in ("modality", "location"):
        values: dict[str, dict[str, Any]] = {}  # value -> {success: int, total: int}
        for t in trials:
            val = t.get("situation_params", {}).get(param, "unknown")
            if val not in values:
                values[val] = {"success": 0, "total": 0}
            values[val]["total"] += 1
            if t.get("outcome", {}).get("achieved"):
                values[val]["success"] += 1

        param_data: dict[str, Any] = {}
        for val, counts in sorted(values.items(), key=lambda x: -(x[1]["success"] / max(x[1]["total"], 1))):
            rate = counts["success"] / max(counts["total"], 1)
            param_data[val] = {
                "success_count": counts["success"],
                "total_count": counts["total"],
                "success_rate": round(rate, 3),
            }
        result[param] = param_data

    return result


# ═══════════════════════════════════════════════════════════════════════════
# LLM-powered generation helpers
# ═══════════════════════════════════════════════════════════════════════════


def build_conversation_prompt(
    individuals: list[Individual],
    situation: Situation,
    turn_number: int,
    speaker: Individual,
    history: list[dict[str, Any]],
) -> str:
    """Build a system prompt for conversation between individuals."""
    names = [ind.name for ind in individuals]
    other_names = [n for n in names if n != speaker.name]

    # Get speaker personality info
    traits = speaker.traits.to_dict() if speaker.traits else {}
    high_traits = [(k, v) for k, v in traits.items() if v > 0.6]
    emotions = speaker.get_emotional_state().to_dict() if speaker.get_emotional_state() else {}
    high_emotions = [(k, v) for k, v in emotions.items() if v > 0.3]
    metadata = speaker.metadata or {}

    parts = [
        f"You are {speaker.name}, participating in a conversation.",
        f"Situation: {situation.description or 'A casual conversation'}",
    ]

    if metadata.get("occupation"):
        parts.append(f"Occupation: {metadata['occupation']}")
    if metadata.get("description"):
        parts.append(f"Background: {metadata['description']}")
    if metadata.get("speaking_style"):
        parts.append(f"Speaking style: {metadata['speaking_style']}")
    if metadata.get("interests"):
        parts.append(f"Interests: {metadata['interests']}")

    if high_traits:
        trait_desc = ", ".join(f"{k} ({v:.0%})" for k, v in high_traits[:5])
        parts.append(f"Personality traits: {trait_desc}")
    if high_emotions:
        emo_desc = ", ".join(f"{k} ({v:.0%})" for k, v in high_emotions[:4])
        parts.append(f"Current emotional state: {emo_desc}")

    # Modality guidance
    modality = situation.modality if hasattr(situation, "modality") else Modality.IN_PERSON
    if modality == Modality.TEXT_MESSAGE:
        parts.append("This is a TEXT MESSAGE conversation. Write casually like texting.")
        parts.append("DO NOT include stage directions, actions, or narration.")
    elif modality == Modality.IN_PERSON:
        parts.append("This is an IN-PERSON conversation.")
        parts.append("You may include brief stage directions in [brackets](tone).")
    elif modality == Modality.PHONE_CALL:
        parts.append("This is a PHONE CALL. Include tone-of-voice cues in (parentheses).")

    parts.append(f"\nYou are talking with: {', '.join(other_names)}")
    parts.append("Respond naturally, in character. Keep responses to 1-3 sentences.")
    parts.append("Do NOT prefix your response with your name.")

    prompt = "\n".join(parts) + "\n\n--- Conversation ---\n"

    for entry in history:
        prompt += f"{entry['speaker']}: {entry['content']}\n"

    if not history:
        prompt += "(The conversation just started. You speak first.)\n"
    else:
        prompt += f"\n(It's your turn. Respond as {speaker.name}.)\n"

    prompt += f"\n{speaker.name}:"
    return prompt


def build_survey_prompt(
    individual: Individual,
    question: dict[str, Any],
    situation: Situation | None,
    *,
    has_image: bool = False,
    image_description: str = "",
) -> str:
    """Build a prompt for an individual to answer a survey question."""
    metadata = individual.metadata or {}
    traits = individual.traits.to_dict() if individual.traits else {}
    high_traits = [(k, v) for k, v in traits.items() if v > 0.6]
    emotions = individual.get_emotional_state().to_dict() if individual.get_emotional_state() else {}
    high_emotions = [(k, v) for k, v in emotions.items() if v > 0.3]

    parts = [
        f"You are {individual.name}.",
    ]
    if metadata.get("description"):
        parts.append(f"Background: {metadata['description']}")
    if metadata.get("occupation"):
        parts.append(f"Occupation: {metadata['occupation']}")
    if high_traits:
        trait_desc = ", ".join(f"{k} ({v:.0%})" for k, v in high_traits[:5])
        parts.append(f"Personality: {trait_desc}")
    if high_emotions:
        emo_desc = ", ".join(f"{k} ({v:.0%})" for k, v in high_emotions[:4])
        parts.append(f"Current mood: {emo_desc}")

    q_type = question.get("type", "open_ended")
    q_text = question.get("text", "")

    parts.append("\nYou are being asked to answer a survey question.")
    if situation:
        parts.append(f"Context: {situation.description}")

    # If an image is attached, instruct the model to examine it
    if has_image:
        parts.append(
            "\nAn image of a product has been provided for you to examine. "
            "Look carefully at the product shown in the image — its design, "
            "features, branding, packaging, and overall appearance."
        )
        if image_description:
            parts.append(f"Product description: {image_description}")
        parts.append(
            "Base your answer on your genuine reaction to this product as shown "
            "in the image, considering your personality, background, and current mood."
        )

    parts.append(f"\nQuestion: {q_text}")

    if q_type == "likert_5":
        parts.append("Answer on a scale of 1-5 (1=Strongly Disagree, 5=Strongly Agree).")
        parts.append("Format: First give your number rating, then a brief explanation in 1-2 sentences.")
    elif q_type == "likert_7":
        parts.append("Answer on a scale of 1-7 (1=Strongly Disagree, 7=Strongly Agree).")
        parts.append("Format: First give your number rating, then a brief explanation in 1-2 sentences.")
    elif q_type == "yes_no":
        parts.append("Answer Yes or No, then briefly explain why in 1-2 sentences.")
    elif q_type == "multiple_choice":
        options = question.get("options", [])
        parts.append(f"Choose from: {', '.join(options)}")
        parts.append("State your choice, then briefly explain why in 1-2 sentences.")
    else:
        parts.append("Answer thoughtfully in 2-4 sentences, staying in character.")

    parts.append("\nAnswer:")
    return "\n".join(parts)


def generate_llm_response(prompt: str, max_tokens: int = 200) -> str | None:
    """Generate a response using the LLM."""
    llm = get_llm()
    if llm is None:
        return None
    try:
        result = llm.generate(prompt, temperature=0.8, max_tokens=max_tokens)
        text = result.text.strip() if hasattr(result, "text") else str(result).strip()
        return text or None
    except Exception as e:
        logger.warning("LLM generation failed: %s", e)
        return None


def generate_llm_response_multimodal(
    prompt: str,
    image_base64: str | None = None,
    image_mime: str = "image/png",
    max_tokens: int = 300,
) -> str | None:
    """Generate a response using the LLM with optional image input."""
    llm = get_llm()
    if llm is None:
        return None
    try:
        # If no image, fall back to text-only
        if not image_base64:
            return generate_llm_response(prompt, max_tokens=max_tokens)

        # Build multimodal content parts for Gemini
        import base64

        from google.genai import types

        image_bytes = base64.b64decode(image_base64)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=image_mime)
        text_part = types.Part.from_text(text=prompt)

        client = llm._ensure_client()
        gen_config = types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=max_tokens,
        )
        response = client.models.generate_content(
            model=llm.model,
            contents=[text_part, image_part],
            config=gen_config,
        )
        text = response.text if hasattr(response, "text") else ""
        return text.strip() or None
    except Exception as e:
        logger.warning("Multimodal LLM generation failed: %s — falling back to text", e)
        # Fall back to text-only if multimodal fails
        return generate_llm_response(prompt, max_tokens=max_tokens)


def survey_fallback(individual: Individual, question: dict[str, Any]) -> str:
    """Simple fallback when LLM is unavailable for survey."""
    q_type = question.get("type", "open_ended")
    emotions = individual.get_emotional_state().to_dict() if individual.get_emotional_state() else {}

    # Calculate emotional positivity
    positive = {"cheerful", "content", "creative", "hopeful", "excited", "satisfied"}
    negative = {"anxious", "depressed", "angry", "lonely", "hostile"}
    pos_sum = sum(v for k, v in emotions.items() if k in positive)
    neg_sum = sum(v for k, v in emotions.items() if k in negative)
    positivity = (pos_sum - neg_sum) / max(pos_sum + neg_sum, 0.01)

    if q_type.startswith("likert"):
        max_val = 5 if q_type == "likert_5" else 7
        mid = (max_val + 1) / 2
        val = round(mid + positivity * (max_val - mid) * 0.5)
        val = max(1, min(max_val, val))
        return f"{val} — Based on my current perspective, I'd rate this moderately."
    elif q_type == "yes_no":
        return "Yes — I think so, overall." if positivity > 0 else "No — Not at this time."
    else:
        return "I have mixed feelings about this. Some aspects are positive, others could use improvement."
