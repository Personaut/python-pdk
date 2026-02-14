"""State calculation system for Personaut PDK.

This module provides tools for calculating and transitioning between
emotional states, including:
- State calculation modes (AVERAGE, MAXIMUM, etc.)
- StateCalculator for computing states from history
- MarkovTransitionMatrix for probabilistic state transitions

Example:
    >>> from personaut.states import StateCalculator, StateMode
    >>> from personaut.emotions import EmotionalState
    >>>
    >>> calc = StateCalculator(mode=StateMode.AVERAGE)
    >>> calc.add_state(EmotionalState())
    >>> result = calc.get_calculated_state()
"""

from personaut.states.calculator import CustomCalculator, StateCalculator
from personaut.states.markov import DEFAULT_CATEGORY_TRANSITIONS, MarkovTransitionMatrix
from personaut.states.mode import (
    AVERAGE,
    CUSTOM,
    MAXIMUM,
    MINIMUM,
    RECENT,
    StateMode,
    parse_state_mode,
)


__all__ = [
    # Constants
    "AVERAGE",
    "CUSTOM",
    "DEFAULT_CATEGORY_TRANSITIONS",
    "MAXIMUM",
    "MINIMUM",
    "RECENT",
    # Type aliases
    "CustomCalculator",
    # Main classes
    "MarkovTransitionMatrix",
    "StateCalculator",
    # Enums
    "StateMode",
    # Functions
    "parse_state_mode",
]
