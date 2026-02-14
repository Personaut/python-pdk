"""Simulation type definitions for Personaut PDK.

This module defines the different types of simulations available.

Example:
    >>> from personaut.simulations.types import SimulationType
    >>> sim_type = SimulationType.CONVERSATION
    >>> print(sim_type.description)
    'Dialogue between two or more individuals'
"""

from __future__ import annotations

from enum import Enum


class SimulationType(str, Enum):
    """Types of simulations available in Personaut.

    Each type represents a different simulation mode with specific
    behavior and output characteristics.

    Attributes:
        CONVERSATION: Dialogue between two or more individuals.
        SURVEY: Questionnaire responses from an individual.
        OUTCOME_SUMMARY: Analysis of whether a target outcome is achieved.
        LIVE_CONVERSATION: Real-time interactive simulation.

    Example:
        >>> sim_type = SimulationType.CONVERSATION
        >>> print(sim_type.is_interactive)
        False
    """

    CONVERSATION = "conversation"
    SURVEY = "survey"
    OUTCOME_SUMMARY = "outcome_summary"
    LIVE_CONVERSATION = "live_conversation"

    @property
    def description(self) -> str:
        """Get a description of this simulation type.

        Returns:
            Human-readable description of the simulation type.
        """
        descriptions = {
            SimulationType.CONVERSATION: "Dialogue between two or more individuals",
            SimulationType.SURVEY: "Questionnaire responses from an individual",
            SimulationType.OUTCOME_SUMMARY: ("Analysis of whether a target outcome is achieved"),
            SimulationType.LIVE_CONVERSATION: "Real-time interactive simulation",
        }
        return descriptions[self]

    @property
    def is_interactive(self) -> bool:
        """Check if this simulation type requires user interaction.

        Returns:
            True if the simulation is interactive.
        """
        return self == SimulationType.LIVE_CONVERSATION

    @property
    def supports_multi_turn(self) -> bool:
        """Check if this simulation supports multi-turn dialogue.

        Returns:
            True if the simulation supports multiple conversation turns.
        """
        return self in {SimulationType.CONVERSATION, SimulationType.LIVE_CONVERSATION}

    @property
    def default_style(self) -> str:
        """Get the default output style for this simulation type.

        Returns:
            Default style name.
        """
        defaults = {
            SimulationType.CONVERSATION: "script",
            SimulationType.SURVEY: "questionnaire",
            SimulationType.OUTCOME_SUMMARY: "narrative",
            SimulationType.LIVE_CONVERSATION: "json",
        }
        return defaults[self]


# String constants for convenience
CONVERSATION = SimulationType.CONVERSATION.value
SURVEY = SimulationType.SURVEY.value
OUTCOME_SUMMARY = SimulationType.OUTCOME_SUMMARY.value
LIVE_CONVERSATION = SimulationType.LIVE_CONVERSATION.value


def parse_simulation_type(value: str | SimulationType) -> SimulationType:
    """Parse a string or SimulationType into a SimulationType enum.

    Args:
        value: String value or SimulationType enum.

    Returns:
        The corresponding SimulationType.

    Raises:
        ValueError: If the value is not a valid simulation type.

    Example:
        >>> parse_simulation_type("conversation")
        <SimulationType.CONVERSATION: 'conversation'>
    """
    if isinstance(value, SimulationType):
        return value

    try:
        return SimulationType(value)
    except ValueError:
        valid = [t.value for t in SimulationType]
        msg = f"Invalid simulation type '{value}'. Valid options: {valid}"
        raise ValueError(msg) from None


__all__ = [
    # Enum
    "SimulationType",
    # Constants
    "CONVERSATION",
    "LIVE_CONVERSATION",
    "OUTCOME_SUMMARY",
    "SURVEY",
    # Functions
    "parse_simulation_type",
]
