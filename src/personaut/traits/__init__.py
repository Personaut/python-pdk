"""Trait system for Personaut PDK.

This module provides the complete personality trait modeling system, including:
- 17 distinct traits based on the 16PF model
- TraitProfile class for tracking trait values
- Trait-emotion coefficients for personality-based emotion modification
- Utility functions for trait validation and lookup

Example:
    >>> from personaut.traits import TraitProfile, WARMTH, DOMINANCE
    >>> profile = TraitProfile()
    >>> profile.set_trait(WARMTH, 0.9)
    >>> profile.set_trait(DOMINANCE, 0.3)
    >>> print(profile.get_high_traits())
    [('warmth', 0.9)]
"""

from personaut.traits.coefficients import (
    TRAIT_COEFFICIENTS,
    calculate_emotion_modifier,
    get_affected_emotions,
    get_coefficient,
    get_traits_affecting_emotion,
)
from personaut.traits.profile import TraitProfile
from personaut.traits.trait import (
    ABSTRACTEDNESS,
    ALL_TRAITS,
    APPREHENSION,
    BEHAVIORAL_TRAITS,
    COGNITIVE_TRAITS,
    DOMINANCE,
    EMOTIONAL_STABILITY,
    EMOTIONAL_TRAITS,
    HUMILITY,
    INTERPERSONAL_TRAITS,
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
    TRAIT_METADATA,
    VIGILANCE,
    WARMTH,
    Trait,
    get_trait_cluster,
    get_trait_metadata,
    is_valid_trait,
)


__all__ = [
    # All 17 trait constants
    "ABSTRACTEDNESS",
    # Collections
    "ALL_TRAITS",
    "APPREHENSION",
    "BEHAVIORAL_TRAITS",
    "COGNITIVE_TRAITS",
    "DOMINANCE",
    "EMOTIONAL_STABILITY",
    "EMOTIONAL_TRAITS",
    "HUMILITY",
    "INTERPERSONAL_TRAITS",
    "LIVELINESS",
    "OPENNESS_TO_CHANGE",
    "PERFECTIONISM",
    "PRIVATENESS",
    "REASONING",
    "RULE_CONSCIOUSNESS",
    "SELF_RELIANCE",
    "SENSITIVITY",
    "SOCIAL_BOLDNESS",
    "TENSION",
    "TRAIT_COEFFICIENTS",
    "TRAIT_METADATA",
    "VIGILANCE",
    "WARMTH",
    # Trait dataclass
    "Trait",
    # Main class
    "TraitProfile",
    # Functions
    "calculate_emotion_modifier",
    "get_affected_emotions",
    "get_coefficient",
    "get_trait_cluster",
    "get_trait_metadata",
    "get_traits_affecting_emotion",
    "is_valid_trait",
]
