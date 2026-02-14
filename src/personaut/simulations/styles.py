"""Simulation style definitions for Personaut PDK.

This module defines the different output styles for simulations.

Example:
    >>> from personaut.simulations.styles import SimulationStyle
    >>> style = SimulationStyle.SCRIPT
    >>> print(style.extension)
    'txt'
"""

from __future__ import annotations

from enum import Enum


class SimulationStyle(str, Enum):
    """Output styles for simulations.

    Each style determines how simulation output is formatted and structured.

    Attributes:
        SCRIPT: Screenplay-like dialogue format.
        QUESTIONNAIRE: Structured Q&A format.
        NARRATIVE: Prose narrative format.
        JSON: Machine-readable structured output.
        TXT: Human-readable text output.

    Example:
        >>> style = SimulationStyle.SCRIPT
        >>> print(style.is_structured)
        False
    """

    SCRIPT = "script"
    QUESTIONNAIRE = "questionnaire"
    NARRATIVE = "narrative"
    JSON = "json"
    TXT = "txt"

    @property
    def description(self) -> str:
        """Get a description of this output style.

        Returns:
            Human-readable description of the style.
        """
        descriptions = {
            SimulationStyle.SCRIPT: "Screenplay-like dialogue format",
            SimulationStyle.QUESTIONNAIRE: "Structured Q&A format",
            SimulationStyle.NARRATIVE: "Prose narrative format",
            SimulationStyle.JSON: "Machine-readable structured output",
            SimulationStyle.TXT: "Human-readable text output",
        }
        return descriptions[self]

    @property
    def extension(self) -> str:
        """Get the file extension for this style.

        Returns:
            File extension without the dot.
        """
        extensions = {
            SimulationStyle.SCRIPT: "txt",
            SimulationStyle.QUESTIONNAIRE: "txt",
            SimulationStyle.NARRATIVE: "txt",
            SimulationStyle.JSON: "json",
            SimulationStyle.TXT: "txt",
        }
        return extensions[self]

    @property
    def is_structured(self) -> bool:
        """Check if this style produces structured (machine-readable) output.

        Returns:
            True if the output is structured.
        """
        return self == SimulationStyle.JSON

    @property
    def supports_metadata(self) -> bool:
        """Check if this style supports embedded metadata.

        Returns:
            True if metadata can be included inline.
        """
        return self in {SimulationStyle.JSON, SimulationStyle.QUESTIONNAIRE}


# String constants for convenience
SCRIPT = SimulationStyle.SCRIPT.value
QUESTIONNAIRE = SimulationStyle.QUESTIONNAIRE.value
NARRATIVE = SimulationStyle.NARRATIVE.value
JSON = SimulationStyle.JSON.value
TXT = SimulationStyle.TXT.value


def parse_simulation_style(value: str | SimulationStyle) -> SimulationStyle:
    """Parse a string or SimulationStyle into a SimulationStyle enum.

    Args:
        value: String value or SimulationStyle enum.

    Returns:
        The corresponding SimulationStyle.

    Raises:
        ValueError: If the value is not a valid simulation style.

    Example:
        >>> parse_simulation_style("script")
        <SimulationStyle.SCRIPT: 'script'>
    """
    if isinstance(value, SimulationStyle):
        return value

    try:
        return SimulationStyle(value)
    except ValueError:
        valid = [s.value for s in SimulationStyle]
        msg = f"Invalid simulation style '{value}'. Valid options: {valid}"
        raise ValueError(msg) from None


__all__ = [
    # Enum
    "SimulationStyle",
    # Constants
    "JSON",
    "NARRATIVE",
    "QUESTIONNAIRE",
    "SCRIPT",
    "TXT",
    # Functions
    "parse_simulation_style",
]
