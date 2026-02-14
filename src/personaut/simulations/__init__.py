"""Simulation system for Personaut PDK.

This module provides simulation capabilities for conversations, surveys,
outcome analysis, and live interactive sessions.

Simulation Types:
- CONVERSATION: Dialogue between two or more individuals
- SURVEY: Questionnaire responses from an individual
- OUTCOME_SUMMARY: Analysis of whether a target outcome is achieved
- LIVE_CONVERSATION: Real-time interactive simulation

Output Styles:
- SCRIPT: Screenplay-like dialogue format
- QUESTIONNAIRE: Structured Q&A format
- NARRATIVE: Prose narrative format
- JSON: Machine-readable structured output
- TXT: Human-readable text output

Example:
    >>> from personaut.simulations import create_simulation, SimulationType
    >>> simulation = create_simulation(
    ...     situation=situation,
    ...     individuals=[user_a, user_b],
    ...     type=SimulationType.CONVERSATION,
    ... )
    >>> simulation.run(num=10, dir="./")
"""

# Types and styles
# Simulation implementations
from personaut.simulations.conversation import ConversationSimulation
from personaut.simulations.live import (
    ChatMessage,
    ChatSession,
    LiveSimulation,
)
from personaut.simulations.outcome import OutcomeSimulation

# Base simulation
from personaut.simulations.simulation import (
    Simulation,
    SimulationResult,
    create_simulation,
)
from personaut.simulations.styles import (
    JSON,
    NARRATIVE,
    QUESTIONNAIRE,
    SCRIPT,
    TXT,
    SimulationStyle,
    parse_simulation_style,
)
from personaut.simulations.survey import QUESTION_TYPES, SurveySimulation
from personaut.simulations.types import (
    CONVERSATION,
    LIVE_CONVERSATION,
    OUTCOME_SUMMARY,
    SURVEY,
    SimulationType,
    parse_simulation_type,
)


__all__ = [
    # Types enum and constants
    "SimulationType",
    "CONVERSATION",
    "SURVEY",
    "OUTCOME_SUMMARY",
    "LIVE_CONVERSATION",
    "parse_simulation_type",
    # Styles enum and constants
    "SimulationStyle",
    "SCRIPT",
    "QUESTIONNAIRE",
    "NARRATIVE",
    "JSON",
    "TXT",
    "parse_simulation_style",
    # Base classes
    "Simulation",
    "SimulationResult",
    # Factory
    "create_simulation",
    # Implementations
    "ConversationSimulation",
    "SurveySimulation",
    "QUESTION_TYPES",
    "OutcomeSimulation",
    "LiveSimulation",
    "ChatMessage",
    "ChatSession",
]
