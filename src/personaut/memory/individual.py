"""Individual memory for Personaut PDK.

This module provides individual-specific memories that belong
to a single persona.

Example:
    >>> from personaut.memory import IndividualMemory, create_individual_memory
    >>> from personaut.emotions import EmotionalState
    >>>
    >>> memory = create_individual_memory(
    ...     owner_id="persona_123",
    ...     description="My first day at the new job",
    ...     emotional_state=EmotionalState({"excited": 0.8, "anxious": 0.4}),
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from personaut.memory.memory import Memory, MemoryType, _generate_memory_id


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.facts.context import SituationalContext


@dataclass
class IndividualMemory(Memory):
    """Memory belonging to a single individual.

    Individual memories are personal experiences that are not
    shared with others by default.

    Attributes:
        owner_id: The ID of the individual who owns this memory.
        salience: How important/memorable this is (0.0 to 1.0).

    Example:
        >>> memory = IndividualMemory(
        ...     owner_id="sarah_123",
        ...     description="First coffee date",
        ...     salience=0.9,
        ... )
    """

    owner_id: str = ""
    salience: float = 0.5

    def __post_init__(self) -> None:
        """Ensure memory type is set correctly."""
        # Force memory type to INDIVIDUAL
        object.__setattr__(self, "memory_type", MemoryType.INDIVIDUAL)

        # Validate salience
        if not 0.0 <= self.salience <= 1.0:
            msg = f"Salience must be between 0.0 and 1.0, got {self.salience}"
            raise ValueError(msg)

    def belongs_to(self, individual_id: str) -> bool:
        """Check if this memory belongs to a specific individual.

        Args:
            individual_id: The ID to check against.

        Returns:
            True if this memory belongs to the individual.
        """
        return self.owner_id == individual_id

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary including individual-specific fields."""
        result = super().to_dict()
        result["owner_id"] = self.owner_id
        result["salience"] = self.salience
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndividualMemory:
        """Create an IndividualMemory from a dictionary."""
        from personaut.facts.context import SituationalContext
        from personaut.memory.memory import _emotional_state_from_dict

        emotional_state = None
        if "emotional_state" in data:
            emotional_state = _emotional_state_from_dict(data["emotional_state"])

        context = None
        if "context" in data:
            context = SituationalContext.from_dict(data["context"])

        return cls(
            id=data.get("id", _generate_memory_id()),
            description=data["description"],
            owner_id=data.get("owner_id", ""),
            salience=data.get("salience", 0.5),
            emotional_state=emotional_state,
            context=context,
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )


def create_individual_memory(
    owner_id: str,
    description: str,
    emotional_state: EmotionalState | None = None,
    context: SituationalContext | None = None,
    salience: float = 0.5,
    metadata: dict[str, Any] | None = None,
) -> IndividualMemory:
    """Create a new individual memory.

    Args:
        owner_id: The ID of the individual who owns this memory.
        description: Human-readable description of the memory.
        emotional_state: Optional emotional state at time of memory.
        context: Optional situational context.
        salience: How important this memory is (0.0 to 1.0).
        metadata: Optional additional metadata.

    Returns:
        A new IndividualMemory instance.

    Example:
        >>> memory = create_individual_memory(
        ...     owner_id="sarah_123",
        ...     description="Got promoted at work",
        ...     emotional_state=EmotionalState({"proud": 0.9}),
        ...     salience=0.95,
        ... )
    """
    return IndividualMemory(
        owner_id=owner_id,
        description=description,
        emotional_state=emotional_state,
        context=context,
        salience=salience,
        metadata=metadata or {},
    )


def generate_memory_emotional_state(
    description: str,
    trait_profile: dict[str, float] | None = None,
    individual_name: str = "this person",
) -> EmotionalState:
    """Generate an emotional state for a memory using the LLM and trait modulation.

    This function asks the LLM to infer what emotions an individual would
    experience for a given memory, then applies trait modulation via
    ``EmotionalState.apply_trait_modulated_change()`` so that the resulting
    emotions are consistent with the individual's personality.

    Args:
        description: The memory description text.
        trait_profile: Optional dict of trait name → value (0.0–1.0).
            Used both to inform the LLM prompt and to modulate the result.
        individual_name: Name of the individual (for prompt context).

    Returns:
        An ``EmotionalState`` with the inferred emotional values.

    Raises:
        RuntimeError: If the LLM response cannot be parsed.

    Example:
        >>> state = generate_memory_emotional_state(
        ...     description="Got fired from my dream job",
        ...     trait_profile={"emotional_stability": 0.3, "sensitivity": 0.8},
        ...     individual_name="Sarah",
        ... )
        >>> state.get_dominant()
        ('guilty', 0.85)
    """
    import json
    import logging
    import re

    from personaut.emotions.emotion import ALL_EMOTIONS
    from personaut.emotions.state import EmotionalState
    from personaut.models.registry import get_llm

    logger = logging.getLogger(__name__)

    # Build trait summary for the prompt
    trait_summary = "Average personality across all traits."
    if trait_profile:
        high = [t for t, v in trait_profile.items() if v >= 0.65]
        low = [t for t, v in trait_profile.items() if v <= 0.35]
        parts: list[str] = []
        if high:
            parts.append(f"High traits: {', '.join(high)}.")
        if low:
            parts.append(f"Low traits: {', '.join(low)}.")
        if parts:
            trait_summary = " ".join(parts)

    valid_emotions = ", ".join(ALL_EMOTIONS)

    prompt = (
        "You are a psychologist analysing how a memory would have "
        "affected someone emotionally.\n\n"
        f"PERSON: {individual_name}\n"
        f"PERSONALITY: {trait_summary}\n"
        f'MEMORY: "{description}"\n\n'
        "Based on this person's personality traits, determine the emotional "
        "state they would have experienced during this memory. Consider:\n"
        "1. Their trait profile should modulate the intensity "
        "(high emotional_stability = dampened reactions)\n"
        "2. The memory content determines which emotions are relevant\n"
        "3. Return only the 3-8 most relevant emotions, not all of them\n"
        "4. Values 0.0-1.0 where 0.0=absent, 1.0=extreme\n\n"
        f"Valid emotion names: {valid_emotions}\n\n"
        "Respond with ONLY a compact JSON object on a SINGLE LINE, "
        "no explanation.\n"
        'Example: {"proud": 0.8, "excited": 0.6, "anxious": 0.2}'
    )

    llm = get_llm()
    result = llm.generate(prompt, temperature=0.3, max_tokens=256)
    text = result.text.strip()

    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()

    # Extract JSON object
    json_match = re.search(r"\{.+\}", text, re.DOTALL)
    if not json_match:
        msg = f"Could not parse emotional state from LLM response: {text[:120]}"
        logger.warning(msg)
        raise RuntimeError(msg)

    raw_emotions: dict[str, float] = json.loads(json_match.group())

    # Validate and clamp
    all_emotions_set = set(ALL_EMOTIONS)
    validated: dict[str, float] = {}
    for k, v in raw_emotions.items():
        if k in all_emotions_set and isinstance(v, (int, float)):
            validated[k] = round(max(0.0, min(1.0, float(v))), 2)

    if not validated:
        msg = "No valid emotions in LLM response"
        raise RuntimeError(msg)

    # Create an EmotionalState and apply trait modulation
    state = EmotionalState()
    state.apply_trait_modulated_change(validated, trait_profile)

    return state


__all__ = [
    "IndividualMemory",
    "create_individual_memory",
    "generate_memory_emotional_state",
]
