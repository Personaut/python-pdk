"""Trigger system for Personaut PDK.

Triggers are conditional activators that can modify an individual's
emotional state or activate masks when specific conditions are met.

Trigger Types:
    - **Emotional**: Activate based on emotional state thresholds
    - **Situational**: Activate based on physical or situational context

Basic Usage:
    >>> from personaut.triggers import create_emotional_trigger
    >>> from personaut.masks import STOIC_MASK
    >>>
    >>> # Trigger stoic mask when anxiety is high
    >>> trigger = create_emotional_trigger(
    ...     description="High anxiety response",
    ...     rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
    ...     response=STOIC_MASK,
    ... )
    >>>
    >>> # Check and fire
    >>> if trigger.check(emotional_state):
    ...     state = trigger.fire(emotional_state)

Situational Triggers:
    >>> from personaut.triggers import create_situational_trigger
    >>>
    >>> trigger = create_situational_trigger(
    ...     description="Dark enclosed spaces",
    ...     keywords=["basement", "closet", "cave"],
    ...     response={"anxious": 0.3, "helpless": 0.2},
    ... )
"""

from personaut.triggers.emotional import EmotionalTrigger, create_emotional_trigger
from personaut.triggers.situational import SituationalTrigger, create_situational_trigger
from personaut.triggers.trigger import Trigger, TriggerResponse, TriggerRule


__all__ = [
    # Base classes
    "Trigger",
    "TriggerRule",
    "TriggerResponse",
    # Emotional triggers
    "EmotionalTrigger",
    "create_emotional_trigger",
    # Situational triggers
    "SituationalTrigger",
    "create_situational_trigger",
]
