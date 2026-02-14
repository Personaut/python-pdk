"""Emotional state component for prompt generation.

This module provides the EmotionalStateComponent class that converts
an EmotionalState into natural language descriptions with intensity
awareness and category grouping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState


# Intensity labels for emotional values
INTENSITY_LABELS: list[tuple[float, str]] = [
    (0.0, "minimal"),
    (0.2, "slight"),
    (0.4, "noticeable"),
    (0.6, "significant"),
    (0.8, "overwhelming"),
]


def get_intensity_label(value: float) -> str:
    """Get the intensity label for an emotion value.

    Args:
        value: Emotion intensity from 0.0 to 1.0.

    Returns:
        Human-readable intensity label.

    Example:
        >>> get_intensity_label(0.7)
        'significant'
    """
    label = "minimal"
    for threshold, name in INTENSITY_LABELS:
        if value >= threshold:
            label = name
    return label


def get_intensity_description(emotion: str, value: float) -> str:
    """Get a full description of an emotion with its intensity.

    Args:
        emotion: Name of the emotion.
        value: Intensity from 0.0 to 1.0.

    Returns:
        Description like "significant anxiety".
    """
    intensity = get_intensity_label(value)
    return f"{intensity} {emotion}"


@dataclass
class EmotionalStateComponent:
    """Component for formatting emotional state into prompt text.

    This component converts an EmotionalState into natural language
    that describes the individual's current emotional condition.

    Attributes:
        intensity_threshold: Minimum intensity to include an emotion.
        max_emotions: Maximum number of emotions to describe.
        group_by_category: Whether to group emotions by category.

    Example:
        >>> component = EmotionalStateComponent()
        >>> text = component.format(emotional_state)
    """

    intensity_threshold: float = 0.2
    max_emotions: int = 5
    group_by_category: bool = True

    def format(
        self,
        emotional_state: EmotionalState,
        *,
        highlight_dominant: bool = False,
        name: str = "They",
    ) -> str:
        """Format an emotional state into natural language.

        Args:
            emotional_state: The emotional state to format.
            highlight_dominant: Whether to emphasize the dominant emotion.
            name: Name to use in the description (default "They").

        Returns:
            Natural language description of the emotional state.
        """
        # Get emotions above threshold
        emotions = emotional_state.to_dict()
        active_emotions = [(emotion, value) for emotion, value in emotions.items() if value >= self.intensity_threshold]

        if not active_emotions:
            return f"{name} is in a relatively neutral emotional state."

        # Sort by intensity
        active_emotions.sort(key=lambda x: (-x[1], x[0]))

        # Limit to max emotions
        active_emotions = active_emotions[: self.max_emotions]

        # Build the core description
        if highlight_dominant and active_emotions:
            dominant_emotion, dominant_value = active_emotions[0]
            dominant_desc = get_intensity_description(dominant_emotion, dominant_value)

            if len(active_emotions) == 1:
                base_text = (
                    f"{name} is primarily feeling {dominant_desc}, which dominates their current emotional experience."
                )
            else:
                others = active_emotions[1:]
                other_descs = [get_intensity_description(e, v) for e, v in others]
                other_text = self._format_list(other_descs)
                base_text = (
                    f"{name} is primarily feeling {dominant_desc}, "
                    f"which colors their other emotional experiences: {other_text}."
                )
        elif self.group_by_category:
            base_text = self._format_grouped(active_emotions, name)
        else:
            base_text = self._format_flat(active_emotions, name)

        # Add volatility and mood context if available
        volatility_text = ""
        if hasattr(emotional_state, "get_emotional_volatility"):
            volatility = emotional_state.get_emotional_volatility()
            if volatility > 0.3:
                volatility_text = (
                    f" {name} is in a highly emotionally charged state — far from their emotional equilibrium."
                )
            elif volatility > 0.15:
                volatility_text = (
                    f" {name} is somewhat emotionally stirred — noticeably shifted from their usual baseline."
                )
            elif volatility > 0.05:
                volatility_text = f" {name}'s emotional state is close to their natural resting point."

        return base_text + volatility_text

    def _format_flat(
        self,
        emotions: list[tuple[str, float]],
        name: str,
    ) -> str:
        """Format emotions as a flat list."""
        if len(emotions) == 1:
            emotion, value = emotions[0]
            desc = get_intensity_description(emotion, value)
            return f"{name} is feeling {desc}."

        descriptions = [get_intensity_description(e, v) for e, v in emotions]
        emotion_list = self._format_list(descriptions)
        return f"{name} is experiencing {emotion_list}."

    def _format_grouped(
        self,
        emotions: list[tuple[str, float]],
        name: str,
    ) -> str:
        """Format emotions grouped by category."""
        # Import here to avoid circular imports
        from personaut.emotions.categories import (
            EmotionCategory,
            get_category,
        )

        # Group by category
        groups: dict[EmotionCategory, list[tuple[str, float]]] = {}
        for emotion, value in emotions:
            try:
                category = get_category(emotion)
            except KeyError:
                # Unknown emotion, skip grouping
                return self._format_flat(emotions, name)

            if category not in groups:
                groups[category] = []
            groups[category].append((emotion, value))

        # If only one category, format as a cluster
        if len(groups) == 1:
            category = next(iter(groups))
            category_emotions = groups[category]
            descriptions = [get_intensity_description(e, v) for e, v in category_emotions]
            emotion_list = self._format_list(descriptions)
            return f"{name} is experiencing a cluster of {category.value.lower()}-based emotions: {emotion_list}."

        # Multiple categories - describe each
        parts = []
        for _category, category_emotions in sorted(groups.items(), key=lambda x: x[0].value):
            if len(category_emotions) == 1:
                emotion, value = category_emotions[0]
                desc = get_intensity_description(emotion, value)
                parts.append(f"{desc}")
            else:
                descriptions = [get_intensity_description(e, v) for e, v in category_emotions]
                parts.append(self._format_list(descriptions))

        emotion_text = self._format_list(parts)
        return f"{name} is feeling {emotion_text}."

    def _format_list(self, items: list[str]) -> str:
        """Format a list with proper punctuation."""
        if len(items) == 0:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"

    def format_brief(
        self,
        emotional_state: EmotionalState,
    ) -> str:
        """Generate a brief one-line summary of emotional state.

        Args:
            emotional_state: The emotional state to summarize.

        Returns:
            Brief summary suitable for inline use.
        """
        dominant = emotional_state.get_dominant()
        if dominant[1] < self.intensity_threshold:
            return "neutral"

        return get_intensity_description(dominant[0], dominant[1])


__all__ = [
    "INTENSITY_LABELS",
    "EmotionalStateComponent",
    "get_intensity_description",
    "get_intensity_label",
]
