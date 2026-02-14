"""Private memory for Personaut PDK.

This module provides trust-gated memories that are only accessible
when a sufficient trust level is established.

Example:
    >>> from personaut.memory import PrivateMemory, create_private_memory
    >>> from personaut.emotions import EmotionalState
    >>>
    >>> # A deeply personal memory requiring high trust to access
    >>> memory = create_private_memory(
    ...     owner_id="sarah_123",
    ...     description="The day I found out about my diagnosis",
    ...     trust_threshold=0.8,
    ...     emotional_state=EmotionalState({"anxious": 0.9, "scared": 0.7}),
    ... )
    >>> memory.can_access(0.5)  # Low trust
    False
    >>> memory.can_access(0.9)  # High trust
    True
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from personaut.memory.memory import Memory, MemoryType, _generate_memory_id


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.facts.context import SituationalContext


@dataclass
class PrivateMemory(Memory):
    """Trust-gated memory requiring minimum trust level for access.

    Private memories represent sensitive experiences that an individual
    only shares with others they trust sufficiently.

    Attributes:
        owner_id: The ID of the individual who owns this memory.
        trust_threshold: Minimum trust level required to access (0.0 to 1.0).
        disclosure_count: How many times this memory has been shared.
        tags: Optional tags for categorizing private memories.

    Example:
        >>> memory = PrivateMemory(
        ...     owner_id="sarah_123",
        ...     description="My secret fear of failure",
        ...     trust_threshold=0.7,
        ... )
        >>> memory.can_access(0.5)
        False
        >>> memory.can_access(0.8)
        True
    """

    owner_id: str = ""
    trust_threshold: float = 0.5
    disclosure_count: int = 0
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure memory type is set correctly and validate threshold."""
        object.__setattr__(self, "memory_type", MemoryType.PRIVATE)

        # Validate trust threshold
        if not 0.0 <= self.trust_threshold <= 1.0:
            msg = f"Trust threshold must be between 0.0 and 1.0, got {self.trust_threshold}"
            raise ValueError(msg)

    def can_access(self, trust_level: float) -> bool:
        """Check if the given trust level allows access to this memory.

        Args:
            trust_level: The trust level to check (0.0 to 1.0).

        Returns:
            True if access is allowed.

        Example:
            >>> memory = PrivateMemory(
            ...     description="Secret",
            ...     trust_threshold=0.6,
            ... )
            >>> memory.can_access(0.5)
            False
            >>> memory.can_access(0.6)
            True
        """
        return trust_level >= self.trust_threshold

    def record_disclosure(self) -> None:
        """Record that this memory has been disclosed.

        Increments the disclosure count, which can be used
        to track how often private information is shared.
        """
        self.disclosure_count += 1

    def get_sensitivity_level(self) -> str:
        """Get a human-readable sensitivity level.

        Returns:
            A description of how sensitive this memory is.
        """
        if self.trust_threshold >= 0.9:
            return "extremely sensitive"
        if self.trust_threshold >= 0.7:
            return "highly sensitive"
        if self.trust_threshold >= 0.5:
            return "moderately sensitive"
        if self.trust_threshold >= 0.3:
            return "mildly sensitive"
        return "minimally sensitive"

    def belongs_to(self, individual_id: str) -> bool:
        """Check if this memory belongs to a specific individual.

        Args:
            individual_id: The ID to check against.

        Returns:
            True if this memory belongs to the individual.
        """
        return self.owner_id == individual_id

    def add_tag(self, tag: str) -> None:
        """Add a tag to this memory.

        Args:
            tag: The tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if this memory has a specific tag.

        Args:
            tag: The tag to check for.

        Returns:
            True if the tag is present.
        """
        return tag in self.tags

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary including private-specific fields."""
        result = super().to_dict()
        result["owner_id"] = self.owner_id
        result["trust_threshold"] = self.trust_threshold
        result["disclosure_count"] = self.disclosure_count
        result["tags"] = self.tags
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PrivateMemory:
        """Create a PrivateMemory from a dictionary."""
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
            trust_threshold=data.get("trust_threshold", 0.5),
            disclosure_count=data.get("disclosure_count", 0),
            tags=data.get("tags", []),
            emotional_state=emotional_state,
            context=context,
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )


def create_private_memory(
    owner_id: str,
    description: str,
    trust_threshold: float = 0.5,
    emotional_state: EmotionalState | None = None,
    context: SituationalContext | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> PrivateMemory:
    """Create a new private memory.

    Args:
        owner_id: The ID of the individual who owns this memory.
        description: Human-readable description of the memory.
        trust_threshold: Minimum trust level required to access (0.0 to 1.0).
        emotional_state: Optional emotional state at time of memory.
        context: Optional situational context.
        tags: Optional tags for categorizing.
        metadata: Optional additional metadata.

    Returns:
        A new PrivateMemory instance.

    Example:
        >>> memory = create_private_memory(
        ...     owner_id="sarah_123",
        ...     description="My childhood trauma",
        ...     trust_threshold=0.9,
        ...     tags=["childhood", "trauma"],
        ... )
    """
    return PrivateMemory(
        owner_id=owner_id,
        description=description,
        trust_threshold=trust_threshold,
        emotional_state=emotional_state,
        context=context,
        tags=tags or [],
        metadata=metadata or {},
    )


__all__ = [
    "PrivateMemory",
    "create_private_memory",
]
