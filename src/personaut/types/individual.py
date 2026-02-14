"""Individual type definitions for Personaut PDK.

This module defines the types related to individuals in the simulation system,
including the IndividualType enum that distinguishes between simulated AI
personas, human participants, and non-tracked background characters.

Example:
    >>> from personaut.types.individual import IndividualType
    >>> individual_type = IndividualType.SIMULATED
    >>> print(individual_type.description)
    'AI-driven persona with full emotional and personality modeling'
"""

from __future__ import annotations

from enum import Enum


class IndividualType(str, Enum):
    """Type classification for individuals in simulations.

    This enum classifies individuals based on how they are controlled
    and tracked within the simulation system.

    Attributes:
        SIMULATED: AI-driven persona with full modeling.
        HUMAN: Real human participant in the simulation.
        NONTRACKED: Background character without state tracking.

    Example:
        >>> individual = Individual(type=IndividualType.SIMULATED, name="Sarah")
    """

    SIMULATED = "simulated"
    HUMAN = "human"
    NONTRACKED = "nontracked"

    @property
    def description(self) -> str:
        """Get a human-readable description of the individual type.

        Returns:
            Description of the individual type's characteristics.
        """
        descriptions = {
            IndividualType.SIMULATED: ("AI-driven persona with full emotional and personality modeling"),
            IndividualType.HUMAN: ("Real human participant whose responses are provided externally"),
            IndividualType.NONTRACKED: ("Background character without emotional state or memory tracking"),
        }
        return descriptions[self]

    @property
    def has_emotional_state(self) -> bool:
        """Check if this type tracks emotional state.

        Returns:
            True if the type supports emotional state tracking.
        """
        return self == IndividualType.SIMULATED

    @property
    def has_memory(self) -> bool:
        """Check if this type supports memory storage.

        Returns:
            True if the type supports memory storage and retrieval.
        """
        return self in {IndividualType.SIMULATED, IndividualType.HUMAN}

    @property
    def generates_responses(self) -> bool:
        """Check if this type generates AI responses.

        Returns:
            True if the type generates responses via LLM.
        """
        return self == IndividualType.SIMULATED

    @property
    def requires_context(self) -> bool:
        """Check if this type requires external context for responses.

        Human participants provide their own responses; non-tracked
        individuals don't participate meaningfully.

        Returns:
            True if the type requires external context input.
        """
        return self == IndividualType.HUMAN


# String constants for convenience
SIMULATED = IndividualType.SIMULATED.value
HUMAN = IndividualType.HUMAN.value
NONTRACKED = IndividualType.NONTRACKED.value


def parse_individual_type(value: str | IndividualType) -> IndividualType:
    """Parse a string or IndividualType value into an IndividualType enum.

    This function provides flexible parsing of individual type values,
    accepting both string values and IndividualType enum instances.

    Args:
        value: String value or IndividualType enum to parse.

    Returns:
        The corresponding IndividualType enum value.

    Raises:
        ValueError: If the value is not a valid individual type.

    Example:
        >>> parse_individual_type("simulated")
        <IndividualType.SIMULATED: 'simulated'>
        >>> parse_individual_type(IndividualType.HUMAN)
        <IndividualType.HUMAN: 'human'>
    """
    if isinstance(value, IndividualType):
        return value

    try:
        return IndividualType(value)
    except ValueError:
        valid = [t.value for t in IndividualType]
        msg = f"Invalid individual type '{value}'. Valid options: {valid}"
        raise ValueError(msg) from None


__all__ = [
    # Constants
    "HUMAN",
    "NONTRACKED",
    "SIMULATED",
    # Enum
    "IndividualType",
    # Functions
    "parse_individual_type",
]
