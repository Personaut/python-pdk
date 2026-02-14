"""Relationship component for prompt generation.

This module provides the RelationshipComponent class that formats
relationship context and trust levels into prompt text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


# Trust level descriptions
TRUST_DESCRIPTIONS: list[tuple[float, str, str]] = [
    (0.0, "deeply distrustful of", "guarded and suspicious around"),
    (0.2, "cautious with", "reserved and wary around"),
    (0.4, "neutral toward", "open to building trust with"),
    (0.6, "trusting of", "comfortable and at ease with"),
    (0.8, "deeply trusting of", "vulnerable and open with"),
]


def get_trust_description(trust_level: float) -> tuple[str, str]:
    """Get trust description for a trust level.

    Args:
        trust_level: Trust value from 0.0 to 1.0.

    Returns:
        Tuple of (short description, detailed description).

    Example:
        >>> get_trust_description(0.75)
        ('trusting of', 'comfortable and at ease with')
    """
    short_desc = "neutral toward"
    detailed_desc = "open to building trust with"

    for threshold, short, detailed in TRUST_DESCRIPTIONS:
        if trust_level >= threshold:
            short_desc = short
            detailed_desc = detailed

    return short_desc, detailed_desc


class RelationshipProtocol(Protocol):
    """Protocol for relationship objects."""

    def get_trust(self, individual_id: str) -> float:
        """Get trust level for an individual."""
        ...

    @property
    def members(self) -> list[str]:
        """IDs of individuals in the relationship."""
        ...


class IndividualProtocol(Protocol):
    """Protocol for individual objects."""

    @property
    def id(self) -> str:
        """Individual ID."""
        ...

    @property
    def name(self) -> str:
        """Individual name."""
        ...


@dataclass
class RelationshipComponent:
    """Component for formatting relationship context into prompt text.

    This component converts relationship information and trust levels
    into natural language that provides context for interactions.

    Attributes:
        include_history: Whether to include relationship history.

    Example:
        >>> component = RelationshipComponent()
        >>> text = component.format(individual, others, relationships)
    """

    include_history: bool = False

    def format(
        self,
        individual: Any,
        other_individuals: list[Any],
        relationships: list[Any],
    ) -> str:
        """Format relationship context into natural language.

        Args:
            individual: The main individual.
            other_individuals: Other individuals in the interaction.
            relationships: List of relationship objects.

        Returns:
            Natural language description of relationships.
        """
        if not other_individuals:
            return ""

        individual_id = self._get_id(individual)
        individual_name = self._get_name(individual)

        lines = ["## Relationship Context"]

        for other in other_individuals:
            other_id = self._get_id(other)
            other_name = self._get_name(other)

            # Find relationship between them
            relationship = self._find_relationship(individual_id, other_id, relationships)

            if relationship:
                trust = self._get_trust(relationship, individual_id)
                _short_desc, detailed_desc = get_trust_description(trust)
                lines.append(f"- With {other_name}: {individual_name} is {detailed_desc} them.")
            else:
                lines.append(
                    f"- With {other_name}: {individual_name} has no prior relationship. "
                    f"They will naturally be somewhat cautious initially."
                )

        return "\n".join(lines)

    def _get_id(self, individual: Any) -> str:
        """Get ID from individual object."""
        if hasattr(individual, "id"):
            return str(individual.id)
        if isinstance(individual, dict):
            return str(individual.get("id", str(individual)))
        return str(individual)

    def _get_name(self, individual: Any) -> str:
        """Get name from individual object."""
        if hasattr(individual, "name"):
            return str(individual.name)
        if isinstance(individual, dict):
            return str(individual.get("name", "Unknown"))
        return "Unknown"

    def _find_relationship(
        self,
        individual_id: str,
        other_id: str,
        relationships: list[Any],
    ) -> Any | None:
        """Find relationship between two individuals."""
        for relationship in relationships:
            members = self._get_members(relationship)
            if individual_id in members and other_id in members:
                return relationship
        return None

    def _get_members(self, relationship: Any) -> list[str]:
        """Get member IDs from relationship object."""
        if hasattr(relationship, "members"):
            members = relationship.members
            return [str(m) for m in members] if members else []
        if hasattr(relationship, "individuals"):
            return [self._get_id(i) for i in relationship.individuals]
        if isinstance(relationship, dict):
            members = relationship.get("members", relationship.get("individuals", []))
            return [str(m) for m in members] if members else []
        return []

    def _get_trust(self, relationship: Any, individual_id: str) -> float:
        """Get trust level from relationship."""
        if hasattr(relationship, "get_trust"):
            try:
                return float(relationship.get_trust(individual_id))
            except (ValueError, TypeError):
                pass
        if hasattr(relationship, "trust"):
            trust = relationship.trust
            if isinstance(trust, dict):
                return float(trust.get(individual_id, 0.5))
            return float(trust)
        if isinstance(relationship, dict):
            trust = relationship.get("trust", 0.5)
            if isinstance(trust, dict):
                return float(trust.get(individual_id, 0.5))
            return float(trust)
        return 0.5

    def format_brief(
        self,
        individual: Any,
        other_individuals: list[Any],
        relationships: list[Any],
    ) -> str:
        """Generate a brief relationship summary.

        Args:
            individual: The main individual.
            other_individuals: Other individuals.
            relationships: List of relationships.

        Returns:
            Brief one-line summary.
        """
        if not other_individuals:
            return "no relationships"

        individual_id = self._get_id(individual)
        trust_levels = []

        for other in other_individuals:
            other_id = self._get_id(other)
            relationship = self._find_relationship(individual_id, other_id, relationships)
            if relationship:
                trust = self._get_trust(relationship, individual_id)
                trust_levels.append(trust)
            else:
                trust_levels.append(0.5)  # Neutral for strangers

        avg_trust = sum(trust_levels) / len(trust_levels)
        short_desc, _ = get_trust_description(avg_trust)

        return f"{short_desc} others"


__all__ = [
    "TRUST_DESCRIPTIONS",
    "RelationshipComponent",
    "get_trust_description",
]
