"""Situations module for Personaut PDK.

This module provides situation definition for simulations including
modality, location, time, and contextual information.

Basic Usage:
    >>> from personaut.situations import create_situation
    >>> from personaut.types.modality import Modality
    >>> from datetime import datetime
    >>>
    >>> situation = create_situation(
    ...     modality=Modality.IN_PERSON,
    ...     description="Meeting at a coffee shop",
    ...     time=datetime.now(),
    ...     location="Miami, FL",
    ... )

With Context:
    >>> from personaut.situations import create_situation, SituationContext
    >>>
    >>> ctx = SituationContext()
    >>> ctx.set("environment.lighting", "dim")
    >>> ctx.set("atmosphere", "tense")
    >>>
    >>> situation = create_situation(
    ...     modality=Modality.IN_PERSON,
    ...     description="Meeting in a dimly lit bar",
    ...     context=ctx.to_dict(),
    ... )

Modality Types:
    - IN_PERSON: Full non-verbal cues, physical presence
    - VIDEO_CALL: Visual + audio, technology-mediated
    - PHONE_CALL: Audio only, real-time
    - TEXT_MESSAGE: Written, asynchronous, informal
    - EMAIL: Written, asynchronous, formal
"""

from personaut.situations.context import (
    CONTEXT_SCHEMA,
    ContextCategory,
    SituationContext,
    ValidationError,
    ValidationResult,
    create_context,
    create_environment_context,
    create_social_context,
)
from personaut.situations.situation import (
    Situation,
    create_situation,
)


__all__ = [
    # Situation
    "Situation",
    "create_situation",
    # Context
    "ContextCategory",
    "ValidationError",
    "ValidationResult",
    "SituationContext",
    "CONTEXT_SCHEMA",
    "create_context",
    "create_environment_context",
    "create_social_context",
]
