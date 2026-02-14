"""Shared memory for Personaut PDK.

This module provides memories that are shared between multiple
individuals, each with their own perspective.

Example:
    >>> from personaut.memory import SharedMemory, create_shared_memory
    >>>
    >>> memory = create_shared_memory(
    ...     description="The group dinner at the Italian restaurant",
    ...     participant_ids=["sarah_123", "mike_456", "alex_789"],
    ...     perspectives={
    ...         "sarah_123": "Great food, but Mike was being annoying",
    ...         "mike_456": "Fun evening with old friends",
    ...     },
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from personaut.memory.memory import Memory, MemoryType, _generate_memory_id


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.facts.context import SituationalContext


@dataclass
class SharedMemory(Memory):
    """Memory shared between multiple individuals.

    Shared memories represent experiences that involved multiple
    participants, each potentially with their own perspective
    on what happened.

    Attributes:
        participant_ids: List of individual IDs who share this memory.
        perspectives: Individual-specific interpretations of the memory.
        emotional_states: Individual-specific emotional states.

    Example:
        >>> memory = SharedMemory(
        ...     description="Team celebration after the project launch",
        ...     participant_ids=["alice", "bob", "carol"],
        ...     perspectives={
        ...         "alice": "Proud of leading the team",
        ...         "bob": "Relieved it's finally done",
        ...     },
        ... )
    """

    participant_ids: list[str] = field(default_factory=list)
    perspectives: dict[str, str] = field(default_factory=dict)
    emotional_states: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure memory type is set correctly."""
        object.__setattr__(self, "memory_type", MemoryType.SHARED)

    def add_participant(self, individual_id: str) -> None:
        """Add a participant to this shared memory.

        Args:
            individual_id: The ID of the individual to add.
        """
        if individual_id not in self.participant_ids:
            self.participant_ids.append(individual_id)

    def set_perspective(self, individual_id: str, perspective: str) -> None:
        """Set an individual's perspective on this memory.

        Args:
            individual_id: The ID of the individual.
            perspective: Their interpretation of the memory.
        """
        self.perspectives[individual_id] = perspective
        if individual_id not in self.participant_ids:
            self.participant_ids.append(individual_id)

    def get_perspective(self, individual_id: str) -> str | None:
        """Get an individual's perspective on this memory.

        Args:
            individual_id: The ID of the individual.

        Returns:
            Their perspective, or None if not set.
        """
        return self.perspectives.get(individual_id)

    def set_emotional_state(self, individual_id: str, state: EmotionalState) -> None:
        """Set an individual's emotional state for this memory.

        Args:
            individual_id: The ID of the individual.
            state: Their emotional state during this memory.
        """
        self.emotional_states[individual_id] = state.to_dict()

    def get_emotional_state(self, individual_id: str) -> EmotionalState | None:
        """Get an individual's emotional state for this memory.

        Args:
            individual_id: The ID of the individual.

        Returns:
            Their emotional state, or None if not set.
        """
        from personaut.memory.memory import _emotional_state_from_dict

        state_data = self.emotional_states.get(individual_id)
        if state_data is None:
            return None
        return _emotional_state_from_dict(state_data)

    def is_participant(self, individual_id: str) -> bool:
        """Check if an individual is a participant.

        Args:
            individual_id: The ID to check.

        Returns:
            True if they are a participant.
        """
        return individual_id in self.participant_ids

    def to_embedding_text(self, perspective_id: str | None = None) -> str:
        """Generate embedding text, optionally from a specific perspective.

        Args:
            perspective_id: Optional individual ID for perspective-specific text.

        Returns:
            Text suitable for embedding generation.
        """
        parts = [self.description]

        # Add perspective-specific interpretation
        if perspective_id and perspective_id in self.perspectives:
            parts.append(f"Personal perspective: {self.perspectives[perspective_id]}")

        # Add emotional state (either shared or perspective-specific)
        emotional_state = None
        if perspective_id and perspective_id in self.emotional_states:
            from personaut.memory.memory import _emotional_state_from_dict

            emotional_state = _emotional_state_from_dict(self.emotional_states[perspective_id])
        elif self.emotional_state is not None:
            emotional_state = self.emotional_state

        if emotional_state is not None:
            dominant = emotional_state.get_dominant()
            if dominant:
                emotion, value = dominant
                intensity = self._value_to_intensity(value)
                parts.append(f"Emotional state: {emotion} ({intensity})")

        # Add situational context
        if self.context is not None:
            context_text = self.context.to_embedding_text()
            if context_text:
                parts.append(context_text)

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary including shared-specific fields."""
        result = super().to_dict()
        result["participant_ids"] = self.participant_ids
        result["perspectives"] = self.perspectives
        result["emotional_states"] = self.emotional_states
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SharedMemory:
        """Create a SharedMemory from a dictionary."""
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
            participant_ids=data.get("participant_ids", []),
            perspectives=data.get("perspectives", {}),
            emotional_states=data.get("emotional_states", {}),
            emotional_state=emotional_state,
            context=context,
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )


def create_shared_memory(
    description: str,
    participant_ids: list[str] | None = None,
    perspectives: dict[str, str] | None = None,
    context: SituationalContext | None = None,
    emotional_state: EmotionalState | None = None,
    metadata: dict[str, Any] | None = None,
) -> SharedMemory:
    """Create a new shared memory.

    Args:
        description: Human-readable description of the memory.
        participant_ids: List of individual IDs who share this memory.
        perspectives: Individual-specific interpretations.
        context: Optional situational context.
        emotional_state: Optional shared emotional state.
        metadata: Optional additional metadata.

    Returns:
        A new SharedMemory instance.

    Example:
        >>> memory = create_shared_memory(
        ...     description="The surprise birthday party",
        ...     participant_ids=["alice", "bob", "carol"],
        ...     perspectives={
        ...         "alice": "I was genuinely surprised!",
        ...         "bob": "Keeping the secret was hard",
        ...     },
        ... )
    """
    return SharedMemory(
        description=description,
        participant_ids=participant_ids or [],
        perspectives=perspectives or {},
        context=context,
        emotional_state=emotional_state,
        metadata=metadata or {},
    )


__all__ = [
    "SharedMemory",
    "create_shared_memory",
]
