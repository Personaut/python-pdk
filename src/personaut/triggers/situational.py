"""Situational triggers for Personaut PDK.

Situational triggers activate based on the physical or contextual
environment. They can monitor specific situational factors and fire
when conditions match.

Example:
    >>> from personaut.triggers import create_situational_trigger
    >>> from personaut.emotions.state import EmotionalState
    >>>
    >>> # Trigger increased anxiety in crowded spaces
    >>> trigger = create_situational_trigger(
    ...     description="Crowded space anxiety",
    ...     rules=[{"field": "crowd_level", "threshold": 0.7, "operator": ">"}],
    ...     response={"anxious": 0.3, "insecure": 0.2},
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from personaut.triggers.trigger import Trigger, TriggerResponse, TriggerRule


@dataclass
class SituationalTrigger(Trigger):
    """Trigger that activates based on situational context.

    Situational triggers monitor environmental factors and fire when
    specific conditions are met.

    Attributes:
        rules: List of rules that define when this trigger fires.
        match_all: If True, all rules must match. If False, any rule matches.
        keyword_triggers: Optional keywords to match in situation description.

    Example:
        >>> trigger = SituationalTrigger(
        ...     description="Dark spaces",
        ...     rules=[
        ...         TriggerRule("lighting", 0.3, "<"),
        ...     ],
        ...     keyword_triggers=["dark", "dim", "unlit"],
        ... )
    """

    rules: list[TriggerRule] = field(default_factory=list)
    match_all: bool = True
    keyword_triggers: list[str] = field(default_factory=list)

    def check(self, context: Any) -> bool:
        """Check if this trigger should fire based on situation.

        Args:
            context: The situational context. Can be:
                - SituationalContext object
                - dict with field values
                - str (situation description for keyword matching)

        Returns:
            True if the trigger conditions are met.
        """
        if not self.active:
            return False

        # Handle string context (keyword matching)
        if isinstance(context, str):
            return self._check_keywords(context)

        # Handle dict context
        if isinstance(context, dict):
            return self._check_dict(context)

        # Handle SituationalContext object
        if hasattr(context, "to_dict"):
            return self._check_dict(context.to_dict())

        return False

    def _check_keywords(self, text: str) -> bool:
        """Check if any keywords match in the text."""
        if not self.keyword_triggers:
            return False

        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.keyword_triggers)

    def _check_dict(self, data: dict[str, Any]) -> bool:
        """Check rules against a dictionary of values."""
        # First check keywords if description is present
        if self.keyword_triggers:
            description = data.get("description", "")
            if isinstance(description, str) and self._check_keywords(description):
                return True

        # If no rules, only keyword matching applies
        if not self.rules:
            return False

        results = []
        for rule in self.rules:
            value = self._get_nested_value(data, rule.field)
            if value is None:
                results.append(False)
            elif isinstance(value, (int, float)):
                results.append(rule.evaluate(float(value)))
            else:
                results.append(False)

        if self.match_all:
            return all(results)
        return any(results)

    def _get_nested_value(self, data: dict[str, Any], field: str) -> Any:
        """Get a value from nested dict using dot notation.

        Args:
            data: The dictionary to search.
            field: Field name, optionally with dots for nesting.

        Returns:
            The value if found, None otherwise.
        """
        parts = field.split(".")
        current: Any = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    def add_rule(
        self,
        field: str,
        threshold: float,
        operator: str = ">",
    ) -> None:
        """Add a rule to this trigger.

        Args:
            field: The situational field to monitor.
            threshold: The threshold value.
            operator: Comparison operator.
        """
        self.rules.append(TriggerRule(field, threshold, operator))

    def add_keyword(self, keyword: str) -> None:
        """Add a keyword trigger.

        Args:
            keyword: The keyword to match in situation descriptions.
        """
        if keyword not in self.keyword_triggers:
            self.keyword_triggers.append(keyword)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data["rules"] = [rule.to_dict() for rule in self.rules]
        data["match_all"] = self.match_all
        data["keyword_triggers"] = self.keyword_triggers
        data["type"] = "situational"
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SituationalTrigger:
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
            keyword_triggers=data.get("keyword_triggers", []),
        )


def create_situational_trigger(
    description: str,
    rules: list[dict[str, Any]] | None = None,
    keywords: list[str] | None = None,
    response: TriggerResponse | None = None,
    match_all: bool = True,
    active: bool = True,
    priority: int = 0,
) -> SituationalTrigger:
    """Create a situational trigger.

    Factory function for creating situational triggers.

    Args:
        description: Human-readable description of the trigger.
        rules: List of rule dictionaries with keys:
            - field: The situational field to monitor
            - threshold: The threshold value
            - operator: Comparison operator (default: ">")
        keywords: Optional keywords to match in situation descriptions.
        response: What happens when triggered (Mask or emotion changes).
        match_all: If True, all rules must match. If False, any matches.
        active: Whether the trigger is active.
        priority: Priority for ordering (higher = first).

    Returns:
        A new SituationalTrigger instance.

    Example:
        >>> trigger = create_situational_trigger(
        ...     description="Dark enclosed spaces",
        ...     rules=[{"field": "lighting", "threshold": 0.3, "operator": "<"}],
        ...     keywords=["basement", "closet", "cave"],
        ...     response={"anxious": 0.4, "helpless": 0.3},
        ... )
    """
    parsed_rules = []
    for rule_data in rules or []:
        parsed_rules.append(
            TriggerRule(
                field=rule_data["field"],
                threshold=rule_data["threshold"],
                operator=rule_data.get("operator", ">"),
            )
        )

    return SituationalTrigger(
        description=description,
        response=response,
        active=active,
        priority=priority,
        rules=parsed_rules,
        match_all=match_all,
        keyword_triggers=keywords or [],
    )


__all__ = [
    "SituationalTrigger",
    "create_situational_trigger",
]
