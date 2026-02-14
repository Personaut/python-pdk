"""Fact extraction utilities for Personaut PDK.

This module provides utilities for extracting structured facts
from unstructured text descriptions.

Example:
    >>> from personaut.facts import FactExtractor
    >>> extractor = FactExtractor()
    >>> text = "We met at a busy coffee shop in downtown Miami around 3pm"
    >>> context = extractor.extract(text)
    >>> context.get_value("venue_type")
    'coffee shop'
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from personaut.facts.context import SituationalContext
from personaut.facts.fact import FactCategory


@dataclass
class ExtractionPattern:
    """A pattern for extracting facts from text.

    Attributes:
        category: The fact category to assign.
        key: The fact key to use.
        pattern: Regex pattern to match.
        group: Which regex group contains the value.
        transform: Optional function to transform the matched value.
    """

    category: FactCategory
    key: str
    pattern: str
    group: int = 1
    transform: Any | None = None


# Common extraction patterns
DEFAULT_PATTERNS: list[ExtractionPattern] = [
    # Location patterns
    ExtractionPattern(
        category=FactCategory.LOCATION,
        key="venue_type",
        pattern=r"\b(?:a|an|the)?\s*(coffee\s*shop|cafe|restaurant|bar|office|store|shop|mall|park|gym|library|museum|hotel|airport)\b",
    ),
    ExtractionPattern(
        category=FactCategory.LOCATION,
        key="city",
        pattern=r"\bin\s+(?:downtown\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z]{2})?)",
    ),
    ExtractionPattern(
        category=FactCategory.LOCATION,
        key="indoor_outdoor",
        pattern=r"\b(inside|indoors|indoor|outside|outdoors|outdoor)\b",
        transform=lambda x: "indoor" if "in" in x.lower() else "outdoor",
    ),
    # Temporal patterns
    ExtractionPattern(
        category=FactCategory.TEMPORAL,
        key="time_of_day",
        pattern=r"\b(morning|afternoon|evening|night|noon|midnight|dawn|dusk)\b",
    ),
    ExtractionPattern(
        category=FactCategory.TEMPORAL,
        key="time_approx",
        pattern=r"\b(?:around|at|about)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\b",
    ),
    ExtractionPattern(
        category=FactCategory.TEMPORAL,
        key="day_of_week",
        pattern=r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    ),
    # Environment patterns
    ExtractionPattern(
        category=FactCategory.ENVIRONMENT,
        key="crowd_level",
        pattern=r"\b(empty|quiet|sparse|moderate|busy|crowded|packed|bustling)\b",
    ),
    ExtractionPattern(
        category=FactCategory.ENVIRONMENT,
        key="capacity_percent",
        pattern=r"(\d{1,3})(?:\s*%|\s*percent)\s*(?:capacity|full|filled)",
        transform=lambda x: int(x),
    ),
    ExtractionPattern(
        category=FactCategory.ENVIRONMENT,
        key="noise_level",
        pattern=r"\b(quiet|silent|noisy|loud|deafening)\b",
    ),
    ExtractionPattern(
        category=FactCategory.ENVIRONMENT,
        key="atmosphere",
        pattern=r"\b(relaxed|tense|professional|casual|formal|festive|romantic|cozy|hectic)\b",
    ),
    # Behavioral patterns
    ExtractionPattern(
        category=FactCategory.BEHAVIORAL,
        key="queue_length",
        pattern=r"\b(?:line|queue)\s+(?:of\s+)?(\d+)(?:\s+(?:people|customers))?\b",
        transform=lambda x: int(x),
    ),
    ExtractionPattern(
        category=FactCategory.BEHAVIORAL,
        key="wait_time",
        pattern=r"(\d+)\s*(?:minute|min)s?\s*(?:wait|waiting)",
        transform=lambda x: int(x),
    ),
    # Social patterns
    ExtractionPattern(
        category=FactCategory.SOCIAL,
        key="people_count",
        pattern=r"(\d+)\s+(?:people|customers|guests|attendees|participants)",
        transform=lambda x: int(x),
    ),
    ExtractionPattern(
        category=FactCategory.SOCIAL,
        key="relationship_type",
        pattern=r"\b(strangers?|colleagues?|coworkers?|friends?|family|couples?)\b",
    ),
    # Physical patterns
    ExtractionPattern(
        category=FactCategory.PHYSICAL,
        key="temperature",
        pattern=r"(\d+)\s*(?:degrees?|°)\s*(?:F|C|fahrenheit|celsius)?",
        transform=lambda x: int(x),
    ),
    # Sensory patterns
    ExtractionPattern(
        category=FactCategory.SENSORY,
        key="smell",
        pattern=r"(?:smell(?:ed|s)?|scent|aroma)\s+(?:of\s+)?(\w+(?:\s+\w+)?)",
    ),
]


@dataclass
class FactExtractor:
    """Extracts structured facts from unstructured text.

    The extractor uses pattern matching to identify and extract
    facts from natural language descriptions.

    Attributes:
        patterns: List of extraction patterns to apply.
        confidence_default: Default confidence for extracted facts.

    Example:
        >>> extractor = FactExtractor()
        >>> ctx = extractor.extract("A busy coffee shop in Miami")
        >>> ctx.get_value("venue_type")
        'coffee shop'
    """

    patterns: list[ExtractionPattern] = field(default_factory=lambda: list(DEFAULT_PATTERNS))
    confidence_default: float = 0.8

    def extract(self, text: str, existing_context: SituationalContext | None = None) -> SituationalContext:
        """Extract facts from text.

        Args:
            text: The text to extract facts from.
            existing_context: Optional existing context to add facts to.

        Returns:
            A SituationalContext with extracted facts.

        Example:
            >>> extractor = FactExtractor()
            >>> ctx = extractor.extract(
            ...     "We met at a cozy coffee shop in downtown Miami around 3pm. "
            ...     "It was 80% capacity with a line of 5 people."
            ... )
            >>> ctx.get_value("venue_type")
            'coffee shop'
            >>> ctx.get_value("capacity_percent")
            80
            >>> ctx.get_value("queue_length")
            5
        """
        context = existing_context.copy() if existing_context else SituationalContext()
        context.description = text[:200] if len(text) > 200 else text

        for pattern in self.patterns:
            match = re.search(pattern.pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = match.group(pattern.group)
                    if pattern.transform:
                        value = pattern.transform(value)

                    # Don't duplicate existing keys
                    if pattern.key not in context:
                        self._add_fact_to_context(
                            context,
                            pattern.category,
                            pattern.key,
                            value,
                        )
                except (IndexError, ValueError):
                    pass  # Pattern matched but value extraction failed

        return context

    def _add_fact_to_context(
        self,
        context: SituationalContext,
        category: FactCategory,
        key: str,
        value: Any,
    ) -> None:
        """Add a fact to the context based on category."""
        # Determine unit based on key
        unit = None
        if key == "capacity_percent":
            unit = "percent"
        elif key in ("queue_length", "people_count"):
            unit = "people"
        elif key in ("wait_time",):
            unit = "minutes"
        elif key == "temperature":
            unit = "°F"  # Default to Fahrenheit

        if category == FactCategory.LOCATION:
            context.add_location(key, value, confidence=self.confidence_default)
        elif category == FactCategory.ENVIRONMENT:
            context.add_environment(key, value, unit=unit, confidence=self.confidence_default)
        elif category == FactCategory.TEMPORAL:
            context.add_temporal(key, value, confidence=self.confidence_default)
        elif category == FactCategory.SOCIAL:
            context.add_social(key, value, unit=unit, confidence=self.confidence_default)
        elif category == FactCategory.BEHAVIORAL:
            context.add_behavioral(key, value, unit=unit, confidence=self.confidence_default)
        elif category == FactCategory.SENSORY:
            context.add_sensory(key, value, confidence=self.confidence_default)

    def add_pattern(self, pattern: ExtractionPattern) -> None:
        r"""Add a custom extraction pattern.

        Args:
            pattern: The pattern to add.

        Example:
            >>> extractor = FactExtractor()
            >>> pattern = ExtractionPattern(
            ...     category=FactCategory.LOCATION,
            ...     key="parking",
            ...     pattern=r"(free|paid|no)\s+parking",
            ... )
            >>> extractor.add_pattern(pattern)
        """
        self.patterns.append(pattern)

    def extract_all_matches(self, text: str) -> list[tuple[str, str, Any]]:
        """Extract all pattern matches as raw tuples.

        Args:
            text: The text to search.

        Returns:
            List of (key, category, value) tuples.

        Example:
            >>> extractor = FactExtractor()
            >>> matches = extractor.extract_all_matches("busy coffee shop")
            >>> len(matches) > 0
            True
        """
        matches = []
        for pattern in self.patterns:
            match = re.search(pattern.pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = match.group(pattern.group)
                    if pattern.transform:
                        value = pattern.transform(value)
                    matches.append((pattern.key, pattern.category.value, value))
                except (IndexError, ValueError):
                    pass
        return matches


__all__ = [
    "DEFAULT_PATTERNS",
    "ExtractionPattern",
    "FactExtractor",
]
