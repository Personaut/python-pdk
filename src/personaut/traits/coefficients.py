"""Trait-Emotion Coefficients for Personaut PDK.

This module defines the relationships between personality traits and
emotional states. Each trait has coefficients that modify the likelihood
or intensity of certain emotions.

Coefficients range from -1.0 to 1.0:
- Positive values: trait increases emotion intensity
- Negative values: trait decreases emotion intensity
- Zero/absent: no relationship

Example:
    >>> from personaut.traits.coefficients import get_coefficient, get_affected_emotions
    >>> get_coefficient("warmth", "loving")
    0.4
    >>> get_affected_emotions("warmth")
    ['loving', 'trusting', 'hostile', 'nurturing', 'critical', 'lonely']
"""

from __future__ import annotations

from personaut.traits.trait import (
    ABSTRACTEDNESS,
    APPREHENSION,
    DOMINANCE,
    EMOTIONAL_STABILITY,
    HUMILITY,
    LIVELINESS,
    OPENNESS_TO_CHANGE,
    PERFECTIONISM,
    PRIVATENESS,
    REASONING,
    RULE_CONSCIOUSNESS,
    SELF_RELIANCE,
    SENSITIVITY,
    SOCIAL_BOLDNESS,
    TENSION,
    VIGILANCE,
    WARMTH,
)


# =============================================================================
# Trait-Emotion Coefficient Mappings
# =============================================================================

TRAIT_COEFFICIENTS: dict[str, dict[str, float]] = {
    WARMTH: {
        "loving": 0.4,
        "trusting": 0.3,
        "nurturing": 0.3,
        "intimate": 0.3,
        "hostile": -0.5,
        "critical": -0.3,
        "lonely": -0.2,
        "hateful": -0.4,
    },
    REASONING: {
        "confused": -0.3,
        "creative": 0.2,
        "thoughtful": 0.3,
        "helpless": -0.2,
    },
    EMOTIONAL_STABILITY: {
        "anxious": -0.5,
        "depressed": -0.4,
        "angry": -0.3,
        "content": 0.4,
        "satisfied": 0.3,
        "helpless": -0.3,
        "guilty": -0.2,
        "ashamed": -0.2,
    },
    DOMINANCE: {
        "proud": 0.3,
        "important": 0.3,
        "respected": 0.3,
        "submissive": -0.5,
        "helpless": -0.3,
        "insecure": -0.3,
        "hostile": 0.2,
        "critical": 0.2,
    },
    HUMILITY: {
        "proud": -0.3,
        "important": -0.2,
        "appreciated": 0.2,
        "content": 0.2,
        "selfish": -0.4,
    },
    LIVELINESS: {
        "excited": 0.4,
        "cheerful": 0.4,
        "energetic": 0.4,
        "hopeful": 0.3,
        "bored": -0.4,
        "apathetic": -0.4,
        "depressed": -0.3,
    },
    RULE_CONSCIOUSNESS: {
        "guilty": 0.3,
        "ashamed": 0.2,
        "satisfied": 0.2,
        "faithful": 0.3,
        "selfish": -0.3,
    },
    SOCIAL_BOLDNESS: {
        "rejected": -0.4,
        "insecure": -0.4,
        "submissive": -0.3,
        "excited": 0.2,
        "energetic": 0.2,
        "respected": 0.2,
        "lonely": -0.2,
    },
    SENSITIVITY: {
        "loving": 0.3,
        "hurt": 0.3,
        "intimate": 0.3,
        "sensual": 0.3,
        "lonely": 0.2,
        "depressed": 0.2,
        "creative": 0.2,
    },
    VIGILANCE: {
        "trusting": -0.5,
        "anxious": 0.3,
        "hostile": 0.2,
        "critical": 0.3,
        "insecure": 0.2,
    },
    ABSTRACTEDNESS: {
        "creative": 0.4,
        "thoughtful": 0.3,
        "confused": 0.2,
        "bored": -0.2,
    },
    PRIVATENESS: {
        "intimate": -0.3,
        "trusting": -0.2,
        "insecure": 0.2,
        "lonely": 0.2,
    },
    APPREHENSION: {
        "anxious": 0.4,
        "guilty": 0.3,
        "ashamed": 0.3,
        "insecure": 0.4,
        "helpless": 0.3,
        "content": -0.3,
        "satisfied": -0.3,
        "proud": -0.3,
    },
    OPENNESS_TO_CHANGE: {
        "excited": 0.3,
        "creative": 0.3,
        "hopeful": 0.2,
        "anxious": 0.1,
        "bored": -0.3,
        "content": -0.1,
    },
    SELF_RELIANCE: {
        "lonely": 0.2,
        "rejected": -0.2,
        "important": 0.2,
        "trusting": -0.2,
        "intimate": -0.2,
    },
    PERFECTIONISM: {
        "satisfied": 0.2,
        "guilty": 0.2,
        "angry": 0.3,
        "critical": 0.3,
        "anxious": 0.2,
    },
    TENSION: {
        "anxious": 0.4,
        "angry": 0.4,
        "hostile": 0.3,
        "content": -0.4,
        "energetic": 0.2,
    },
}
"""Mapping of traits to their emotion coefficients."""


def get_coefficient(trait: str, emotion: str) -> float:
    """Get the coefficient for a trait-emotion pair.

    Args:
        trait: Name of the trait.
        emotion: Name of the emotion.

    Returns:
        The coefficient value, or 0.0 if no relationship exists.

    Example:
        >>> get_coefficient("warmth", "loving")
        0.4
        >>> get_coefficient("warmth", "excited")
        0.0
    """
    trait_coeffs = TRAIT_COEFFICIENTS.get(trait, {})
    return trait_coeffs.get(emotion, 0.0)


def get_affected_emotions(trait: str) -> list[str]:
    """Get all emotions affected by a trait.

    Args:
        trait: Name of the trait.

    Returns:
        List of emotion names that have non-zero coefficients
        for this trait.

    Example:
        >>> emotions = get_affected_emotions("warmth")
        >>> "loving" in emotions
        True
    """
    trait_coeffs = TRAIT_COEFFICIENTS.get(trait, {})
    return list(trait_coeffs.keys())


def get_traits_affecting_emotion(emotion: str) -> dict[str, float]:
    """Get all traits that affect an emotion and their coefficients.

    Args:
        emotion: Name of the emotion.

    Returns:
        Dictionary mapping trait names to their coefficients
        for this emotion.

    Example:
        >>> traits = get_traits_affecting_emotion("anxious")
        >>> "emotional_stability" in traits
        True
    """
    result: dict[str, float] = {}
    for trait, coeffs in TRAIT_COEFFICIENTS.items():
        if emotion in coeffs:
            result[trait] = coeffs[emotion]
    return result


def calculate_emotion_modifier(traits: dict[str, float], emotion: str) -> float:
    """Calculate the emotion modifier based on trait values.

    This applies the coefficient formula:
    modifier = sum(trait_value * coefficient) for each trait

    Args:
        traits: Dictionary of trait names to their values (0.0-1.0).
        emotion: The emotion to calculate the modifier for.

    Returns:
        The combined modifier value. Positive values increase
        the emotion, negative values decrease it.

    Example:
        >>> traits = {"warmth": 0.9, "emotional_stability": 0.8}
        >>> modifier = calculate_emotion_modifier(traits, "loving")
        >>> modifier > 0  # High warmth increases loving
        True
    """
    modifier = 0.0
    for trait, value in traits.items():
        # Normalize trait value around 0.5 (average)
        # So 0.0 = -0.5, 0.5 = 0, 1.0 = +0.5
        normalized = value - 0.5
        coefficient = get_coefficient(trait, emotion)
        modifier += normalized * coefficient * 2  # Scale to full effect
    return modifier


__all__ = [
    "TRAIT_COEFFICIENTS",
    "calculate_emotion_modifier",
    "get_affected_emotions",
    "get_coefficient",
    "get_traits_affecting_emotion",
]
