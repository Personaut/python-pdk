"""Emotional triggers for Personaut PDK.

Emotional triggers activate based on the current emotional state of an
individual. They can monitor specific emotions and fire when thresholds
are crossed.

Example:
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
    >>> # Check if trigger should fire
    >>> if trigger.check(emotional_state):
    ...     state = trigger.fire(emotional_state)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from personaut.triggers.trigger import Trigger, TriggerResponse, TriggerRule


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState


@dataclass
class EmotionalTrigger(Trigger):
    """Trigger that activates based on emotional state.

    Emotional triggers monitor specific emotions and fire when the
    configured thresholds are crossed.

    Attributes:
        rules: List of rules that define when this trigger fires.
        match_all: If True, all rules must match. If False, any rule matches.

    Example:
        >>> trigger = EmotionalTrigger(
        ...     description="Anxiety crisis",
        ...     rules=[
        ...         TriggerRule("anxious", 0.8, ">"),
        ...         TriggerRule("helpless", 0.6, ">"),
        ...     ],
        ...     match_all=True,  # Both must be true
        ... )
    """

    rules: list[TriggerRule] = field(default_factory=list)
    match_all: bool = True

    def check(self, context: EmotionalState) -> bool:
        """Check if this trigger should fire based on emotional state.

        Args:
            context: The emotional state to check against.

        Returns:
            True if the trigger conditions are met.
        """
        if not self.active:
            return False

        if not self.rules:
            return False

        results = []
        for rule in self.rules:
            value = context.get_emotion(rule.field)
            results.append(rule.evaluate(value))

        if self.match_all:
            return all(results)
        return any(results)

    def add_rule(
        self,
        emotion: str,
        threshold: float,
        operator: str = ">",
    ) -> None:
        """Add a rule to this trigger.

        Args:
            emotion: The emotion to monitor.
            threshold: The threshold value.
            operator: Comparison operator.
        """
        self.rules.append(TriggerRule(emotion, threshold, operator))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data["rules"] = [rule.to_dict() for rule in self.rules]
        data["match_all"] = self.match_all
        data["type"] = "emotional"
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmotionalTrigger:
        """Create from dictionary."""
        from personaut.masks.mask import Mask

        # Parse response
        response: TriggerResponse | None = None
        if data.get("response"):
            resp_data = data["response"]
            if resp_data["type"] == "mask":
                response = Mask.from_dict(resp_data["data"])
            else:
                response = resp_data["data"]

        # Parse rules
        rules = [TriggerRule.from_dict(r) for r in data.get("rules", [])]

        return cls(
            description=data["description"],
            response=response,
            active=data.get("active", True),
            priority=data.get("priority", 0),
            rules=rules,
            match_all=data.get("match_all", True),
        )


def create_emotional_trigger(
    description: str,
    rules: list[dict[str, Any]],
    response: TriggerResponse | None = None,
    match_all: bool = True,
    active: bool = True,
    priority: int = 0,
) -> EmotionalTrigger:
    """Create an emotional trigger.

    Factory function for creating emotional triggers with rules.

    Args:
        description: Human-readable description of the trigger.
        rules: List of rule dictionaries with keys:
            - emotion: The emotion to monitor
            - threshold: The threshold value
            - operator: Comparison operator (default: ">")
        response: What happens when triggered (Mask or emotion changes).
        match_all: If True, all rules must match. If False, any matches.
        active: Whether the trigger is active.
        priority: Priority for ordering (higher = first).

    Returns:
        A new EmotionalTrigger instance.

    Example:
        >>> trigger = create_emotional_trigger(
        ...     description="Fear response",
        ...     rules=[
        ...         {"emotion": "anxious", "threshold": 0.7, "operator": ">"},
        ...         {"emotion": "helpless", "threshold": 0.5, "operator": ">"},
        ...     ],
        ...     response=STOIC_MASK,
        ...     match_all=False,  # Either condition triggers
        ... )
    """
    parsed_rules = []
    for rule_data in rules:
        parsed_rules.append(
            TriggerRule(
                field=rule_data.get("emotion", rule_data.get("field", "")),
                threshold=rule_data["threshold"],
                operator=rule_data.get("operator", ">"),
            )
        )

    return EmotionalTrigger(
        description=description,
        response=response,
        active=active,
        priority=priority,
        rules=parsed_rules,
        match_all=match_all,
    )


__all__ = [
    "EmotionalTrigger",
    "create_emotional_trigger",
]
