"""Individuals module for Personaut PDK.

This module provides the Individual class, which represents a complete
persona with personality traits, emotions, memories, masks, and triggers.

Basic Usage:
    >>> from personaut.individuals import create_individual
    >>>
    >>> individual = create_individual(
    ...     name="Sarah Chen",
    ...     traits={"warmth": 0.8, "dominance": 0.4},
    ...     emotional_state={"cheerful": 0.6},
    ... )
    >>>
    >>> # Get emotional state (respects active mask)
    >>> state = individual.get_emotional_state()
    >>> print(individual.get_dominant_emotion())
    ('cheerful', 0.6)

With Masks and Triggers:
    >>> from personaut.masks import PROFESSIONAL_MASK
    >>> from personaut.triggers import create_emotional_trigger
    >>>
    >>> # Add a professional mask
    >>> individual.add_mask(PROFESSIONAL_MASK)
    >>> individual.activate_mask("professional")
    >>>
    >>> # The mask modifies emotional expression
    >>> modified_state = individual.get_emotional_state()

Human Participants:
    >>> from personaut.individuals import create_human
    >>>
    >>> # Create a tracked human participant
    >>> user = create_human("Alex", role="interviewer")
    >>> print(user.get_metadata("is_human"))
    True

Background Characters:
    >>> from personaut.individuals import create_nontracked_individual
    >>>
    >>> # Create untracked background characters
    >>> barista = create_nontracked_individual("barista")
    >>> crowd = create_nontracked_individual("crowd_member")
"""

from personaut.individuals.individual import (
    Individual,
    create_human,
    create_individual,
    create_nontracked_individual,
)
from personaut.individuals.physical import PhysicalFeatures


__all__ = [
    "Individual",
    "PhysicalFeatures",
    "create_human",
    "create_individual",
    "create_nontracked_individual",
]
