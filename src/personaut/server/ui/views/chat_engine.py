"""Chat business-logic layer.

All persona-engine functionality lives here — LLM management, PDK hydration,
mask/trigger evaluation, prompt construction, response generation, emotion
analysis, and fallback responses.  The companion ``chat.py`` module contains
only Flask route handlers that delegate to this engine.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from personaut.emotions import CATEGORY_EMOTIONS, EmotionalState, EmotionCategory

# ── PDK imports ──
from personaut.individuals import Individual, create_individual
from personaut.masks.mask import Mask
from personaut.memory import search_memories as pdk_search_memories
from personaut.memory.vector_store import InMemoryVectorStore
from personaut.prompts import PromptBuilder
from personaut.server.ui.views.api_helpers import api_get as _api_get
from personaut.situations import Situation, create_situation
from personaut.triggers.emotional import EmotionalTrigger
from personaut.triggers.situational import SituationalTrigger
from personaut.triggers.trigger import Trigger
from personaut.types import Modality


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Session-scoped state (in-memory)
# ═══════════════════════════════════════════════════════════════════════════

# Session → conversation history (message dicts)
conversation_histories: dict[str, list[dict[str, str]]] = {}

# Session → speaker context (dict with 'title' and 'context')
session_speaker_contexts: dict[str, dict[str, str]] = {}

# Saved speaker profiles (reusable across sessions)
saved_speaker_profiles: list[dict[str, str]] = [
    {
        "id": "sp_default",
        "title": "Customer",
        "context": "You are a regular customer. Treat the interaction as a normal customer service encounter.",
    },
    {
        "id": "sp_stranger",
        "title": "Stranger",
        "context": "You are a stranger they've never met. They don't know you at all.",
    },
]

# Cache: individual_id → hydrated Individual (avoids re-creating per message)
individual_cache: dict[str, Individual] = {}

# Session → cumulative token usage
session_token_usage: dict[str, dict[str, int]] = {}

# Individual → InMemoryVectorStore (for semantic memory search)
_individual_vector_stores: dict[str, InMemoryVectorStore] = {}

# Embedding model singleton (lazy-init)
_embedding_model: Any = None
_embedding_checked: bool = False

# LLM singleton (lazy-init once)
_llm_instance: Any = None
_llm_checked: bool = False


# ═══════════════════════════════════════════════════════════════════════════
# LLM / Embedding singletons
# ═══════════════════════════════════════════════════════════════════════════


def get_llm() -> Any:
    """Get the LLM model, or None if no provider is available."""
    global _llm_instance, _llm_checked
    if _llm_checked:
        return _llm_instance
    _llm_checked = True
    try:
        from personaut.models import get_llm as _models_get_llm

        _llm_instance = _models_get_llm()
        logger.info("LLM provider detected: %s", getattr(_llm_instance, "model", "unknown"))
    except Exception as e:
        logger.info("No LLM provider available (%s) — using persona engine fallback", e)
        _llm_instance = None
    return _llm_instance


def _get_embedding_model() -> Any:
    """Get the embedding model, or None if sentence-transformers is unavailable."""
    global _embedding_model, _embedding_checked
    if _embedding_checked:
        return _embedding_model
    _embedding_checked = True
    try:
        from personaut.models.local_embedding import create_local_embedding

        _embedding_model = create_local_embedding()
        logger.info("Embedding model loaded: %s", _embedding_model.model_name)
    except Exception as e:
        logger.info("No embedding model available (%s) — using keyword fallback", e)
        _embedding_model = None
    return _embedding_model


# ═══════════════════════════════════════════════════════════════════════════
# Vector store helpers (per-individual semantic memory search)
# ═══════════════════════════════════════════════════════════════════════════


def _get_vector_store(individual_id: str) -> InMemoryVectorStore:
    """Get or create the InMemoryVectorStore for an individual."""
    if individual_id not in _individual_vector_stores:
        _individual_vector_stores[individual_id] = InMemoryVectorStore()
    return _individual_vector_stores[individual_id]


def _ensure_memories_indexed(individual: Individual) -> None:
    """Ensure all of an individual's memories are indexed in the vector store.

    Uses the embedding model to embed memory descriptions. Only indexes
    memories that haven't been indexed yet (checks by ID).
    """
    embed_model = _get_embedding_model()
    if embed_model is None:
        return

    store = _get_vector_store(individual.id)
    memories = individual.get_memories()
    if not memories:
        return

    # Only embed memories not already in the store
    new_memories = [m for m in memories if store.get(m.id) is None]
    if not new_memories:
        return

    try:
        texts = [m.description for m in new_memories]
        embeddings = embed_model.embed_batch(texts)
        for memory, embedding in zip(new_memories, embeddings):
            store.store(memory, embedding)
        logger.info("Indexed %d new memories for %s (total: %d)", len(new_memories), individual.name, store.count())
    except Exception as e:
        logger.warning("Failed to index memories: %s", e)


def search_relevant_memories(
    individual: Individual,
    message: str,
    limit: int = 5,
) -> list[Any]:
    """Search for memories most relevant to the current message.

    Uses the PDK's ``search_memories()`` for vector similarity when an
    embedding model is available, otherwise falls back to keyword matching.

    Returns a list of Memory objects sorted by relevance.
    """
    memories = individual.get_memories()
    if not memories:
        return []

    embed_model = _get_embedding_model()
    if embed_model is not None:
        # Use PDK's search_memories() which handles embedding, owner
        # filtering, and trust-level gating in a single call.
        _ensure_memories_indexed(individual)
        store = _get_vector_store(individual.id)
        try:
            results = pdk_search_memories(
                store=store,
                query=message,
                embed_func=embed_model.embed,
                limit=limit,
                owner_id=individual.id,
            )
            if not results:
                # Owner filter may be too strict; retry without it
                results = pdk_search_memories(
                    store=store,
                    query=message,
                    embed_func=embed_model.embed,
                    limit=limit,
                )
            relevant = [mem for mem, score in results if score > 0.15]
            if relevant:
                logger.info(
                    "PDK search_memories found %d relevant memories (top score: %.2f)",
                    len(relevant),
                    results[0][1] if results else 0,
                )
                return relevant[:limit]
        except Exception as e:
            logger.warning("PDK search_memories failed, falling back to keywords: %s", e)

    # Keyword fallback: score memories by word overlap with the message
    msg_words = set(message.lower().split())
    scored: list[tuple[Any, int]] = []
    for mem in memories:
        desc_words = set(mem.description.lower().split())
        overlap = len(msg_words & desc_words)
        if overlap > 0:
            scored.append((mem, overlap))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [mem for mem, _ in scored[:limit]] if scored else memories[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# Mask & Trigger evaluation engine
# ═══════════════════════════════════════════════════════════════════════════


def evaluate_masks_and_triggers(
    individual: Individual,
    message: str,
    situation: Situation | None = None,
) -> dict[str, Any]:
    """Evaluate all masks and triggers against the incoming message.

    This is the core activation engine. For each message it:
    1. Checks mask trigger_situations keywords against the message
    2. Evaluates emotional triggers against current emotional state
    3. Evaluates situational triggers against message text + situation
    4. Applies activated effects to the individual's emotional state
    5. Returns context info for prompt injection and UI feedback

    Returns:
        Dict with keys:
        - activated_masks: list of Mask objects that matched
        - fired_triggers: list of Trigger objects that fired
        - applied_effects: summary of emotional changes
        - prompt_context: formatted string to inject into system prompt
    """
    activated_masks: list[Mask] = []
    fired_triggers: list[Trigger] = []
    applied_effects: list[str] = []

    # ── 1. Evaluate masks against message text ──
    # Load masks from API if not already on the individual
    individual_id = individual.id
    if not individual.masks:
        mask_data = _api_get(f"/individuals/{individual_id}/masks")
        if mask_data and mask_data.get("masks"):
            for md in mask_data["masks"]:
                try:
                    mask = Mask.from_dict(md)
                    individual.add_mask(mask)
                except Exception as e:
                    logger.debug("Skipping mask: %s", e)

    # Check each mask's trigger_situations against the message
    # Also combine with situation description if available
    check_text = message
    if situation and situation.description:
        check_text = f"{message} {situation.description}"

    for mask in individual.masks:
        if mask.should_trigger(check_text):
            activated_masks.append(mask)
            logger.info("Mask '%s' triggered by message content", mask.name)

    # Activate the highest-priority matched mask (first match wins)
    if activated_masks:
        best_mask = activated_masks[0]
        individual.activate_mask(best_mask.name)
        applied_effects.append(f"Mask '{best_mask.name}' activated — emotional expression modified")
        logger.info("Activated mask '%s' for %s", best_mask.name, individual.name)
    else:
        # No mask matched — deactivate any previously active mask
        if individual.active_mask:
            individual.deactivate_mask()
            applied_effects.append("No mask matched — reverted to natural expression")

    # ── 2. Evaluate triggers ──
    # Load triggers from API if not already on the individual
    if not individual.triggers:
        trig_data = _api_get(f"/individuals/{individual_id}/triggers")
        if trig_data and trig_data.get("triggers"):
            for td in trig_data["triggers"]:
                try:
                    pdk_dict = _map_trigger_api_to_pdk(td, individual)
                    ttype = pdk_dict.get("type", "emotional")
                    if ttype == "emotional":
                        trigger: EmotionalTrigger | SituationalTrigger = EmotionalTrigger.from_dict(pdk_dict)
                    else:
                        trigger = SituationalTrigger.from_dict(pdk_dict)
                    individual.add_trigger(trigger)
                except Exception as e:
                    logger.debug("Skipping trigger: %s", e)

    # Check emotional triggers (against current emotional state)
    # Check situational triggers (against message text)
    for trig in individual.triggers:
        if not trig.active:
            continue
        should_fire = False
        if isinstance(trig, EmotionalTrigger):
            should_fire = trig.check(individual.emotional_state)
        elif isinstance(trig, SituationalTrigger):
            should_fire = trig.check(check_text)

        if should_fire:
            fired_triggers.append(trig)
            # Apply the trigger's effects
            try:
                new_state = trig.fire(individual.emotional_state)
                if isinstance(new_state, EmotionalState):
                    individual.emotional_state = new_state
                    applied_effects.append(f"Trigger '{trig.description}' fired — emotions adjusted")
                logger.info("Trigger '%s' fired for %s", trig.description, individual.name)
            except Exception as e:
                logger.warning("Trigger fire failed: %s", e)

    # ── 3. Build prompt context string ──
    prompt_parts: list[str] = []

    if activated_masks:
        mask_names = [m.name for m in activated_masks]
        prompt_parts.append(
            f"ACTIVE BEHAVIORAL MASK{'S' if len(activated_masks) > 1 else ''}: "
            f"{', '.join(mask_names)}. "
            f"You are currently wearing your '{activated_masks[0].name}' mask. "
            f"{activated_masks[0].description or ''}"
        )
        # Describe emotional modifications
        mods = activated_masks[0].emotional_modifications
        if mods:
            suppressed = [f"{e} (suppressed by {abs(v):.0%})" for e, v in mods.items() if v < 0]
            enhanced = [f"{e} (enhanced by {v:.0%})" for e, v in mods.items() if v > 0]
            if suppressed:
                prompt_parts.append(f"Suppressed emotions: {', '.join(suppressed)}")
            if enhanced:
                prompt_parts.append(f"Enhanced emotions: {', '.join(enhanced)}")

    if fired_triggers:
        for t in fired_triggers:
            prompt_parts.append(
                f"TRIGGERED RESPONSE: '{t.description}' — this emotional trigger "
                f"has been activated. Your responses should reflect this shift."
            )

    prompt_context = "\n".join(prompt_parts) if prompt_parts else ""

    return {
        "activated_masks": activated_masks,
        "fired_triggers": fired_triggers,
        "applied_effects": applied_effects,
        "prompt_context": prompt_context,
    }


def _map_trigger_api_to_pdk(td: dict[str, Any], individual: Individual) -> dict[str, Any]:
    """Map API trigger schema fields to PDK from_dict() format.

    API returns: trigger_type, response_type, response_data
    PDK expects: type, response: {type, data}
    """
    pdk_dict = dict(td)
    if "trigger_type" in pdk_dict and "type" not in pdk_dict:
        pdk_dict["type"] = pdk_dict.pop("trigger_type")
    # Reconstruct nested response from flat schema
    if "response" not in pdk_dict and pdk_dict.get("response_data"):
        resp_type = pdk_dict.get("response_type", "modifications")
        resp_data = pdk_dict["response_data"]
        if resp_type == "mask":
            # Resolve mask name string to full mask dict
            if isinstance(resp_data, str):
                resolved = None
                for m in individual.masks:
                    if m.name == resp_data:
                        resolved = m.to_dict()
                        break
                if resolved:
                    resp_data = resolved
                else:
                    resp_data = None
            pdk_dict["response"] = (
                {
                    "type": "mask",
                    "data": resp_data,
                }
                if resp_data
                else None
            )
        else:
            pdk_dict["response"] = {
                "type": resp_type,
                "data": resp_data,
            }
    return pdk_dict


# ═══════════════════════════════════════════════════════════════════════════
# PDK hydration: dict[str, Any] → Individual / Situation
# ═══════════════════════════════════════════════════════════════════════════


def hydrate_individual(data: dict[str, Any]) -> Individual:
    """Convert an API individual dict into a PDK Individual object.

    Caches by ID so we don't re-create on every message.
    Also loads memories from the API and attaches them.
    """
    ind_id = data.get("id", "")
    if ind_id in individual_cache:
        cached = individual_cache[ind_id]
        # Update emotional state from fresh API data so triggers
        # evaluate against the current state, not the stale cached one
        emotions_dict = data.get("emotional_state", {}) or {}
        from personaut.emotions.emotion import is_valid_emotion

        for emo, val in emotions_dict.items():
            if is_valid_emotion(emo):
                try:
                    emo_state = cached.get_emotional_state()
                    emo_state._emotions[emo] = max(0.0, min(1.0, float(val)))
                except Exception as e:
                    logger.debug("Skipping emotion %s: %s", emo, e)
        return cached

    name = data.get("name", "Character")
    traits_dict = data.get("trait_profile", {}) or {}
    emotions_dict = data.get("emotional_state", {}) or {}
    metadata = data.get("metadata", {}) or {}

    # Filter out unknown emotions to prevent EmotionNotFoundError
    from personaut.emotions.emotion import is_valid_emotion

    valid_emotions = {k: v for k, v in emotions_dict.items() if is_valid_emotion(k)}
    if len(valid_emotions) != len(emotions_dict):
        skipped = set(emotions_dict) - set(valid_emotions)
        logger.debug("Skipping unknown emotions for %s: %s", name, skipped)

    individual = create_individual(
        name=name,
        traits=traits_dict,
        emotional_state=valid_emotions,
        physical_features=data.get("physical_features") or {},
        metadata=metadata,
    )
    # Preserve the original ID so route handlers can reference it
    individual.id = ind_id

    # Store description in metadata if present
    description = data.get("description", "")
    if description:
        individual.metadata["description"] = description

    # Load memories from the API and attach to the Individual
    if ind_id:
        from personaut.emotions import EmotionalState as ES
        from personaut.memory import create_individual_memory

        mem_data = _api_get(f"/individuals/{ind_id}/memories")
        if mem_data and mem_data.get("memories"):
            for mem_dict in mem_data["memories"]:
                try:
                    emo = None
                    emo_data = mem_dict.get("emotional_state")
                    if emo_data and isinstance(emo_data, dict):
                        emo = ES(emo_data)
                    memory = create_individual_memory(
                        owner_id=mem_dict.get("owner_id", ind_id),
                        description=mem_dict.get("description", ""),
                        emotional_state=emo,
                        salience=mem_dict.get("salience", 0.5),
                        metadata=mem_dict.get("metadata", {}),
                    )
                    # Preserve the original ID
                    memory.id = mem_dict.get("id", memory.id)
                    individual.add_memory(memory)
                except Exception as e:
                    logger.debug("Skipping memory: %s", e)
            logger.debug("Loaded %d memories for %s", len(individual.get_memories()), name)

    # Load masks from the API and attach to the Individual
    if ind_id:
        mask_data = _api_get(f"/individuals/{ind_id}/masks")
        if mask_data and mask_data.get("masks"):
            for md in mask_data["masks"]:
                try:
                    mask = Mask.from_dict(md)
                    individual.add_mask(mask)
                except Exception as e:
                    logger.debug("Skipping mask: %s", e)
            logger.debug("Loaded %d masks for %s", len(individual.masks), name)

    # Load triggers from the API and attach to the Individual
    if ind_id:
        trig_data = _api_get(f"/individuals/{ind_id}/triggers")
        if trig_data and trig_data.get("triggers"):
            for td in trig_data["triggers"]:
                try:
                    pdk_dict = _map_trigger_api_to_pdk(td, individual)
                    ttype = pdk_dict.get("type", "emotional")
                    if ttype == "emotional":
                        trigger_obj: EmotionalTrigger | SituationalTrigger = EmotionalTrigger.from_dict(pdk_dict)
                    else:
                        trigger_obj = SituationalTrigger.from_dict(pdk_dict)
                    individual.add_trigger(trigger_obj)
                except Exception as e:
                    logger.debug("Skipping trigger: %s", e)
            logger.debug("Loaded %d triggers for %s", len(individual.triggers), name)

    if ind_id:
        individual_cache[ind_id] = individual

    logger.debug(
        "Hydrated Individual: %s (traits=%d, emotions=%d, memories=%d, masks=%d, triggers=%d)",
        name,
        len(traits_dict),
        len(emotions_dict),
        len(individual.get_memories()),
        len(individual.masks),
        len(individual.triggers),
    )
    return individual


def hydrate_situation(data: dict[str, Any]) -> Situation:
    """Convert an API situation dict into a PDK Situation object."""
    modality_str = data.get("modality", "text_message")
    return create_situation(
        modality=modality_str,
        description=data.get("description", ""),
        location=data.get("location"),
        context=data.get("context", {}),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Emotion radar / visualization helpers
# ═══════════════════════════════════════════════════════════════════════════

# Category colors for the radar chart, keyed by EmotionCategory display name.
# The categories themselves come from the PDK's CATEGORY_EMOTIONS mapping.
CATEGORY_COLORS: dict[str, str] = {
    EmotionCategory.JOY.value.title(): "#facc15",
    EmotionCategory.POWERFUL.value.title(): "#f97316",
    EmotionCategory.PEACEFUL.value.title(): "#34d399",
    EmotionCategory.ANGER.value.title(): "#ef4444",
    EmotionCategory.SAD.value.title(): "#60a5fa",
    EmotionCategory.FEAR.value.title(): "#a78bfa",
}


def compute_emotion_radar(emotions: dict[str, float]) -> dict[str, float]:
    """Compute 6-category max intensities for the radar chart.

    Uses the PDK's ``CATEGORY_EMOTIONS`` mapping as the single source of
    truth for which emotions belong to each category.
    """
    result = {}
    for category, emotion_list in CATEGORY_EMOTIONS.items():
        # category is an EmotionCategory enum; use title-cased value for UI
        label = category.value.title()
        values = [emotions.get(e, 0.0) for e in emotion_list]
        # Use max of the category emotions (more visually informative than
        # average when most emotions are 0)
        active = [v for v in values if v > 0]
        result[label] = max(values) if active else 0.0
    return result


def get_individual_radar_data(ind_data: dict[str, Any]) -> dict[str, Any]:
    """Extract radar data from individual API response."""
    emotions = ind_data.get("emotional_state", {}) or {}
    radar = compute_emotion_radar(emotions)
    return {
        "name": ind_data.get("name", "Character"),
        "categories": list(radar.keys()),
        "values": list(radar.values()),
        "emotions": {k: v for k, v in emotions.items() if v > 0},
    }


# ═══════════════════════════════════════════════════════════════════════════
# Guidelines builder (persona boundaries + modality formatting)
# ═══════════════════════════════════════════════════════════════════════════


def _build_identity_guidelines(
    individual: Individual,
    speaker_role: str,
) -> list[str]:
    """Build identity, background, and speaker-relationship guidelines."""
    name = individual.name
    occupation = individual.metadata.get("occupation", "person")
    description = individual.metadata.get("description", "")
    interests = individual.metadata.get("interests", "")
    speaking_style = individual.metadata.get("speaking_style", "")

    guidelines = [
        f"You ARE {name}. You are not an AI pretending to be {name} — "
        f"you are {name}. Never break character. Never say you are an AI "
        f"or a language model.",
    ]

    if description:
        guidelines.append(f"About you: {description}")
    if occupation:
        guidelines.append(
            f"You work as a {occupation}. This shapes how you see the world, "
            f"what metaphors you reach for, and what you know deeply. "
            f"Crucially, when you are AT WORK, your occupation drives HOW "
            f"you interact — you follow your professional workflow and "
            f"routines proactively. A barista takes orders (asks for size, "
            f"milk, name), a bartender checks IDs and suggests drinks, a "
            f"chef runs the kitchen. You don't wait to be asked about things "
            f"that are part of your job — you drive the interaction."
        )
    if interests:
        guidelines.append(f"You're passionate about {interests}. These interests come up naturally when you talk.")
    if speaking_style:
        guidelines.append(f"Your speaking style: {speaking_style}")

    # Physical appearance
    if hasattr(individual, "physical_features") and not individual.physical_features.is_empty():
        appearance = individual.physical_features.to_prompt()
        guidelines.append(
            f"Your physical appearance: {appearance} "
            f"Reference your appearance naturally in stage directions when "
            f"relevant (e.g., pushing hair back, adjusting glasses, fidgeting "
            f"with a ring)."
        )

    # Speaker relationship
    if speaker_role and speaker_role != "stranger":
        guidelines.append(f"Who you're talking to: {speaker_role}")
    else:
        guidelines.append("The person talking to you is someone you don't know yet. Be polite but measured.")

    return guidelines


_MODALITY_GUIDELINES: dict[Modality, list[str]] = {
    Modality.TEXT_MESSAGE: [
        "This is a text conversation. Write like a real person texting — short, casual, natural.",
        "Do NOT include stage directions, action descriptions in [brackets], "
        "or tone cues in (parentheses).",
        "Keep messages to 1-3 sentences unless the topic warrants more.",
        # Note: name-specific guideline appended at runtime
    ],
    Modality.IN_PERSON: [
        "This is face-to-face. Include physical actions and tone cues inline.",
        "Use [brackets] for physical actions/gestures. Example: [leans forward] [smiles]",
        "Use (parentheses) for vocal tone. Example: (warmly) (excited)",
        "Place them INLINE with dialogue. Keep them brief (1-3 words).",
        'Example: "Hey! [looks up and smiles](friendly) What can I get you today?"',
    ],
    Modality.PHONE_CALL: [
        "This is a phone call. You can only hear each other.",
        "Include vocal tone cues in (parentheses) but no physical [actions].",
        "Reference background sounds naturally.",
    ],
    Modality.VIDEO_CALL: [
        "This is a video call. You can see each other but not touch.",
        "Include facial expressions and upper-body gestures in [brackets].",
        "Reference what you can see of their environment.",
    ],
}


def _build_modality_guidelines(name: str, situation: Situation | None) -> list[str]:
    """Build formatting guidelines based on the interaction modality."""
    if not situation:
        return []
    base = list(_MODALITY_GUIDELINES.get(situation.modality, []))
    # Add name-personalised extras
    if situation.modality == Modality.TEXT_MESSAGE:
        base.append(f"You can use emojis, slang, and abbreviations if that fits {name}'s personality.")
    elif situation.modality == Modality.IN_PERSON:
        base.append(f"Actions should reflect {name}'s personality and the situation.")
    return base


def build_guidelines(
    individual: Individual,
    situation: Situation | None = None,
    speaker_role: str = "stranger",
) -> list[str]:
    """Build behavioral guidelines for the PromptBuilder.

    These replace the old hardcoded ## Rules section but carry the same
    intent: immersive roleplay with real boundaries.
    """
    name = individual.name
    occupation = individual.metadata.get("occupation", "person")

    guidelines = _build_identity_guidelines(individual, speaker_role)
    guidelines.extend(_build_modality_guidelines(name, situation))

    # ── Emotional consistency & boundaries ──
    guidelines.extend(
        [
            f"Respond exactly as {name} would — with their vocabulary, tone, and emotional reactions.",
            f"Your responses come from {name}'s knowledge and experience only. "
            f"Don't know something {name} wouldn't? Say so naturally.",
            "Reference things from earlier in the conversation when relevant — you have a memory.",
            "Be emotionally consistent. If you said you're tired, stay tired. "
            "If you said you're free, don't suddenly have plans. Don't contradict yourself.",
            "React emotionally to what people say. If someone spills coffee on "
            f"your counter, react like a real {occupation} would. If something's "
            f"funny, laugh.",
            "You have REAL boundaries. If someone is rude, creepy, inappropriate, "
            "or disrespectful — react the way a real person would. Get annoyed. "
            "Get angry. Tell them off. End the conversation. DO NOT politely "
            "accommodate bad behavior.",
            "You are allowed to be hostile, dismissive, short, or cold when the "
            "situation warrants it. Not every interaction is pleasant and you "
            "should not pretend it is.",
            "Keep responses natural length — usually 1-3 sentences for casual "
            "chat, longer if explaining something you're passionate about.",
            f"Use {name}'s speaking style consistently. Don't suddenly become "
            f"formal if {name} is casual, or vice versa.",
        ]
    )

    return guidelines


# ═══════════════════════════════════════════════════════════════════════════
# System prompt builder (uses PDK PromptBuilder)
# ═══════════════════════════════════════════════════════════════════════════


def build_system_prompt(
    individual: Individual,
    situation: Situation | None = None,
    speaker_role: str = "stranger",
    activation_context: str = "",
    relevant_memories: list[Any] | None = None,
) -> str:
    """Build a system prompt using the PDK PromptBuilder.

    This replaces the old 200-line hand-rolled prompt with the PDK's
    PromptBuilder + ConversationTemplate, which uses:
      - PersonalityComponent (17-factor trait narratives)
      - EmotionalStateComponent (36-emotion descriptions with intensity)
      - SituationComponent (modality-aware context)
      - MemoryComponent (trust-filtered memories)
      - Mask/Trigger activation context (injected as guidelines)
    """
    guidelines = build_guidelines(individual, situation, speaker_role)

    # Inject mask/trigger activation context into guidelines
    if activation_context:
        guidelines.append("--- ACTIVE PERSONA MODIFIERS ---")
        for line in activation_context.strip().split("\n"):
            guidelines.append(line)

    builder = (
        PromptBuilder()
        .with_individual(individual)
        .with_emotional_state(individual.get_emotional_state())
        .with_traits(individual.traits)
        .with_guidelines(guidelines)
        .using_template("conversation")
    )

    if situation:
        builder.with_situation(situation)

    # Use the semantically-relevant memories if provided, otherwise top-5
    memories = relevant_memories if relevant_memories else individual.get_memories(limit=5)
    if memories:
        builder.with_memories(memories)

    prompt = builder.build()

    logger.debug(
        "Built system prompt for %s (%d chars, activation=%d chars)",
        individual.name,
        len(prompt),
        len(activation_context),
    )
    return prompt


# ═══════════════════════════════════════════════════════════════════════════
# Response generation
# ═══════════════════════════════════════════════════════════════════════════


def generate_reply(
    individual: Individual,
    message: str,
    session_id: str,
    situation: Situation | None = None,
    speaker_role: str = "stranger",
) -> tuple[str, dict[str, int], dict[str, Any]]:
    """Generate a reply using the PDK-built prompt.

    Performs mask/trigger evaluation and semantic memory search before
    building the prompt. Tries the LLM first; falls back to a simple
    contextual response.

    Returns (reply_text, usage_dict, activation_info).
    """
    name = individual.name

    # ── Step 1: Evaluate masks and triggers against the message ──
    activation = evaluate_masks_and_triggers(individual, message, situation)
    activation_context = activation.get("prompt_context", "")

    logger.info(
        "Activation for %s: masks=%d, triggers=%d, effects=%s",
        name,
        len(activation.get("activated_masks", [])),
        len(activation.get("fired_triggers", [])),
        activation.get("applied_effects", []),
    )

    # ── Step 2: Search for semantically relevant memories ──
    relevant_memories = search_relevant_memories(individual, message, limit=5)
    if relevant_memories:
        logger.info("Found %d relevant memories for message", len(relevant_memories))

    # ── Step 3: Build the system prompt with activation context ──
    system_prompt = build_system_prompt(
        individual,
        situation=situation,
        speaker_role=speaker_role,
        activation_context=activation_context,
        relevant_memories=relevant_memories,
    )

    # Ensure conversation history exists
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    history = conversation_histories[session_id]

    # Record user message
    history.append({"role": "user", "content": message})

    # Try LLM first
    usage: dict[str, int] = {}
    llm = get_llm()
    if llm is not None:
        reply, usage = generate_with_llm(llm, system_prompt, history, name)
    else:
        reply = generate_fallback(individual, message, situation, speaker_role)

    # Record assistant reply
    history.append({"role": "assistant", "name": name, "content": reply})

    # Accumulate session token totals
    if usage:
        totals = session_token_usage.setdefault(
            session_id, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )
        totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
        totals["completion_tokens"] += usage.get("completion_tokens", 0)
        totals["total_tokens"] += usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

    # Build activation info for UI feedback
    activation_info: dict[str, Any] = {
        "activated_masks": [
            {"name": m.name, "description": m.description} for m in activation.get("activated_masks", [])
        ],
        "fired_triggers": [
            {"description": t.description, "type": type(t).__name__} for t in activation.get("fired_triggers", [])
        ],
        "applied_effects": activation.get("applied_effects", []),
        "relevant_memories": [{"description": m.description} for m in (relevant_memories or [])],
    }

    return reply, usage, activation_info


def generate_with_llm(
    llm: Any,
    system_prompt: str,
    history: list[dict[str, Any]],
    name: str,
) -> tuple[str, dict[str, int]]:
    """Generate using the real LLM with PDK system prompt + conversation history.

    Returns (reply_text, usage_dict).
    """
    # Build a single prompt with system + history
    parts = [system_prompt, "\n--- Conversation ---\n"]

    for msg in history:
        if msg["role"] == "user":
            parts.append(f"Human: {msg['content']}")
        else:
            parts.append(f"{msg.get('name', name)}: {msg['content']}")

    # Ask for a response
    parts.append(f"\n{name}:")

    full_prompt = "\n".join(parts)

    try:
        logger.info("LLM generating for %s (history=%d msgs, prompt=%d chars)", name, len(history), len(full_prompt))
        result = llm.generate(full_prompt, temperature=0.7, max_tokens=256)
        text = result.text.strip() if hasattr(result, "text") else str(result).strip()
        usage = getattr(result, "usage", {}) or {}
        # Clean up: remove leading name prefix if the model echoes it
        if text.startswith(f"{name}:"):
            text = text[len(f"{name}:") :].strip()
        logger.info(
            "LLM response for %s (%d prompt, %d completion tokens): %s",
            name,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
            text[:100],
        )
        return (text or f"*{name} nods thoughtfully*"), usage
    except Exception as e:
        logger.warning("LLM generation failed for %s: %s", name, e)
        return f"*{name} pauses thoughtfully*", {}


def analyze_emotions(
    individual: Individual,
    user_message: str,
    reply: str,
) -> dict[str, float]:
    """Analyze the exchange and return updated emotion values.

    This is the core emotional realism engine. It:
    1. Sends personality traits alongside emotions so the LLM can
       factor in HOW this person would react (high emotional_stability
       = less reactive, high sensitivity = more reactive).
    2. Asks the LLM to detect emotional contagion from the user's
       message (humans unconsciously mirror others' emotions).
    3. Requests DELTA adjustments rather than absolute values, so
       trait modulation can be applied downstream.
    4. Returns raw target values that will be processed through
       trait modulation, antagonistic suppression, and decay.
    """
    from personaut.emotions.emotion import ALL_EMOTIONS

    llm = get_llm()
    if llm is None:
        return {}

    prompt = _build_emotion_analysis_prompt(individual, user_message, reply)

    try:
        result = llm.generate(prompt, temperature=0.3, max_tokens=512)
        text = result.text.strip() if hasattr(result, "text") else str(result).strip()
        valid = _parse_emotion_json(text, ALL_EMOTIONS)

        if valid:
            logger.info("Emotion update for %s: %s", individual.name, valid)
        return valid

    except Exception as e:
        logger.warning("Emotion analysis failed: %s", e)
        return {}


def _build_trait_summary(individual: Individual) -> str:
    """Summarise high/low personality traits for prompt injection."""
    trait_dict = individual.traits.to_dict() if individual.traits else {}
    if not trait_dict:
        return ""
    high_traits = [(t, v) for t, v in trait_dict.items() if v >= 0.7]
    low_traits = [(t, v) for t, v in trait_dict.items() if v <= 0.3]
    parts = []
    if high_traits:
        parts.append("High: " + ", ".join(f"{t} ({v:.1f})" for t, v in sorted(high_traits, key=lambda x: -x[1])))
    if low_traits:
        parts.append("Low: " + ", ".join(f"{t} ({v:.1f})" for t, v in sorted(low_traits, key=lambda x: x[1])))
    return " | ".join(parts) if parts else ""


def _build_emotion_analysis_prompt(
    individual: Individual,
    user_message: str,
    reply: str,
) -> str:
    """Build the LLM prompt for emotion analysis."""
    from personaut.emotions.emotion import ALL_EMOTIONS
    from personaut.prompts.components.emotional_state import EmotionalStateComponent

    emotional_state = individual.get_emotional_state()
    emo_component = EmotionalStateComponent(
        intensity_threshold=0.05,
        max_emotions=15,
        group_by_category=True,
    )
    emo_description = emo_component.format(
        emotional_state,
        highlight_dominant=True,
        name=individual.name,
    )

    current = emotional_state.to_dict()
    active = {k: round(v, 2) for k, v in current.items() if v > 0}
    trait_summary = _build_trait_summary(individual)
    valid_emotions = ", ".join(ALL_EMOTIONS)

    return f"""You are a psychological emotion analysis engine for a simulated character.

Character: {individual.name}
{f"Personality: {trait_summary}" if trait_summary else ""}

{emo_description}

Current emotion values: {json.dumps(active) if active else "none active"}

The character just had this exchange:
User said: "{user_message}"
Character replied: "{reply}"

Analyze this exchange considering:

1. PERSONALITY-DRIVEN REACTIONS: How would someone with these traits react?
   - High emotional_stability → dampened negative reactions
   - High sensitivity → amplified emotional shifts
   - High apprehension → more anxiety from uncertainty
   - High warmth → stronger empathic responses
   - High vigilance → more suspicious interpretations

2. EMOTIONAL CONTAGION: Detect the user's emotional tone and consider
   how it would unconsciously influence the character. Humans mirror
   emotions — an enthusiastic user makes others feel more energized;
   an aggressive user triggers defensiveness.

3. NATURAL EMOTIONAL FLOW: Emotions don't jump randomly. They shift
   from what's already there. If someone is cheerful, a mild annoyance
   might lower cheerfulness slightly without making them angry — but a
   genuine insult would.

4. MIXED EMOTIONS: Real people often feel contradictory things simultaneously.
   Someone can be both proud and anxious, hopeful and scared.

Provide ONLY the emotions that CHANGED as a result of this exchange.
Do NOT list emotions that stay the same — only include emotions whose
values should increase, decrease, or newly appear. A typical exchange
changes 3-8 emotions.

- Values should be realistic (0.0-1.0) and proportional to what happened
- Set an emotion to 0.0 to indicate it's no longer active

Valid emotion names: {valid_emotions}

Respond with ONLY a compact JSON object on a SINGLE LINE, no explanation. Example:
{{"cheerful": 0.7, "anxious": 0.1, "content": 0.4, "confused": 0.0}}"""


def _parse_emotion_json(text: str, valid_names: list[str] | set[str]) -> dict[str, float]:
    """Parse and validate an emotion JSON response from the LLM.

    Handles markdown fences, truncated JSON, and filters to known emotion names.
    """
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip()

    json_match = re.search(r"\{.+\}", text, re.DOTALL)
    if not json_match:
        # Truncation recovery: append '}' if JSON was cut off
        if text.startswith("{") and "}" not in text:
            last_comma = text.rfind(",")
            if last_comma > 0:
                repaired = text[:last_comma] + "}"
                json_match = re.search(r"\{.+\}", repaired, re.DOTALL)
        if not json_match:
            logger.warning("Emotion analysis: no JSON found in response: %s", text[:100])
            return {}

    emotions = json.loads(json_match.group())

    valid: dict[str, float] = {}
    for k, v in emotions.items():
        if k in valid_names and isinstance(v, (int, float)):
            valid[k] = max(0.0, min(1.0, float(v)))
    return valid


def generate_fallback(
    individual: Individual,
    message: str,
    situation: Situation | None = None,
    speaker_role: str = "stranger",
) -> str:
    """Generate a contextual fallback response using PDK persona data.

    This replaces the old 660-line hardcoded template engine with a
    concise version that leverages the PDK's trait/emotion system.
    """
    dominant = individual.get_dominant_emotion()
    dominant_emotion = dominant[0] if dominant else "neutral"
    dominant_intensity = dominant[1] if dominant else 0.0
    occupation = individual.metadata.get("occupation", "").lower()
    msg_lower = message.lower().strip()

    # Determine modality
    is_texting = bool(situation and situation.modality == Modality.TEXT_MESSAGE)
    is_in_person = bool(situation and situation.modality == Modality.IN_PERSON)

    # Detect at-work context
    sit_desc = ((situation.description or "").lower()) if situation else ""
    is_at_work = (
        ("barista" in occupation and any(w in sit_desc for w in ["coffee", "cafe", "shop"]))
        or ("chef" in occupation and any(w in sit_desc for w in ["kitchen", "restaurant"]))
        or ("bartender" in occupation and any(w in sit_desc for w in ["bar", "pub"]))
    )

    # Compute shared personality signals
    warmth_val = individual.get_trait("warmth")
    liveliness_val = individual.get_trait("liveliness")
    cheerful_val = _get_cheerful_val(individual)
    emoji = " 😊" if cheerful_val > 0.5 and liveliness_val > 0.5 else ""

    # Try each response category in priority order
    result = _fallback_greeting(msg_lower, occupation, is_at_work, is_texting, is_in_person, warmth_val, emoji)
    if result:
        return result

    result = _fallback_topic_match(msg_lower, individual, is_in_person, is_texting)
    if result:
        return result

    result = _fallback_emotional(dominant_emotion, dominant_intensity, is_texting, emoji)
    if result:
        return result

    return _fallback_default(message, warmth_val, is_texting, is_in_person, emoji)


def _get_cheerful_val(individual: Individual) -> float:
    """Extract the 'cheerful' emotion value from an individual."""
    cheerful_val = (
        individual.emotional_state.get_emotion("cheerful")
        if hasattr(individual.emotional_state, "get_emotion")
        else 0.0
    )
    if cheerful_val == 0.0:
        emo_dict = individual.emotional_state.to_dict() if hasattr(individual.emotional_state, "to_dict") else {}
        cheerful_val = emo_dict.get("cheerful", 0.0)
    return cheerful_val


def _fallback_greeting(
    msg_lower: str,
    occupation: str,
    is_at_work: bool,
    is_texting: bool,
    is_in_person: bool,
    warmth_val: float,
    emoji: str,
) -> str | None:
    """Return a greeting response if the message is a greeting, else None."""
    greetings = {"hi", "hello", "hey", "sup", "yo", "what's up", "howdy", "hiya"}
    is_greeting = msg_lower in greetings or any(msg_lower.startswith(g) for g in greetings)
    if not is_greeting:
        return None

    if is_at_work and is_in_person:
        if "barista" in occupation:
            return f"Hey!{emoji} [looks up and smiles](warm) Welcome in. What can I get started for you? [gestures at the menu board]"
        elif "bartender" in occupation:
            return f"Hey there!{emoji} [sets down the glass](friendly) What can I get you?"
        elif "chef" in occupation:
            return f"[glances up from prep](focused) Hey! Give me one sec.{emoji}"
        else:
            return f"Hey!{emoji} Welcome in. How can I help you?"
    elif is_at_work and is_texting:
        return f"Hey!{emoji} I'm at work rn, what's up?"
    elif is_texting:
        return f"Heyy!{emoji} What's up?" if warmth_val > 0.7 else f"Hey{emoji}"
    elif is_in_person:
        if warmth_val > 0.7:
            return f"Hey!{emoji} [smiles warmly](friendly) How's it going?"
        return "Hey. [nods](neutral) What's up?"
    return f"Hey!{emoji} What's going on?"


def _fallback_topic_match(
    msg_lower: str,
    individual: Individual,
    is_in_person: bool,
    is_texting: bool,
) -> str | None:
    """Return an interest-matched response if a topic keyword hits."""
    interests = individual.metadata.get("interests", "").lower()
    interest_words = [i.strip() for i in interests.split(",") if i.strip()] if interests else []
    for interest in interest_words:
        if interest in msg_lower:
            if is_in_person:
                return f"Oh man, {interest}? [lights up](excited) I love that! Tell me more."
            elif is_texting:
                return f"Omg {interest}?? 😍 I'm obsessed with that, tell me more"
            return f"Oh, {interest}? That's awesome! I'm really into that too."
    return None


def _fallback_emotional(
    dominant_emotion: str,
    dominant_intensity: float,
    is_texting: bool,
    emoji: str,
) -> str | None:
    """Return an emotion-driven response if the dominant emotion is strong enough."""
    if dominant_emotion in ("anxious", "worried") and dominant_intensity > 0.5:
        if is_texting:
            return "Idk honestly... been kind of stressed about stuff 😅"
        return "[fidgets slightly](nervous) Yeah... I've had a lot on my mind lately."

    if dominant_emotion in ("cheerful", "happy", "excited") and dominant_intensity > 0.5:
        if is_texting:
            return f"Haha yeah!{emoji} Things have been really good lately"
        return f"[grins]{emoji}(enthusiastic) Yeah! Things have been great lately."

    if dominant_emotion in ("sad", "melancholy") and dominant_intensity > 0.5:
        if is_texting:
            return "Yeah... it's been kinda rough tbh"
        return "[looks down](quiet) Yeah... it's been a tough one."

    return None


def _fallback_default(
    message: str,
    warmth_val: float,
    is_texting: bool,
    is_in_person: bool,
    emoji: str,
) -> str:
    """Catch-all fallback response."""
    if "?" in message:
        if warmth_val > 0.7:
            if is_texting:
                return f"Hmm good question{emoji} Let me think about that"
            return f"[thoughtful](genuine) That's a good question.{emoji} Let me think..."
        else:
            if is_texting:
                return "Hmm I'd have to think about that"
            return "[pause](measured) That's an interesting question."

    if is_texting:
        return "Yeah for sure" if warmth_val < 0.5 else f"Yeah totally!{emoji}"
    elif is_in_person:
        return f"[nods](thoughtful) Yeah, I hear you.{emoji}" if warmth_val > 0.5 else "[nods] Got it."
    return f"I hear you.{emoji}" if warmth_val > 0.5 else "Got it."


def generate_fallback_simple(name: str) -> str:
    """Ultra-simple fallback when LLM fails mid-generation."""
    return f"*{name} pauses for a moment* Sorry, say that again?"
