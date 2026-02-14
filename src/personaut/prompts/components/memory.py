"""Memory component for prompt generation.

This module provides the MemoryComponent class that filters and formats
memories for inclusion in prompts, respecting trust levels and privacy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class MemoryProtocol(Protocol):
    """Protocol for memory objects."""

    @property
    def description(self) -> str:
        """Memory description."""
        ...

    @property
    def memory_type(self) -> str:
        """Type of memory (individual, shared, private)."""
        ...

    def get_trust_threshold(self) -> float | None:
        """Get trust threshold for private memories."""
        ...


@dataclass
class MemoryComponent:
    """Component for formatting memories into prompt text.

    This component filters memories by trust level and formats them
    as relevant context for the individual's responses.

    Attributes:
        max_memories: Maximum number of memories to include.
        include_type: Whether to indicate memory type.

    Example:
        >>> component = MemoryComponent()
        >>> text = component.format(memories, trust_level=0.7)
    """

    max_memories: int = 5
    include_type: bool = False

    def format(
        self,
        memories: list[Any],
        *,
        trust_level: float = 1.0,
        name: str = "They",
    ) -> str:
        """Format memories into natural language.

        Args:
            memories: List of memory objects to format.
            trust_level: Current trust level for filtering private memories.
            name: Name to use in the description.

        Returns:
            Natural language description of relevant memories.
        """
        if not memories:
            return ""

        # Filter by trust level
        accessible_memories = self._filter_by_trust(memories, trust_level)

        if not accessible_memories:
            return ""

        # Limit to max
        accessible_memories = accessible_memories[: self.max_memories]

        lines = ["## Relevant Memories"]

        for memory in accessible_memories:
            description = self._get_description(memory)
            memory_type = self._get_type(memory)

            if self.include_type and memory_type:
                type_label = f"[{memory_type}] "
            else:
                type_label = ""

            lines.append(f"- {type_label}{name} remembers: {description}")

        return "\n".join(lines)

    def _filter_by_trust(
        self,
        memories: list[Any],
        trust_level: float,
    ) -> list[Any]:
        """Filter memories based on trust level.

        Private memories are only included if trust level meets threshold.
        """
        accessible = []
        for memory in memories:
            threshold = self._get_trust_threshold(memory)

            if threshold is None or trust_level >= threshold:
                accessible.append(memory)

        return accessible

    def _get_description(self, memory: Any) -> str:
        """Get description from memory object."""
        if hasattr(memory, "description"):
            return str(memory.description)
        if isinstance(memory, dict):
            return str(memory.get("description", str(memory)))
        return str(memory)

    def _get_type(self, memory: Any) -> str | None:
        """Get type from memory object."""
        if hasattr(memory, "memory_type"):
            return str(memory.memory_type)
        if isinstance(memory, dict):
            return memory.get("memory_type")
        return None

    def _get_trust_threshold(self, memory: Any) -> float | None:
        """Get trust threshold from memory object."""
        if hasattr(memory, "get_trust_threshold"):
            result = memory.get_trust_threshold()
            return float(result) if result is not None else None
        if hasattr(memory, "trust_threshold"):
            threshold = memory.trust_threshold
            return float(threshold) if threshold is not None else None
        if isinstance(memory, dict):
            threshold = memory.get("trust_threshold")
            return float(threshold) if threshold is not None else None
        return None

    def format_brief(
        self,
        memories: list[Any],
        *,
        trust_level: float = 1.0,
    ) -> str:
        """Generate a brief summary of memories.

        Args:
            memories: List of memory objects.
            trust_level: Current trust level.

        Returns:
            Brief one-line summary.
        """
        accessible = self._filter_by_trust(memories, trust_level)

        if not accessible:
            return "no relevant memories"

        count = len(accessible)
        if count == 1:
            return "1 relevant memory"
        return f"{count} relevant memories"


__all__ = [
    "MemoryComponent",
    "MemoryProtocol",
]
