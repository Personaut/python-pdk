"""Personality component for prompt generation.

This module provides the PersonalityComponent class that converts
personality traits into natural language behavioral descriptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from personaut.traits.trait import TRAIT_METADATA, get_trait_metadata


if TYPE_CHECKING:
    from personaut.traits.profile import TraitProfile


# Interpretation thresholds
HIGH_THRESHOLD = 0.7
LOW_THRESHOLD = 0.3
NEUTRAL_RANGE = (0.4, 0.6)


def interpret_trait_value(trait: str, value: float) -> str | None:
    """Interpret a trait value as a behavioral description.

    Args:
        trait: Name of the trait.
        value: Trait value from 0.0 to 1.0.

    Returns:
        Description of the trait manifestation, or None if neutral.

    Example:
        >>> interpret_trait_value("warmth", 0.9)
        'warm, outgoing, attentive'
    """
    if trait not in TRAIT_METADATA:
        return None

    metadata = get_trait_metadata(trait)

    if value >= HIGH_THRESHOLD:
        return metadata.high_pole.lower()
    elif value <= LOW_THRESHOLD:
        return metadata.low_pole.lower()
    else:
        return None  # Neutral range


def get_trait_description(trait: str, value: float) -> str:
    """Get a full description of how a trait manifests.

    Args:
        trait: Name of the trait.
        value: Trait value from 0.0 to 1.0.

    Returns:
        Natural language description of trait manifestation.
    """
    if trait not in TRAIT_METADATA:
        return f"has a {trait} score of {value:.1f}"

    metadata = get_trait_metadata(trait)

    if value >= 0.8:
        intensity = "very"
    elif value >= HIGH_THRESHOLD:
        intensity = "notably"
    elif value <= 0.2:
        intensity = "very"
    elif value <= LOW_THRESHOLD:
        intensity = "somewhat"
    else:
        return f"has moderate {trait}"

    if value >= HIGH_THRESHOLD:
        pole_desc = metadata.high_pole.split(",")[0].strip().lower()
    else:
        pole_desc = metadata.low_pole.split(",")[0].strip().lower()

    return f"is {intensity} {pole_desc}"


@dataclass
class PersonalityComponent:
    """Component for formatting personality traits into prompt text.

    This component converts a TraitProfile into natural language
    that describes the individual's personality and behavioral tendencies.

    Attributes:
        include_neutral: Whether to include neutral traits.
        high_threshold: Minimum value to be considered high.
        low_threshold: Maximum value to be considered low.

    Example:
        >>> component = PersonalityComponent()
        >>> text = component.format(trait_profile)
    """

    include_neutral: bool = False
    high_threshold: float = 0.7
    low_threshold: float = 0.3

    def format(
        self,
        traits: TraitProfile,
        *,
        name: str = "They",
        style: str = "narrative",
    ) -> str:
        """Format a trait profile into natural language.

        Args:
            traits: The trait profile to format.
            name: Name to use in the description.
            style: Output style ("narrative", "list", or "brief").

        Returns:
            Natural language description of personality.
        """
        if style == "list":
            return self._format_list(traits, name)
        elif style == "brief":
            return self._format_brief(traits, name)
        else:
            return self._format_narrative(traits, name)

    def _format_narrative(self, traits: TraitProfile, name: str) -> str:
        """Format traits as a narrative paragraph."""
        high_traits = traits.get_high_traits(threshold=self.high_threshold)
        low_traits = traits.get_low_traits(threshold=self.low_threshold)

        if not high_traits and not low_traits:
            return f"{name} has a fairly balanced personality without extreme tendencies."

        parts = []

        # Describe high traits
        if high_traits:
            high_descriptions = []
            for trait, value in high_traits[:3]:  # Limit to top 3
                interpretation = interpret_trait_value(trait, value)
                if interpretation:
                    high_descriptions.append(interpretation)

            if high_descriptions:
                if len(high_descriptions) == 1:
                    parts.append(f"{name} tends to be {high_descriptions[0]}")
                else:
                    joined = self._join_list(high_descriptions)
                    parts.append(f"{name} tends to be {joined}")

        # Describe low traits as contrasts
        if low_traits:
            low_descriptions = []
            for trait, value in low_traits[:2]:  # Limit to bottom 2
                interpretation = interpret_trait_value(trait, value)
                if interpretation:
                    low_descriptions.append(interpretation)

            if low_descriptions:
                joined = self._join_list(low_descriptions)
                if parts:
                    parts.append(f"but can also be {joined}")
                else:
                    parts.append(f"{name} tends to be {joined}")

        if not parts:
            return f"{name} has a fairly balanced personality."

        return ". ".join(parts) + "."

    def _format_list(self, traits: TraitProfile, name: str) -> str:
        """Format traits as a bulleted list."""
        high_traits = traits.get_high_traits(threshold=self.high_threshold)
        low_traits = traits.get_low_traits(threshold=self.low_threshold)

        lines = [f"{name}'s personality traits:"]

        for trait, value in high_traits:
            desc = get_trait_description(trait, value)
            lines.append(f"  - {trait.replace('_', ' ').title()}: {desc}")

        for trait, value in low_traits:
            desc = get_trait_description(trait, value)
            lines.append(f"  - {trait.replace('_', ' ').title()}: {desc}")

        if len(lines) == 1:
            lines.append("  - Balanced across all traits")

        return "\n".join(lines)

    def _format_brief(self, traits: TraitProfile, name: str) -> str:
        """Format as a brief one-line summary."""
        extremes = traits.get_extreme_traits(
            low_threshold=self.low_threshold,
            high_threshold=self.high_threshold,
        )

        descriptors = []

        for trait, value in extremes["high"][:2]:
            interpretation = interpret_trait_value(trait, value)
            if interpretation:
                # Take first word
                descriptors.append(interpretation.split(",")[0].strip())

        for trait, value in extremes["low"][:1]:
            interpretation = interpret_trait_value(trait, value)
            if interpretation:
                descriptors.append(interpretation.split(",")[0].strip())

        if not descriptors:
            return "balanced personality"

        return self._join_list(descriptors)

    def _join_list(self, items: list[str]) -> str:
        """Join list items with proper punctuation."""
        if len(items) == 0:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"


__all__ = [
    "PersonalityComponent",
    "get_trait_description",
    "interpret_trait_value",
]
