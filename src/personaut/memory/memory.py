"""Memory base classes for Personaut PDK.

This module provides the foundational memory types that store
experiences with emotional context and situational grounding.

Example:
    >>> from personaut.memory import Memory, MemoryType
    >>> from personaut.emotions import EmotionalState
    >>> from personaut.facts import create_coffee_shop_context
    >>>
    >>> memory = Memory(
    ...     description="First meeting with Sarah at the cafe",
    ...     emotional_state=EmotionalState({"cheerful": 0.8, "anxious": 0.3}),
    ...     context=create_coffee_shop_context(city="Miami, FL"),
    ... )
    >>> print(memory.to_embedding_text())
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.facts.context import SituationalContext


class MemoryType(str, Enum):
    """Types of memories in the system.

    Attributes:
        INDIVIDUAL: Personal memory belonging to a single individual.
        SHARED: Memory shared between multiple individuals.
        PRIVATE: Sensitive memory with trust-gated access.
    """

    INDIVIDUAL = "individual"
    SHARED = "shared"
    PRIVATE = "private"

    @property
    def description(self) -> str:
        """Human-readable description of the memory type."""
        descriptions = {
            MemoryType.INDIVIDUAL: "Personal memory belonging to a single individual",
            MemoryType.SHARED: "Memory shared between multiple individuals",
            MemoryType.PRIVATE: "Sensitive memory with trust-gated access",
        }
        return descriptions[self]

    @property
    def requires_trust_check(self) -> bool:
        """Whether this memory type requires trust level verification."""
        return self == MemoryType.PRIVATE


def _generate_memory_id() -> str:
    """Generate a unique memory ID."""
    return f"mem_{uuid.uuid4().hex[:12]}"


def _emotional_state_from_dict(data: dict[str, float]) -> EmotionalState:
    """Create an EmotionalState from a dictionary of emotion values.

    Helper function since EmotionalState doesn't have from_dict method.
    """
    from personaut.emotions.state import EmotionalState

    # Get only the emotions present in the data
    emotions = list(data.keys())
    state = EmotionalState(emotions=emotions, baseline=0.0)
    state.change_state(data)
    return state


@dataclass
class Memory:
    """Base class for all memory types.

    A memory represents a stored experience with optional emotional
    context and situational grounding.

    Attributes:
        id: Unique identifier for the memory.
        description: Human-readable description of the memory.
        created_at: When the memory was created.
        memory_type: The type of memory (individual, shared, private).
        emotional_state: Optional emotional state at time of memory.
        context: Optional situational context with structured facts.
        embedding: Optional pre-computed embedding vector.
        metadata: Additional metadata storage.

    Example:
        >>> memory = Memory(
        ...     description="Had coffee with Sarah",
        ...     emotional_state=EmotionalState({"cheerful": 0.7}),
        ... )
        >>> memory.id
        'mem_abc123...'
    """

    description: str
    memory_type: MemoryType = MemoryType.INDIVIDUAL
    id: str = field(default_factory=_generate_memory_id)
    created_at: datetime = field(default_factory=datetime.now)
    emotional_state: EmotionalState | None = None
    context: SituationalContext | None = None
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_embedding_text(self) -> str:
        """Generate text suitable for embedding generation.

        Combines the memory description, emotional state summary,
        and situational context into a single text representation.

        Returns:
            A multi-line string optimized for embedding models.

        Example:
            >>> memory = Memory(
            ...     description="Met Sarah at the coffee shop",
            ...     emotional_state=EmotionalState({"cheerful": 0.8}),
            ... )
            >>> print(memory.to_embedding_text())
            Met Sarah at the coffee shop
            Emotional state: cheerful (high)
        """
        parts = [self.description]

        # Add emotional state summary
        if self.emotional_state is not None:
            dominant = self.emotional_state.get_dominant()
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

    def _value_to_intensity(self, value: float) -> str:
        """Convert a numeric value to an intensity description."""
        if value >= 0.8:
            return "very high"
        if value >= 0.6:
            return "high"
        if value >= 0.4:
            return "moderate"
        if value >= 0.2:
            return "mild"
        return "minimal"

    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the situational context.

        Convenience method to access context facts without
        null checking.

        Args:
            key: The fact key to look up.
            default: Default value if not found.

        Returns:
            The fact value or the default.

        Example:
            >>> memory.get_context_value("city")
            'Miami, FL'
            >>> memory.get_context_value("unknown", "N/A")
            'N/A'
        """
        if self.context is None:
            return default
        return self.context.get_value(key, default)

    def has_context(self) -> bool:
        """Check if this memory has situational context."""
        return self.context is not None and len(self.context) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert memory to a dictionary.

        Returns:
            Dictionary representation of the memory.
        """
        result: dict[str, Any] = {
            "id": self.id,
            "description": self.description,
            "memory_type": self.memory_type.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

        if self.emotional_state is not None:
            result["emotional_state"] = self.emotional_state.to_dict()

        if self.context is not None:
            result["context"] = self.context.to_dict()

        if self.embedding is not None:
            result["embedding"] = self.embedding

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Memory:
        """Create a Memory from a dictionary.

        Args:
            data: Dictionary with memory data.

        Returns:
            A new Memory instance.
        """
        from personaut.facts.context import SituationalContext

        emotional_state = None
        if "emotional_state" in data:
            emotional_state = _emotional_state_from_dict(data["emotional_state"])

        context = None
        if "context" in data:
            context = SituationalContext.from_dict(data["context"])

        return cls(
            id=data.get("id", _generate_memory_id()),
            description=data["description"],
            memory_type=MemoryType(data.get("memory_type", "individual")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            emotional_state=emotional_state,
            context=context,
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return a string representation."""
        desc_preview = self.description[:30] + "..." if len(self.description) > 30 else self.description
        return f"Memory(id='{self.id}', description='{desc_preview}', type={self.memory_type.value})"


def create_memory(
    description: str,
    emotional_state: EmotionalState | None = None,
    context: SituationalContext | None = None,
    memory_type: MemoryType = MemoryType.INDIVIDUAL,
    metadata: dict[str, Any] | None = None,
) -> Memory:
    """Create a new memory.

    Factory function for creating memories with sensible defaults.

    Args:
        description: Human-readable description of the memory.
        emotional_state: Optional emotional state at time of memory.
        context: Optional situational context.
        memory_type: Type of memory (default: INDIVIDUAL).
        metadata: Optional additional metadata.

    Returns:
        A new Memory instance.

    Example:
        >>> from personaut.emotions import EmotionalState
        >>> from personaut.facts import create_coffee_shop_context
        >>>
        >>> memory = create_memory(
        ...     description="Great conversation with Sarah",
        ...     emotional_state=EmotionalState({"cheerful": 0.8}),
        ...     context=create_coffee_shop_context(city="Miami, FL"),
        ... )
    """
    return Memory(
        description=description,
        emotional_state=emotional_state,
        context=context,
        memory_type=memory_type,
        metadata=metadata or {},
    )


__all__ = [
    "Memory",
    "MemoryType",
    "create_memory",
]
