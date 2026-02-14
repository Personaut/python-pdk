"""Situational context for Personaut PDK.

This module defines the SituationalContext class that aggregates
multiple facts into a coherent representation of a situation.

Example:
    >>> from personaut.facts import SituationalContext, FactCategory
    >>> context = SituationalContext()
    >>> context.add_location("city", "Miami, FL")
    >>> context.add_environment("capacity_percent", 80, unit="percent")
    >>> context.add_behavioral("queue_length", 5, unit="people")
    >>> print(context.to_embedding_text())
    city: Miami, FL
    capacity_percent: 80 percent
    queue_length: 5 people
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from personaut.facts.fact import (
    Fact,
    FactCategory,
    create_behavioral_fact,
    create_environment_fact,
    create_location_fact,
)


if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class SituationalContext:
    """A collection of facts describing a situation.

    SituationalContext aggregates multiple facts into a coherent
    representation that can be used for embeddings, memory storage,
    and contextual prompting.

    Attributes:
        facts: List of facts in this context.
        timestamp: When this context was captured.
        description: Optional human-readable description.

    Example:
        >>> ctx = SituationalContext(description="Coffee shop visit")
        >>> ctx.add_location("city", "Miami, FL")
        >>> ctx.add_location("venue_type", "coffee shop")
        >>> len(ctx)
        2
    """

    facts: list[Fact] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    description: str | None = None

    def add_fact(self, fact: Fact) -> None:
        """Add a fact to the context.

        Args:
            fact: The fact to add.

        Example:
            >>> ctx = SituationalContext()
            >>> fact = Fact(FactCategory.LOCATION, "city", "Miami")
            >>> ctx.add_fact(fact)
        """
        self.facts.append(fact)

    def add_location(
        self,
        key: str,
        value: Any,
        confidence: float = 1.0,
        **metadata: Any,
    ) -> Fact:
        """Add a location fact.

        Args:
            key: The fact key.
            value: The fact value.
            confidence: Confidence in the fact.
            **metadata: Additional metadata.

        Returns:
            The created fact.

        Example:
            >>> ctx = SituationalContext()
            >>> fact = ctx.add_location("city", "Miami, FL")
            >>> fact.key
            'city'
        """
        fact = create_location_fact(key, value, confidence, **metadata)
        self.facts.append(fact)
        return fact

    def add_environment(
        self,
        key: str,
        value: Any,
        unit: str | None = None,
        confidence: float = 1.0,
        **metadata: Any,
    ) -> Fact:
        """Add an environment fact.

        Args:
            key: The fact key.
            value: The fact value.
            unit: Optional unit of measurement.
            confidence: Confidence in the fact.
            **metadata: Additional metadata.

        Returns:
            The created fact.

        Example:
            >>> ctx = SituationalContext()
            >>> fact = ctx.add_environment("capacity_percent", 80, unit="percent")
            >>> str(fact)
            'capacity_percent: 80 percent'
        """
        fact = create_environment_fact(key, value, unit, confidence, **metadata)
        self.facts.append(fact)
        return fact

    def add_behavioral(
        self,
        key: str,
        value: Any,
        unit: str | None = None,
        confidence: float = 1.0,
        **metadata: Any,
    ) -> Fact:
        """Add a behavioral fact.

        Args:
            key: The fact key.
            value: The fact value.
            unit: Optional unit of measurement.
            confidence: Confidence in the fact.
            **metadata: Additional metadata.

        Returns:
            The created fact.

        Example:
            >>> ctx = SituationalContext()
            >>> fact = ctx.add_behavioral("queue_length", 5, unit="people")
            >>> str(fact)
            'queue_length: 5 people'
        """
        fact = create_behavioral_fact(key, value, unit, confidence, **metadata)
        self.facts.append(fact)
        return fact

    def add_temporal(
        self,
        key: str,
        value: Any,
        confidence: float = 1.0,
        **metadata: Any,
    ) -> Fact:
        """Add a temporal fact.

        Args:
            key: The fact key.
            value: The fact value.
            confidence: Confidence in the fact.
            **metadata: Additional metadata.

        Returns:
            The created fact.
        """
        fact = Fact(
            category=FactCategory.TEMPORAL,
            key=key,
            value=value,
            confidence=confidence,
            metadata=metadata,
        )
        self.facts.append(fact)
        return fact

    def add_social(
        self,
        key: str,
        value: Any,
        unit: str | None = None,
        confidence: float = 1.0,
        **metadata: Any,
    ) -> Fact:
        """Add a social fact.

        Args:
            key: The fact key.
            value: The fact value.
            unit: Optional unit of measurement.
            confidence: Confidence in the fact.
            **metadata: Additional metadata.

        Returns:
            The created fact.
        """
        fact = Fact(
            category=FactCategory.SOCIAL,
            key=key,
            value=value,
            unit=unit,
            confidence=confidence,
            metadata=metadata,
        )
        self.facts.append(fact)
        return fact

    def add_sensory(
        self,
        key: str,
        value: Any,
        confidence: float = 1.0,
        **metadata: Any,
    ) -> Fact:
        """Add a sensory fact.

        Args:
            key: The fact key.
            value: The fact value.
            confidence: Confidence in the fact.
            **metadata: Additional metadata.

        Returns:
            The created fact.
        """
        fact = Fact(
            category=FactCategory.SENSORY,
            key=key,
            value=value,
            confidence=confidence,
            metadata=metadata,
        )
        self.facts.append(fact)
        return fact

    def get_facts_by_category(self, category: FactCategory) -> list[Fact]:
        """Get all facts in a specific category.

        Args:
            category: The category to filter by.

        Returns:
            List of facts in that category.

        Example:
            >>> ctx = SituationalContext()
            >>> ctx.add_location("city", "Miami")
            >>> ctx.add_environment("noise_level", "moderate")
            >>> len(ctx.get_facts_by_category(FactCategory.LOCATION))
            1
        """
        return [f for f in self.facts if f.category == category]

    def get_fact(self, key: str) -> Fact | None:
        """Get a fact by its key.

        Args:
            key: The fact key to search for.

        Returns:
            The first fact with that key, or None.

        Example:
            >>> ctx = SituationalContext()
            >>> ctx.add_location("city", "Miami")
            >>> fact = ctx.get_fact("city")
            >>> fact.value
            'Miami'
        """
        for fact in self.facts:
            if fact.key == key:
                return fact
        return None

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a fact value by key.

        Args:
            key: The fact key.
            default: Default value if not found.

        Returns:
            The fact value or default.

        Example:
            >>> ctx = SituationalContext()
            >>> ctx.add_location("city", "Miami")
            >>> ctx.get_value("city")
            'Miami'
            >>> ctx.get_value("unknown", "N/A")
            'N/A'
        """
        fact = self.get_fact(key)
        return fact.value if fact else default

    def to_embedding_text(self, include_categories: list[FactCategory] | None = None) -> str:
        """Generate text suitable for embedding.

        Args:
            include_categories: Optional list of categories to include.
                If None, includes all categories.

        Returns:
            Multi-line text representation of facts.

        Example:
            >>> ctx = SituationalContext()
            >>> ctx.add_location("city", "Miami, FL")
            >>> ctx.add_environment("capacity_percent", 80)
            >>> print(ctx.to_embedding_text())
            city: Miami, FL
            capacity_percent: 80
        """
        facts = self.facts
        if include_categories:
            facts = [f for f in facts if f.category in include_categories]

        # Sort by category weight (highest first) then by key
        sorted_facts = sorted(
            facts,
            key=lambda f: (-f.category.embedding_weight, f.key),
        )

        lines = [fact.to_embedding_text() for fact in sorted_facts]
        return "\n".join(lines)

    def to_weighted_embedding_pairs(self) -> list[tuple[str, float]]:
        """Generate weighted text-value pairs for embedding.

        Each fact is paired with its category's embedding weight,
        allowing weighted embedding generation.

        Returns:
            List of (text, weight) tuples.

        Example:
            >>> ctx = SituationalContext()
            >>> ctx.add_location("city", "Miami")
            >>> pairs = ctx.to_weighted_embedding_pairs()
            >>> pairs[0][1]  # LOCATION has weight 1.0
            1.0
        """
        return [(fact.to_embedding_text(), fact.category.embedding_weight) for fact in self.facts]

    def to_dict(self) -> dict[str, Any]:
        """Convert context to a dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "facts": [f.to_dict() for f in self.facts],
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SituationalContext:
        """Create context from a dictionary.

        Args:
            data: Dictionary with context data.

        Returns:
            A new SituationalContext instance.
        """
        facts = [Fact.from_dict(f) for f in data.get("facts", [])]
        timestamp = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
        return cls(
            facts=facts,
            timestamp=timestamp,
            description=data.get("description"),
        )

    def copy(self) -> SituationalContext:
        """Create a copy of this context.

        Returns:
            A new SituationalContext with the same facts.
        """
        return SituationalContext(
            facts=list(self.facts),  # Facts are frozen, so shallow copy is fine
            timestamp=self.timestamp,
            description=self.description,
        )

    def merge(self, other: SituationalContext) -> SituationalContext:
        """Merge two contexts into a new one.

        Args:
            other: The other context to merge.

        Returns:
            A new context with facts from both.

        Example:
            >>> ctx1 = SituationalContext()
            >>> ctx1.add_location("city", "Miami")
            >>> ctx2 = SituationalContext()
            >>> ctx2.add_environment("noise", "loud")
            >>> merged = ctx1.merge(ctx2)
            >>> len(merged)
            2
        """
        return SituationalContext(
            facts=self.facts + other.facts,
            timestamp=min(self.timestamp, other.timestamp),
            description=self.description or other.description,
        )

    def __len__(self) -> int:
        """Return the number of facts."""
        return len(self.facts)

    def __iter__(self) -> Iterator[Fact]:
        """Iterate over facts."""
        return iter(self.facts)

    def __contains__(self, key: str) -> bool:
        """Check if a fact key exists."""
        return any(f.key == key for f in self.facts)

    def __repr__(self) -> str:
        """Return a string representation."""
        category_counts: dict[str, int] = {}
        for fact in self.facts:
            cat = fact.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        counts_str = ", ".join(f"{k}={v}" for k, v in sorted(category_counts.items()))
        return f"SituationalContext({counts_str})"


# Pre-built context templates for common situations
def create_coffee_shop_context(
    city: str,
    venue_name: str | None = None,
    capacity_percent: int = 50,
    queue_length: int = 0,
    noise_level: str = "moderate",
    time_of_day: str | None = None,
) -> SituationalContext:
    """Create a context for a coffee shop situation.

    Args:
        city: City location.
        venue_name: Optional specific venue name.
        capacity_percent: Percentage of capacity filled.
        queue_length: Number of people in line.
        noise_level: Ambient noise level.
        time_of_day: Time of day if known.

    Returns:
        A configured SituationalContext.

    Example:
        >>> ctx = create_coffee_shop_context(
        ...     city="Miami, FL",
        ...     venue_name="Sunrise Cafe",
        ...     capacity_percent=80,
        ...     queue_length=5,
        ... )
        >>> ctx.get_value("venue_type")
        'coffee shop'
    """
    ctx = SituationalContext(description=f"Coffee shop in {city}")

    ctx.add_location("city", city)
    ctx.add_location("venue_type", "coffee shop")
    ctx.add_location("indoor_outdoor", "indoor")

    if venue_name:
        ctx.add_location("venue_name", venue_name)

    ctx.add_environment("capacity_percent", capacity_percent, unit="percent")
    ctx.add_environment("noise_level", noise_level)
    ctx.add_environment("atmosphere", "casual")

    ctx.add_behavioral("queue_length", queue_length, unit="people")

    if time_of_day:
        ctx.add_temporal("time_of_day", time_of_day)

    return ctx


def create_office_context(
    city: str,
    company_name: str | None = None,
    floor: int | None = None,
    people_count: int = 0,
    formality: str = "professional",
) -> SituationalContext:
    """Create a context for an office situation.

    Args:
        city: City location.
        company_name: Optional company name.
        floor: Optional floor number.
        people_count: Number of people present.
        formality: Level of formality.

    Returns:
        A configured SituationalContext.
    """
    ctx = SituationalContext(description=f"Office in {city}")

    ctx.add_location("city", city)
    ctx.add_location("venue_type", "office")
    ctx.add_location("indoor_outdoor", "indoor")

    if company_name:
        ctx.add_location("venue_name", company_name)

    if floor:
        ctx.add_location("floor", floor)

    ctx.add_social("people_count", people_count, unit="people")
    ctx.add_social("formality", formality)

    ctx.add_environment("atmosphere", "professional")
    ctx.add_environment("lighting", "fluorescent")

    return ctx


__all__ = [
    "SituationalContext",
    "create_coffee_shop_context",
    "create_office_context",
]
