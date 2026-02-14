"""Fact definitions for Personaut PDK.

This module defines structured facts that capture situational context
for memories and simulations. Facts are concrete, extractable details
about locations, environments, timing, and other contextual elements.

Example:
    >>> from personaut.facts import Fact, FactCategory
    >>> fact = Fact(
    ...     category=FactCategory.LOCATION,
    ...     key="city",
    ...     value="Miami, FL",
    ...     confidence=0.95,
    ... )
    >>> print(fact.to_embedding_text())
    city: Miami, FL
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FactCategory(str, Enum):
    """Categories of situational facts.

    Facts are organized into categories for easier processing
    and embedding generation.

    Attributes:
        LOCATION: Physical location details (city, venue, address).
        ENVIRONMENT: Environmental conditions (crowd, noise, weather).
        TEMPORAL: Time-related facts (time of day, day of week, season).
        SOCIAL: Social context (number of people, relationships).
        PHYSICAL: Physical conditions (temperature, lighting).
        BEHAVIORAL: Observable behaviors (queue length, activity level).
        ECONOMIC: Economic factors (prices, demand indicators).
        SENSORY: Sensory details (sounds, smells, textures).

    Example:
        >>> FactCategory.LOCATION.description
        'Physical location and venue details'
    """

    LOCATION = "location"
    ENVIRONMENT = "environment"
    TEMPORAL = "temporal"
    SOCIAL = "social"
    PHYSICAL = "physical"
    BEHAVIORAL = "behavioral"
    ECONOMIC = "economic"
    SENSORY = "sensory"

    @property
    def description(self) -> str:
        """Get a description of this fact category."""
        descriptions = {
            FactCategory.LOCATION: "Physical location and venue details",
            FactCategory.ENVIRONMENT: "Environmental and atmospheric conditions",
            FactCategory.TEMPORAL: "Time-related contextual information",
            FactCategory.SOCIAL: "Social dynamics and interpersonal context",
            FactCategory.PHYSICAL: "Physical conditions and measurements",
            FactCategory.BEHAVIORAL: "Observable behaviors and patterns",
            FactCategory.ECONOMIC: "Economic and transactional factors",
            FactCategory.SENSORY: "Sensory perceptions and experiences",
        }
        return descriptions[self]

    @property
    def embedding_weight(self) -> float:
        """Get the relative weight for embedding generation.

        Higher weights mean this category is more important
        for distinguishing between situations.

        Returns:
            Weight between 0.5 and 1.0.
        """
        weights = {
            FactCategory.LOCATION: 1.0,
            FactCategory.ENVIRONMENT: 0.8,
            FactCategory.TEMPORAL: 0.7,
            FactCategory.SOCIAL: 0.9,
            FactCategory.PHYSICAL: 0.6,
            FactCategory.BEHAVIORAL: 0.8,
            FactCategory.ECONOMIC: 0.5,
            FactCategory.SENSORY: 0.7,
        }
        return weights[self]


@dataclass(frozen=True, slots=True)
class Fact:
    """A single situational fact.

    Facts are immutable, structured pieces of information that
    capture concrete details about a situation or context.

    Attributes:
        category: The category of this fact.
        key: A short identifier for the fact type.
        value: The fact value (can be string, number, bool, etc.).
        unit: Optional unit of measurement (e.g., "people", "°F").
        confidence: Confidence in the fact's accuracy (0.0 to 1.0).
        source: Where this fact was derived from.
        metadata: Additional key-value pairs.

    Example:
        >>> fact = Fact(
        ...     category=FactCategory.ENVIRONMENT,
        ...     key="capacity",
        ...     value=80,
        ...     unit="percent",
        ...     confidence=0.9,
        ... )
        >>> fact.to_embedding_text()
        'capacity: 80 percent'
    """

    category: FactCategory
    key: str
    value: Any
    unit: str | None = None
    confidence: float = 1.0
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fact attributes."""
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            raise ValueError(msg)

    def to_embedding_text(self) -> str:
        """Convert this fact to text for embedding generation.

        Returns:
            A human-readable string representation.

        Example:
            >>> fact = Fact(FactCategory.LOCATION, "city", "Miami")
            >>> fact.to_embedding_text()
            'city: Miami'
        """
        if self.unit:
            return f"{self.key}: {self.value} {self.unit}"
        return f"{self.key}: {self.value}"

    def to_dict(self) -> dict[str, Any]:
        """Convert this fact to a dictionary.

        Returns:
            Dictionary representation of the fact.
        """
        return {
            "category": self.category.value,
            "key": self.key,
            "value": self.value,
            "unit": self.unit,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fact:
        """Create a Fact from a dictionary.

        Args:
            data: Dictionary with fact data.

        Returns:
            A new Fact instance.
        """
        category = FactCategory(data["category"])
        return cls(
            category=category,
            key=data["key"],
            value=data["value"],
            unit=data.get("unit"),
            confidence=data.get("confidence", 1.0),
            source=data.get("source"),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """Return a string representation."""
        return self.to_embedding_text()


# Common fact templates for easy creation
LOCATION_FACTS = {
    "city": "The city or municipality",
    "state": "The state or province",
    "country": "The country",
    "venue_type": "Type of venue (cafe, office, park, etc.)",
    "venue_name": "Specific venue name",
    "address": "Street address",
    "neighborhood": "Neighborhood or district",
    "indoor_outdoor": "Whether inside or outside",
}

ENVIRONMENT_FACTS = {
    "crowd_level": "Relative crowdedness (empty, sparse, moderate, busy, packed)",
    "capacity_percent": "Percentage of capacity filled",
    "noise_level": "Ambient noise level (quiet, moderate, loud)",
    "lighting": "Lighting conditions (dim, natural, bright, fluorescent)",
    "cleanliness": "How clean the space is (1-10)",
    "atmosphere": "Overall atmosphere (relaxed, professional, festive, tense)",
}

TEMPORAL_FACTS = {
    "time_of_day": "Time period (morning, afternoon, evening, night)",
    "day_of_week": "Day of the week",
    "season": "Current season",
    "holiday": "If a holiday, which one",
    "rush_hour": "Whether it's during rush hour",
    "duration": "How long something lasted",
}

SOCIAL_FACTS = {
    "people_count": "Number of people present",
    "group_size": "Size of the group involved",
    "age_range": "Approximate age range of people",
    "formality": "Social formality level (casual, semi-formal, formal)",
    "familiarity": "How well people know each other",
    "relationship_type": "Type of relationship (strangers, colleagues, friends, family)",
}

BEHAVIORAL_FACTS = {
    "queue_length": "Number of people in line/queue",
    "wait_time": "Expected or actual wait time",
    "activity_level": "Level of activity (idle, moderate, busy, hectic)",
    "movement_pattern": "How people are moving (stationary, browsing, rushing)",
    "service_speed": "Speed of service (slow, average, fast)",
}

SENSORY_FACTS = {
    "temperature": "Temperature (actual or perceived)",
    "smell": "Prominent smells",
    "sound": "Prominent sounds",
    "texture": "Notable textures or surfaces",
    "taste": "If applicable, tastes experienced",
}


def create_location_fact(
    key: str,
    value: Any,
    confidence: float = 1.0,
    **metadata: Any,
) -> Fact:
    """Create a location fact.

    Args:
        key: The fact key (e.g., "city", "venue_type").
        value: The fact value.
        confidence: Confidence in the fact.
        **metadata: Additional metadata.

    Returns:
        A new Fact with LOCATION category.

    Example:
        >>> fact = create_location_fact("city", "Miami, FL")
        >>> fact.category
        <FactCategory.LOCATION: 'location'>
    """
    return Fact(
        category=FactCategory.LOCATION,
        key=key,
        value=value,
        confidence=confidence,
        metadata=metadata,
    )


def create_environment_fact(
    key: str,
    value: Any,
    unit: str | None = None,
    confidence: float = 1.0,
    **metadata: Any,
) -> Fact:
    """Create an environment fact.

    Args:
        key: The fact key (e.g., "capacity_percent", "noise_level").
        value: The fact value.
        unit: Optional unit of measurement.
        confidence: Confidence in the fact.
        **metadata: Additional metadata.

    Returns:
        A new Fact with ENVIRONMENT category.

    Example:
        >>> fact = create_environment_fact("capacity_percent", 80, unit="percent")
        >>> str(fact)
        'capacity_percent: 80 percent'
    """
    return Fact(
        category=FactCategory.ENVIRONMENT,
        key=key,
        value=value,
        unit=unit,
        confidence=confidence,
        metadata=metadata,
    )


def create_behavioral_fact(
    key: str,
    value: Any,
    unit: str | None = None,
    confidence: float = 1.0,
    **metadata: Any,
) -> Fact:
    """Create a behavioral fact.

    Args:
        key: The fact key (e.g., "queue_length", "wait_time").
        value: The fact value.
        unit: Optional unit of measurement.
        confidence: Confidence in the fact.
        **metadata: Additional metadata.

    Returns:
        A new Fact with BEHAVIORAL category.

    Example:
        >>> fact = create_behavioral_fact("queue_length", 5, unit="people")
        >>> str(fact)
        'queue_length: 5 people'
    """
    return Fact(
        category=FactCategory.BEHAVIORAL,
        key=key,
        value=value,
        unit=unit,
        confidence=confidence,
        metadata=metadata,
    )


__all__ = [
    # Fact templates
    "BEHAVIORAL_FACTS",
    "ENVIRONMENT_FACTS",
    "LOCATION_FACTS",
    "SENSORY_FACTS",
    "SOCIAL_FACTS",
    "TEMPORAL_FACTS",
    # Classes
    "Fact",
    "FactCategory",
    # Factory functions
    "create_behavioral_fact",
    "create_environment_fact",
    "create_location_fact",
]
