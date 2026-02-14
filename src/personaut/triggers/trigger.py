"""Trigger base class for Personaut PDK.

Triggers are conditional activators that can modify an individual's
emotional state or activate masks when specific conditions are met.

Example:
    >>> from personaut.triggers import Trigger
    >>> from personaut.masks import STOIC_MASK
    >>>
    >>> # Triggers are abstract - use EmotionalTrigger or SituationalTrigger
    >>> from personaut.triggers import create_emotional_trigger
    >>> trigger = create_emotional_trigger(
    ...     description="High anxiety response",
    ...     rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
    ...     response=STOIC_MASK,
    ... )
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.masks.mask import Mask


# Response type can be a Mask or an EmotionalState modification
TriggerResponse = Union["Mask", dict[str, float]]


@dataclass
class Trigger(ABC):
    """Abstract base class for triggers.

    Triggers are conditional activators that can modify behavior when
    specific conditions are met. Subclasses implement the checking logic.

    Attributes:
        description: Human-readable description of what triggers this.
        active: Whether this trigger is currently active.
        response: What happens when triggered (Mask or emotion changes).
        priority: Priority for ordering when multiple triggers fire (higher = first).

    Example:
        >>> class MyTrigger(Trigger):
        ...     def check(self, context: Any) -> bool:
        ...         return context.get("danger", False)
    """

    description: str
    response: TriggerResponse | None = None
    active: bool = True
    priority: int = 0

    @abstractmethod
    def check(self, context: Any) -> bool:
        """Check if this trigger should fire.

        Args:
            context: The context to check against. Type depends on
                the specific trigger implementation.

        Returns:
            True if the trigger condition is met.
        """
        ...

    def fire(self, emotional_state: EmotionalState) -> EmotionalState:
        """Apply the trigger's response to an emotional state.

        Args:
            emotional_state: The current emotional state.

        Returns:
            The modified emotional state after applying the response.
        """
        from personaut.masks.mask import Mask

        if self.response is None:
            return emotional_state

        # If response is a Mask, apply it
        if isinstance(self.response, Mask):
            return self.response.apply(emotional_state)

        # If response is emotion modifications dict, apply directly
        if isinstance(self.response, dict):
            # Clone and modify
            current_values = emotional_state.to_dict()
            for emotion, change in self.response.items():
                if emotion in current_values:
                    new_value = max(0.0, min(1.0, current_values[emotion] + change))
                    current_values[emotion] = new_value

            from personaut.emotions.state import EmotionalState as ES

            new_state = ES(emotions=list(current_values.keys()), baseline=0.0)
            new_state.change_state(current_values)
            return new_state

        return emotional_state

    def to_dict(self) -> dict[str, Any]:
        """Convert trigger to dictionary for serialization."""
        from personaut.masks.mask import Mask

        response_data: dict[str, Any] | None = None
        if self.response is not None:
            if isinstance(self.response, Mask):
                response_data = {"type": "mask", "data": self.response.to_dict()}
            else:
                response_data = {"type": "modifications", "data": self.response}

        return {
            "description": self.description,
            "active": self.active,
            "response": response_data,
            "priority": self.priority,
        }


@dataclass
class TriggerRule:
    """A single rule for trigger evaluation.

    Attributes:
        field: The field/emotion to check.
        threshold: The threshold value.
        operator: Comparison operator ('>', '<', '>=', '<=', '==', '!=').
    """

    field: str
    threshold: float
    operator: str = ">"

    def evaluate(self, value: float) -> bool:
        """Evaluate the rule against a value.

        Args:
            value: The value to check.

        Returns:
            True if the rule is satisfied.
        """
        if self.operator == ">":
            return value > self.threshold
        elif self.operator == "<":
            return value < self.threshold
        elif self.operator == ">=":
            return value >= self.threshold
        elif self.operator == "<=":
            return value <= self.threshold
        elif self.operator == "==":
            return value == self.threshold
        elif self.operator == "!=":
            return value != self.threshold
        else:
            msg = f"Unknown operator: {self.operator}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "threshold": self.threshold,
            "operator": self.operator,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TriggerRule:
        """Create from dictionary."""
        return cls(
            field=data["field"],
            threshold=data["threshold"],
            operator=data.get("operator", ">"),
        )


__all__ = [
    "Trigger",
    "TriggerResponse",
    "TriggerRule",
]
