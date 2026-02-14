"""Trust calculation utilities for Personaut PDK.

This module provides utilities for managing and calculating trust levels
between individuals in relationships.

Example:
    >>> from personaut.relationships.trust import (
    ...     TrustLevel,
    ...     get_trust_level,
    ...     clamp_trust,
    ... )
    >>>
    >>> level = get_trust_level(0.85)
    >>> level.name
    'HIGH'
    >>> level.description
    'Deep trust - shares personal information freely'
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TrustLevel(Enum):
    """Enumeration of trust levels with thresholds.

    Trust levels define how individuals interact and what information
    they share with each other.
    """

    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    COMPLETE = "complete"


# Trust level thresholds and descriptions
TRUST_THRESHOLDS: dict[TrustLevel, tuple[float, float]] = {
    TrustLevel.NONE: (0.0, 0.1),
    TrustLevel.MINIMAL: (0.1, 0.25),
    TrustLevel.LOW: (0.25, 0.4),
    TrustLevel.MODERATE: (0.4, 0.6),
    TrustLevel.HIGH: (0.6, 0.8),
    TrustLevel.COMPLETE: (0.8, 1.0),
}

TRUST_DESCRIPTIONS: dict[TrustLevel, str] = {
    TrustLevel.NONE: "No trust - actively suspicious or hostile",
    TrustLevel.MINIMAL: "Minimal trust - cautious acquaintance",
    TrustLevel.LOW: "Low trust - guarded interactions, withholds information",
    TrustLevel.MODERATE: "Moderate trust - open communication, some reservations",
    TrustLevel.HIGH: "High trust - shares personal information, relies on other",
    TrustLevel.COMPLETE: "Complete trust - shares everything, deep bond",
}

TRUST_BEHAVIORS: dict[TrustLevel, dict[str, Any]] = {
    TrustLevel.NONE: {
        "shares_private_memories": False,
        "emotional_openness": 0.1,
        "responds_to_requests": False,
        "disclosure_modifier": -0.5,
    },
    TrustLevel.MINIMAL: {
        "shares_private_memories": False,
        "emotional_openness": 0.2,
        "responds_to_requests": False,
        "disclosure_modifier": -0.3,
    },
    TrustLevel.LOW: {
        "shares_private_memories": False,
        "emotional_openness": 0.4,
        "responds_to_requests": True,
        "disclosure_modifier": -0.1,
    },
    TrustLevel.MODERATE: {
        "shares_private_memories": False,
        "emotional_openness": 0.6,
        "responds_to_requests": True,
        "disclosure_modifier": 0.0,
    },
    TrustLevel.HIGH: {
        "shares_private_memories": True,
        "emotional_openness": 0.8,
        "responds_to_requests": True,
        "disclosure_modifier": 0.2,
    },
    TrustLevel.COMPLETE: {
        "shares_private_memories": True,
        "emotional_openness": 1.0,
        "responds_to_requests": True,
        "disclosure_modifier": 0.4,
    },
}


@dataclass
class TrustInfo:
    """Detailed trust information.

    Attributes:
        level: The trust level enum.
        value: The numeric trust value (0.0-1.0).
        description: Human-readable description.
        behaviors: Associated behavioral modifiers.
    """

    level: TrustLevel
    value: float
    description: str
    behaviors: dict[str, Any]


def get_trust_level(trust_value: float) -> TrustLevel:
    """Get the trust level for a numeric value.

    Args:
        trust_value: Trust value between 0.0 and 1.0.

    Returns:
        The corresponding TrustLevel.

    Example:
        >>> get_trust_level(0.85)
        <TrustLevel.COMPLETE: 'complete'>
    """
    for level, (low, high) in TRUST_THRESHOLDS.items():
        if low <= trust_value < high:
            return level

    # Edge case: exactly 1.0
    if trust_value >= 1.0:
        return TrustLevel.COMPLETE

    return TrustLevel.NONE


def get_trust_info(trust_value: float) -> TrustInfo:
    """Get detailed trust information for a value.

    Args:
        trust_value: Trust value between 0.0 and 1.0.

    Returns:
        TrustInfo with level, description, and behaviors.

    Example:
        >>> info = get_trust_info(0.75)
        >>> info.level
        <TrustLevel.HIGH: 'high'>
        >>> info.behaviors["shares_private_memories"]
        True
    """
    level = get_trust_level(trust_value)
    return TrustInfo(
        level=level,
        value=trust_value,
        description=TRUST_DESCRIPTIONS[level],
        behaviors=TRUST_BEHAVIORS[level],
    )


def clamp_trust(value: float) -> float:
    """Clamp a trust value to valid range.

    Args:
        value: Any numeric value.

    Returns:
        Value clamped to [0.0, 1.0].

    Example:
        >>> clamp_trust(1.5)
        1.0
        >>> clamp_trust(-0.2)
        0.0
    """
    return max(0.0, min(1.0, value))


def calculate_trust_change(
    current: float,
    change: float,
    reason: str | None = None,
) -> tuple[float, str]:
    """Calculate a trust change with contextual adjustments.

    Args:
        current: Current trust value.
        change: Proposed change (positive or negative).
        reason: Optional reason for the change.

    Returns:
        Tuple of (new_trust_value, change_description).

    Example:
        >>> new_val, desc = calculate_trust_change(0.5, 0.2, "helped in crisis")
        >>> new_val
        0.7
    """
    # Apply resistance to large changes at extremes
    # It's harder to gain trust when already high, harder to lose when low
    if change > 0 and current > 0.7:
        # Diminishing returns for high trust
        effective_change = change * (1.0 - (current - 0.7) / 0.3 * 0.5)
    elif change < 0 and current < 0.3:
        # Resistance to going below zero
        effective_change = change * (current / 0.3 * 0.5 + 0.5)
    else:
        effective_change = change

    new_value = clamp_trust(current + effective_change)

    # Generate description
    if reason:
        direction = "increased" if effective_change > 0 else "decreased"
        desc = f"Trust {direction} from {current:.2f} to {new_value:.2f}: {reason}"
    else:
        desc = f"Trust changed from {current:.2f} to {new_value:.2f}"

    return new_value, desc


def trust_allows_disclosure(trust_value: float, threshold: float) -> bool:
    """Check if trust level allows disclosure of information.

    Args:
        trust_value: Current trust level.
        threshold: Required threshold for disclosure.

    Returns:
        True if trust meets or exceeds threshold.

    Example:
        >>> trust_allows_disclosure(0.8, 0.7)
        True
        >>> trust_allows_disclosure(0.5, 0.7)
        False
    """
    return trust_value >= threshold


def get_default_trust() -> float:
    """Get the default trust value for new relationships.

    Returns:
        Default trust value (0.3 - low trust).
    """
    return 0.3


def get_stranger_trust() -> float:
    """Get the trust value for strangers.

    Returns:
        Stranger trust value (0.1 - minimal trust).
    """
    return 0.1


__all__ = [
    "TRUST_BEHAVIORS",
    "TRUST_DESCRIPTIONS",
    "TRUST_THRESHOLDS",
    "TrustInfo",
    "TrustLevel",
    "calculate_trust_change",
    "clamp_trust",
    "get_default_trust",
    "get_stranger_trust",
    "get_trust_info",
    "get_trust_level",
    "trust_allows_disclosure",
]
