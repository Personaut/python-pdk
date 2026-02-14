"""State calculation modes for Personaut PDK.

This module defines the different modes for calculating emotional state
from a history of states. These modes determine how past emotional
states are combined to form the current "effective" emotional state.

Example:
    >>> from personaut.states.mode import StateMode
    >>> mode = StateMode.AVERAGE
    >>> print(mode.description)
    Calculate average intensity for each emotion across history
"""

from __future__ import annotations

from enum import Enum


class StateMode(str, Enum):
    """Modes for calculating emotional state from history.

    Different modes provide different strategies for combining
    past emotional states into a single representative state.

    Attributes:
        AVERAGE: Average each emotion's intensity across history.
        MAXIMUM: Use the maximum intensity for each emotion.
        MINIMUM: Use the minimum intensity for each emotion.
        RECENT: Weight recent states more heavily.
        CUSTOM: Use a custom calculation function.

    Example:
        >>> mode = StateMode.AVERAGE
        >>> mode.value
        'average'
    """

    AVERAGE = "average"
    MAXIMUM = "maximum"
    MINIMUM = "minimum"
    RECENT = "recent"
    CUSTOM = "custom"

    @property
    def description(self) -> str:
        """Get a description of the state calculation mode.

        Returns:
            Human-readable description of how this mode calculates state.

        Example:
            >>> StateMode.AVERAGE.description
            'Calculate average intensity for each emotion across history'
        """
        descriptions = {
            StateMode.AVERAGE: "Calculate average intensity for each emotion across history",
            StateMode.MAXIMUM: "Use maximum intensity for each emotion across history",
            StateMode.MINIMUM: "Use minimum intensity for each emotion across history",
            StateMode.RECENT: "Weight recent states more heavily using exponential decay",
            StateMode.CUSTOM: "Use a custom calculation function",
        }
        return descriptions[self]

    @property
    def requires_custom_function(self) -> bool:
        """Check if this mode requires a custom function.

        Returns:
            True if CUSTOM mode, False otherwise.

        Example:
            >>> StateMode.CUSTOM.requires_custom_function
            True
            >>> StateMode.AVERAGE.requires_custom_function
            False
        """
        return self == StateMode.CUSTOM


# String constants for convenient imports
AVERAGE = StateMode.AVERAGE.value
MAXIMUM = StateMode.MAXIMUM.value
MINIMUM = StateMode.MINIMUM.value
RECENT = StateMode.RECENT.value
CUSTOM = StateMode.CUSTOM.value


def parse_state_mode(value: str | StateMode) -> StateMode:
    """Parse a state mode from a string or enum value.

    Args:
        value: Either a StateMode enum or a string matching a mode value.

    Returns:
        The corresponding StateMode enum member.

    Raises:
        ValueError: If the string doesn't match any state mode.

    Example:
        >>> parse_state_mode("average")
        <StateMode.AVERAGE: 'average'>
        >>> parse_state_mode(StateMode.MAXIMUM)
        <StateMode.MAXIMUM: 'maximum'>
    """
    if isinstance(value, StateMode):
        return value

    value_lower = value.lower()
    for mode in StateMode:
        if mode.value == value_lower:
            return mode

    valid = ", ".join(m.value for m in StateMode)
    msg = f"Unknown state mode: {value}. Valid modes: {valid}"
    raise ValueError(msg)


__all__ = [
    "AVERAGE",
    "CUSTOM",
    "MAXIMUM",
    "MINIMUM",
    "RECENT",
    "StateMode",
    "parse_state_mode",
]
