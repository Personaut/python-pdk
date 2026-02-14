"""Emotion categories for Personaut PDK.

This module defines the six major emotional categories and provides
functions for working with emotion-category relationships.

Each category represents a cluster of related emotions that share
underlying psychological characteristics.

Example:
    >>> from personaut.emotions.categories import EmotionCategory, get_category
    >>> category = get_category("anxious")
    >>> print(category)
    EmotionCategory.FEAR
"""

from __future__ import annotations

from enum import Enum

from personaut.emotions.emotion import (
    ANGER_EMOTIONS,
    FEAR_EMOTIONS,
    JOY_EMOTIONS,
    PEACEFUL_EMOTIONS,
    POWERFUL_EMOTIONS,
    SAD_EMOTIONS,
)


class EmotionCategory(str, Enum):
    """Major emotional category classification.

    The six categories represent the primary emotional clusters
    used in the Personaut emotion modeling system.

    Attributes:
        ANGER: Hostile, aggressive, and frustrated emotions.
        SAD: Depressive, lonely, and disengaged emotions.
        FEAR: Anxious, insecure, and helpless emotions.
        JOY: Happy, energetic, and hopeful emotions.
        POWERFUL: Confident, proud, and satisfied emotions.
        PEACEFUL: Calm, loving, and trusting emotions.

    Example:
        >>> category = EmotionCategory.JOY
        >>> print(category.description)
        Happy, energetic, and hopeful emotions
    """

    ANGER = "anger"
    SAD = "sad"
    FEAR = "fear"
    JOY = "joy"
    POWERFUL = "powerful"
    PEACEFUL = "peaceful"

    @property
    def description(self) -> str:
        """Get a description of this emotion category.

        Returns:
            Human-readable description of the category.
        """
        descriptions = {
            EmotionCategory.ANGER: "Hostile, aggressive, and frustrated emotions",
            EmotionCategory.SAD: "Depressive, lonely, and disengaged emotions",
            EmotionCategory.FEAR: "Anxious, insecure, and helpless emotions",
            EmotionCategory.JOY: "Happy, energetic, and hopeful emotions",
            EmotionCategory.POWERFUL: "Confident, proud, and satisfied emotions",
            EmotionCategory.PEACEFUL: "Calm, loving, and trusting emotions",
        }
        return descriptions[self]

    @property
    def is_positive(self) -> bool:
        """Check if this is a positive emotional category.

        Returns:
            True if the category represents positive emotions.
        """
        return self in {EmotionCategory.JOY, EmotionCategory.POWERFUL, EmotionCategory.PEACEFUL}

    @property
    def is_negative(self) -> bool:
        """Check if this is a negative emotional category.

        Returns:
            True if the category represents negative emotions.
        """
        return self in {EmotionCategory.ANGER, EmotionCategory.SAD, EmotionCategory.FEAR}

    @property
    def valence(self) -> float:
        """Get the valence (positive/negative) of this category.

        Returns:
            A value from -1.0 (very negative) to 1.0 (very positive).
        """
        valences = {
            EmotionCategory.ANGER: -0.8,
            EmotionCategory.SAD: -0.6,
            EmotionCategory.FEAR: -0.7,
            EmotionCategory.JOY: 0.9,
            EmotionCategory.POWERFUL: 0.7,
            EmotionCategory.PEACEFUL: 0.8,
        }
        return valences[self]

    @property
    def arousal(self) -> float:
        """Get the arousal level (activation) of this category.

        Returns:
            A value from 0.0 (low arousal) to 1.0 (high arousal).
        """
        arousal_levels = {
            EmotionCategory.ANGER: 0.9,
            EmotionCategory.SAD: 0.2,
            EmotionCategory.FEAR: 0.8,
            EmotionCategory.JOY: 0.8,
            EmotionCategory.POWERFUL: 0.6,
            EmotionCategory.PEACEFUL: 0.2,
        }
        return arousal_levels[self]


# Mapping from category to emotions
CATEGORY_EMOTIONS: dict[EmotionCategory, list[str]] = {
    EmotionCategory.ANGER: ANGER_EMOTIONS,
    EmotionCategory.SAD: SAD_EMOTIONS,
    EmotionCategory.FEAR: FEAR_EMOTIONS,
    EmotionCategory.JOY: JOY_EMOTIONS,
    EmotionCategory.POWERFUL: POWERFUL_EMOTIONS,
    EmotionCategory.PEACEFUL: PEACEFUL_EMOTIONS,
}
"""Mapping from each category to its constituent emotions."""


# Mapping from emotion to category (built from CATEGORY_EMOTIONS)
_EMOTION_TO_CATEGORY: dict[str, EmotionCategory] = {}
for _category, _emotions in CATEGORY_EMOTIONS.items():
    for _emotion in _emotions:
        _EMOTION_TO_CATEGORY[_emotion] = _category


def get_category(emotion: str) -> EmotionCategory:
    """Get the category for a given emotion.

    Args:
        emotion: Name of the emotion (lowercase).

    Returns:
        The EmotionCategory this emotion belongs to.

    Raises:
        KeyError: If the emotion is not recognized.

    Example:
        >>> get_category("anxious")
        <EmotionCategory.FEAR: 'fear'>
        >>> get_category("hopeful")
        <EmotionCategory.JOY: 'joy'>
    """
    return _EMOTION_TO_CATEGORY[emotion]


def get_emotions_in_category(category: EmotionCategory) -> list[str]:
    """Get all emotions belonging to a category.

    Args:
        category: The emotion category to query.

    Returns:
        List of emotion names in this category.

    Example:
        >>> emotions = get_emotions_in_category(EmotionCategory.JOY)
        >>> "hopeful" in emotions
        True
    """
    return list(CATEGORY_EMOTIONS[category])


def get_positive_emotions() -> list[str]:
    """Get all emotions from positive categories.

    Returns:
        List of emotion names from JOY, POWERFUL, and PEACEFUL categories.

    Example:
        >>> positive = get_positive_emotions()
        >>> "hopeful" in positive
        True
        >>> "anxious" in positive
        False
    """
    result: list[str] = []
    for category in EmotionCategory:
        if category.is_positive:
            result.extend(CATEGORY_EMOTIONS[category])
    return result


def get_negative_emotions() -> list[str]:
    """Get all emotions from negative categories.

    Returns:
        List of emotion names from ANGER, SAD, and FEAR categories.

    Example:
        >>> negative = get_negative_emotions()
        >>> "anxious" in negative
        True
        >>> "hopeful" in negative
        False
    """
    result: list[str] = []
    for category in EmotionCategory:
        if category.is_negative:
            result.extend(CATEGORY_EMOTIONS[category])
    return result


def parse_category(value: str | EmotionCategory) -> EmotionCategory:
    """Parse a string or EmotionCategory into an EmotionCategory enum.

    Args:
        value: String value or EmotionCategory enum.

    Returns:
        The corresponding EmotionCategory.

    Raises:
        ValueError: If the value is not a valid category.

    Example:
        >>> parse_category("joy")
        <EmotionCategory.JOY: 'joy'>
    """
    if isinstance(value, EmotionCategory):
        return value

    try:
        return EmotionCategory(value)
    except ValueError:
        valid = [c.value for c in EmotionCategory]
        msg = f"Invalid emotion category '{value}'. Valid options: {valid}"
        raise ValueError(msg) from None


__all__ = [
    "CATEGORY_EMOTIONS",
    "EmotionCategory",
    "get_category",
    "get_emotions_in_category",
    "get_negative_emotions",
    "get_positive_emotions",
    "parse_category",
]
