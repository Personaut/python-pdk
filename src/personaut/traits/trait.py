"""Trait definitions for Personaut PDK.

This module defines all 17 traits used in the Personaut personality modeling
system based on the 16PF (Sixteen Personality Factor) model, with an additional
trait for comprehensive coverage.

The trait system provides a validated framework for representing individual
differences in personality that influence behavior and emotional responses.

Example:
    >>> from personaut.traits.trait import WARMTH, DOMINANCE, ALL_TRAITS
    >>> print(f"Tracking {len(ALL_TRAITS)} traits")
    Tracking 17 traits
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Trait:
    """Representation of a single personality trait.

    Traits are immutable data objects that describe a dimension of
    personality with its name, description, and pole labels.

    Attributes:
        name: Lowercase name of the trait (e.g., "warmth").
        description: Brief description of what the trait measures.
        low_pole: Description of low scores on this trait.
        high_pole: Description of high scores on this trait.

    Example:
        >>> trait = Trait("warmth", "Interpersonal warmth", "Reserved", "Warm")
        >>> print(trait.name)
        warmth
    """

    name: str
    description: str
    low_pole: str
    high_pole: str

    def __str__(self) -> str:
        """Return the trait name."""
        return self.name


# =============================================================================
# Primary Traits (16PF Based)
# =============================================================================

WARMTH = "warmth"
"""Interpersonal warmth and attentiveness to others.
Low: Reserved, impersonal, distant
High: Warm, outgoing, attentive to others
"""

REASONING = "reasoning"
"""Abstract thinking and problem-solving ability.
Low: Concrete thinking
High: Abstract thinking
"""

EMOTIONAL_STABILITY = "emotional_stability"
"""Emotional regulation and coping with stress.
Low: Reactive, emotionally changeable
High: Emotionally stable, adaptive, mature
"""

DOMINANCE = "dominance"
"""Assertiveness and desire to influence others.
Low: Deferential, cooperative, avoids conflict
High: Dominant, forceful, assertive
"""

LIVELINESS = "liveliness"
"""Enthusiasm and spontaneity in interactions.
Low: Serious, restrained, careful
High: Lively, animated, spontaneous
"""

RULE_CONSCIOUSNESS = "rule_consciousness"
"""Adherence to rules and conventional standards.
Low: Expedient, nonconforming
High: Rule-conscious, dutiful
"""

SOCIAL_BOLDNESS = "social_boldness"
"""Comfort in social situations and with attention.
Low: Shy, threat-sensitive, timid
High: Socially bold, venturesome, thick-skinned
"""

SENSITIVITY = "sensitivity"
"""Emotional sensitivity and aesthetic appreciation.
Low: Utilitarian, objective, unsentimental
High: Sensitive, aesthetic, sentimental
"""

VIGILANCE = "vigilance"
"""Suspiciousness and distrust of others.
Low: Trusting, unsuspecting, accepting
High: Vigilant, suspicious, skeptical
"""

ABSTRACTEDNESS = "abstractedness"
"""Orientation toward ideas vs. practical matters.
Low: Grounded, practical, solution-oriented
High: Abstracted, imaginative, idea-oriented
"""

PRIVATENESS = "privateness"
"""Guardedness about personal information.
Low: Forthright, genuine, artless
High: Private, discreet, non-disclosing
"""

APPREHENSION = "apprehension"
"""Tendency toward worry and self-doubt.
Low: Self-assured, unworried, complacent
High: Apprehensive, self-doubting, worried
"""

OPENNESS_TO_CHANGE = "openness_to_change"
"""Comfort with change and new experiences.
Low: Traditional, attached to familiar
High: Open to change, experimenting
"""

SELF_RELIANCE = "self_reliance"
"""Preference for independence vs. group membership.
Low: Group-oriented, affiliative
High: Self-reliant, solitary, individualistic
"""

PERFECTIONISM = "perfectionism"
"""Organization and attention to detail.
Low: Tolerates disorder, flexible, undisciplined
High: Perfectionist, organized, self-disciplined
"""

TENSION = "tension"
"""Physical tension and frustration tolerance.
Low: Relaxed, placid, patient
High: Tense, high energy, impatient
"""

# =============================================================================
# Additional Trait
# =============================================================================

HUMILITY = "humility"
"""Modesty and groundedness about achievements.
Low: Self-assured about accomplishments, confident
High: Humble, modest, unassuming
"""


# =============================================================================
# Trait Collections
# =============================================================================

# All 17 traits in the system
ALL_TRAITS: list[str] = [
    WARMTH,
    REASONING,
    EMOTIONAL_STABILITY,
    DOMINANCE,
    HUMILITY,
    LIVELINESS,
    RULE_CONSCIOUSNESS,
    SOCIAL_BOLDNESS,
    SENSITIVITY,
    VIGILANCE,
    ABSTRACTEDNESS,
    PRIVATENESS,
    APPREHENSION,
    OPENNESS_TO_CHANGE,
    SELF_RELIANCE,
    PERFECTIONISM,
    TENSION,
]
"""Complete list of all 17 traits in the system."""


# Interpersonal traits cluster
INTERPERSONAL_TRAITS: list[str] = [
    WARMTH,
    DOMINANCE,
    SOCIAL_BOLDNESS,
    SENSITIVITY,
    PRIVATENESS,
]
"""Traits related to interpersonal behavior and relationships."""

# Emotional traits cluster
EMOTIONAL_TRAITS: list[str] = [
    EMOTIONAL_STABILITY,
    APPREHENSION,
    TENSION,
    VIGILANCE,
]
"""Traits related to emotional regulation and reactivity."""

# Cognitive traits cluster
COGNITIVE_TRAITS: list[str] = [
    REASONING,
    ABSTRACTEDNESS,
    OPENNESS_TO_CHANGE,
]
"""Traits related to cognitive style and thinking patterns."""

# Behavioral traits cluster
BEHAVIORAL_TRAITS: list[str] = [
    LIVELINESS,
    RULE_CONSCIOUSNESS,
    PERFECTIONISM,
    SELF_RELIANCE,
    HUMILITY,
]
"""Traits related to behavioral tendencies and self-management."""


# Trait metadata registry
TRAIT_METADATA: dict[str, Trait] = {
    WARMTH: Trait(
        WARMTH,
        "Interpersonal warmth and attentiveness to others",
        "Reserved, impersonal, distant",
        "Warm, outgoing, attentive",
    ),
    REASONING: Trait(
        REASONING,
        "Abstract thinking and problem-solving ability",
        "Concrete thinking",
        "Abstract thinking",
    ),
    EMOTIONAL_STABILITY: Trait(
        EMOTIONAL_STABILITY,
        "Emotional regulation and coping with stress",
        "Reactive, emotionally changeable",
        "Emotionally stable, adaptive",
    ),
    DOMINANCE: Trait(
        DOMINANCE,
        "Assertiveness and desire to influence others",
        "Deferential, cooperative",
        "Dominant, forceful, assertive",
    ),
    HUMILITY: Trait(
        HUMILITY,
        "Modesty and groundedness about achievements",
        "Self-assured, confident",
        "Humble, modest, unassuming",
    ),
    LIVELINESS: Trait(
        LIVELINESS,
        "Enthusiasm and spontaneity in interactions",
        "Serious, restrained, careful",
        "Lively, animated, spontaneous",
    ),
    RULE_CONSCIOUSNESS: Trait(
        RULE_CONSCIOUSNESS,
        "Adherence to rules and conventional standards",
        "Expedient, nonconforming",
        "Rule-conscious, dutiful",
    ),
    SOCIAL_BOLDNESS: Trait(
        SOCIAL_BOLDNESS,
        "Comfort in social situations and with attention",
        "Shy, threat-sensitive, timid",
        "Socially bold, venturesome",
    ),
    SENSITIVITY: Trait(
        SENSITIVITY,
        "Emotional sensitivity and aesthetic appreciation",
        "Utilitarian, objective",
        "Sensitive, aesthetic, sentimental",
    ),
    VIGILANCE: Trait(
        VIGILANCE,
        "Suspiciousness and distrust of others",
        "Trusting, unsuspecting",
        "Vigilant, suspicious, skeptical",
    ),
    ABSTRACTEDNESS: Trait(
        ABSTRACTEDNESS,
        "Orientation toward ideas vs. practical matters",
        "Grounded, practical",
        "Abstracted, imaginative",
    ),
    PRIVATENESS: Trait(
        PRIVATENESS,
        "Guardedness about personal information",
        "Forthright, genuine, artless",
        "Private, discreet, non-disclosing",
    ),
    APPREHENSION: Trait(
        APPREHENSION,
        "Tendency toward worry and self-doubt",
        "Self-assured, unworried",
        "Apprehensive, self-doubting",
    ),
    OPENNESS_TO_CHANGE: Trait(
        OPENNESS_TO_CHANGE,
        "Comfort with change and new experiences",
        "Traditional, attached to familiar",
        "Open to change, experimenting",
    ),
    SELF_RELIANCE: Trait(
        SELF_RELIANCE,
        "Preference for independence vs. group membership",
        "Group-oriented, affiliative",
        "Self-reliant, solitary",
    ),
    PERFECTIONISM: Trait(
        PERFECTIONISM,
        "Organization and attention to detail",
        "Tolerates disorder, flexible",
        "Perfectionist, organized",
    ),
    TENSION: Trait(
        TENSION,
        "Physical tension and frustration tolerance",
        "Relaxed, placid, patient",
        "Tense, high energy, impatient",
    ),
}
"""Metadata for all traits including description and pole labels."""


def get_trait_metadata(trait: str) -> Trait:
    """Get metadata for a trait.

    Args:
        trait: Name of the trait (lowercase).

    Returns:
        Trait object with name, description, and pole labels.

    Raises:
        KeyError: If the trait is not recognized.

    Example:
        >>> metadata = get_trait_metadata("warmth")
        >>> print(metadata.high_pole)
        Warm, outgoing, attentive
    """
    return TRAIT_METADATA[trait]


def is_valid_trait(trait: str) -> bool:
    """Check if a trait name is valid.

    Args:
        trait: Name to check.

    Returns:
        True if the trait is recognized, False otherwise.

    Example:
        >>> is_valid_trait("warmth")
        True
        >>> is_valid_trait("charisma")
        False
    """
    return trait in ALL_TRAITS


def get_trait_cluster(trait: str) -> str:
    """Get the cluster a trait belongs to.

    Args:
        trait: Name of the trait.

    Returns:
        Cluster name: 'interpersonal', 'emotional', 'cognitive', or 'behavioral'.

    Raises:
        KeyError: If the trait is not recognized.

    Example:
        >>> get_trait_cluster("warmth")
        'interpersonal'
    """
    if trait in INTERPERSONAL_TRAITS:
        return "interpersonal"
    if trait in EMOTIONAL_TRAITS:
        return "emotional"
    if trait in COGNITIVE_TRAITS:
        return "cognitive"
    if trait in BEHAVIORAL_TRAITS:
        return "behavioral"
    msg = f"Unknown trait: {trait}"
    raise KeyError(msg)


__all__ = [
    # Trait constants
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
    "TRAIT_METADATA",
    "VIGILANCE",
    "WARMTH",
    # Classes
    "Trait",
    # Functions
    "get_trait_cluster",
    "get_trait_metadata",
    "is_valid_trait",
]
