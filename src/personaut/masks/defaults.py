"""Default mask definitions for Personaut PDK.

This module provides predefined masks for common social contexts.
These can be used directly or as templates for custom masks.

Example:
    >>> from personaut.masks import PROFESSIONAL_MASK, CASUAL_MASK
    >>>
    >>> # Check if professional mask should activate
    >>> if PROFESSIONAL_MASK.should_trigger("office meeting"):
    ...     modified_state = PROFESSIONAL_MASK.apply(current_state)
"""

from __future__ import annotations

from personaut.masks.mask import Mask


# =============================================================================
# Professional Context
# =============================================================================

PROFESSIONAL_MASK = Mask(
    name="professional",
    description=(
        "Workplace persona that suppresses strong emotions and promotes "
        "calm, composed behavior suitable for professional environments."
    ),
    emotional_modifications={
        # Suppress negative emotions
        "angry": -0.5,
        "hostile": -0.5,
        "hateful": -0.6,
        "critical": -0.3,
        # Suppress excess enthusiasm
        "excited": -0.3,
        # Boost composed emotions
        "content": 0.2,
        "satisfied": 0.2,
        "thoughtful": 0.3,
    },
    trigger_situations=[
        "office",
        "meeting",
        "professional",
        "work",
        "conference",
        "presentation",
        "interview",
        "client",
        "boss",
        "colleague",
    ],
    active_by_default=False,
)
"""Professional mask for workplace contexts.

Suppresses strong emotional displays and promotes calm, composed behavior.
Activates in office, meeting, and professional settings.
"""


# =============================================================================
# Casual Context
# =============================================================================

CASUAL_MASK = Mask(
    name="casual",
    description=("Relaxed persona for informal social situations that allows more natural emotional expression."),
    emotional_modifications={
        # Allow more expressive emotions
        "excited": 0.2,
        "cheerful": 0.2,
        "energetic": 0.2,
        # Reduce guardedness
        "insecure": -0.2,
        "anxious": -0.2,
        # Boost social warmth
        "loving": 0.1,
        "trusting": 0.2,
    },
    trigger_situations=[
        "party",
        "friends",
        "casual",
        "hanging out",
        "relaxing",
        "weekend",
        "bar",
        "pub",
        "home",
        "vacation",
    ],
    active_by_default=False,
)
"""Casual mask for informal social contexts.

Allows more natural emotional expression and reduces guardedness.
Activates in social, relaxed environments.
"""


# =============================================================================
# Stoic Context
# =============================================================================

STOIC_MASK = Mask(
    name="stoic",
    description=(
        "Calm, unflappable persona for crisis situations that suppresses "
        "emotional reactivity and promotes rational, measured responses."
    ),
    emotional_modifications={
        # Strongly suppress reactive emotions
        "angry": -0.6,
        "anxious": -0.5,
        "helpless": -0.4,
        "confused": -0.3,
        "insecure": -0.4,
        "excited": -0.4,
        # Suppress sadness
        "depressed": -0.3,
        "lonely": -0.2,
        # Boost calm, analytical emotions
        "content": 0.3,
        "thoughtful": 0.4,
        "satisfied": 0.2,
    },
    trigger_situations=[
        "crisis",
        "emergency",
        "danger",
        "high stakes",
        "stressful",
        "pressure",
        "urgent",
        "critical",
        "life or death",
    ],
    active_by_default=False,
)
"""Stoic mask for high-pressure situations.

Suppresses emotional reactivity and promotes calm, measured behavior.
Activates during crises and stressful situations.
"""


# =============================================================================
# Enthusiastic Context
# =============================================================================

ENTHUSIASTIC_MASK = Mask(
    name="enthusiastic",
    description=("High-energy persona for motivational contexts that amplifies positive emotions and enthusiasm."),
    emotional_modifications={
        # Boost positive emotions
        "excited": 0.4,
        "cheerful": 0.4,
        "hopeful": 0.3,
        "energetic": 0.5,
        "creative": 0.3,
        # Suppress dampening emotions
        "bored": -0.4,
        "apathetic": -0.5,
        "depressed": -0.3,
        "lonely": -0.2,
        # Boost confidence
        "proud": 0.2,
        "important": 0.2,
    },
    trigger_situations=[
        "rally",
        "motivational",
        "celebration",
        "achievement",
        "success",
        "launch",
        "opening",
        "kickoff",
        "pep talk",
        "inspiring",
    ],
    active_by_default=False,
)
"""Enthusiastic mask for motivational contexts.

Amplifies positive emotions and enthusiasm.
Activates during celebrations, achievements, and motivational events.
"""


# =============================================================================
# Nurturing Context
# =============================================================================

NURTURING_MASK = Mask(
    name="nurturing",
    description=("Caring, supportive persona for caretaking situations that promotes warmth, patience, and empathy."),
    emotional_modifications={
        # Boost caring emotions
        "loving": 0.4,
        "nurturing": 0.5,
        "intimate": 0.3,
        "trusting": 0.3,
        # Suppress impatience
        "angry": -0.4,
        "critical": -0.4,
        "hostile": -0.5,
        "selfish": -0.5,
        # Boost patience indicators
        "content": 0.2,
        "satisfied": 0.2,
    },
    trigger_situations=[
        "child",
        "children",
        "baby",
        "caring",
        "nursing",
        "teaching",
        "mentoring",
        "comforting",
        "supporting",
        "vulnerable",
    ],
    active_by_default=False,
)
"""Nurturing mask for caretaking contexts.

Promotes warmth, patience, and empathy.
Activates when caring for others or in supportive roles.
"""


# =============================================================================
# Guarded Context
# =============================================================================

GUARDED_MASK = Mask(
    name="guarded",
    description=(
        "Protective persona for unfamiliar or potentially hostile situations "
        "that reduces trust and increases vigilance."
    ),
    emotional_modifications={
        # Reduce vulnerability
        "trusting": -0.4,
        "intimate": -0.5,
        "loving": -0.3,
        # Increase alertness
        "anxious": 0.2,
        "insecure": 0.2,
        # Reduce openness
        "cheerful": -0.2,
        "excited": -0.2,
        # Maintain composure
        "content": 0.1,
        "thoughtful": 0.2,
    },
    trigger_situations=[
        "stranger",
        "unfamiliar",
        "suspicious",
        "unknown",
        "new place",
        "first time",
        "wary",
        "cautious",
    ],
    active_by_default=False,
)
"""Guarded mask for unfamiliar situations.

Reduces trust and increases vigilance in uncertain environments.
Activates around strangers or in unfamiliar situations.
"""


# Collection of all default masks
DEFAULT_MASKS = [
    PROFESSIONAL_MASK,
    CASUAL_MASK,
    STOIC_MASK,
    ENTHUSIASTIC_MASK,
    NURTURING_MASK,
    GUARDED_MASK,
]
"""List of all predefined masks."""


def get_mask_by_name(name: str) -> Mask | None:
    """Get a default mask by name.

    Args:
        name: Name of the mask to retrieve.

    Returns:
        The mask if found, None otherwise.

    Example:
        >>> mask = get_mask_by_name("professional")
        >>> mask.name
        'professional'
    """
    for mask in DEFAULT_MASKS:
        if mask.name.lower() == name.lower():
            return mask
    return None


__all__ = [
    "CASUAL_MASK",
    "DEFAULT_MASKS",
    "ENTHUSIASTIC_MASK",
    "GUARDED_MASK",
    "NURTURING_MASK",
    "PROFESSIONAL_MASK",
    "STOIC_MASK",
    "get_mask_by_name",
]
