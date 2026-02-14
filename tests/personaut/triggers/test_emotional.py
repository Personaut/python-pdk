"""Tests for emotional triggers."""

from __future__ import annotations

import pytest

from personaut.emotions.state import EmotionalState
from personaut.masks import STOIC_MASK
from personaut.triggers import (
    EmotionalTrigger,
    TriggerRule,
    create_emotional_trigger,
)


class TestTriggerRule:
    """Tests for TriggerRule class."""

    def test_create_rule(self) -> None:
        """Should create a rule with basic attributes."""
        rule = TriggerRule(field="anxious", threshold=0.8, operator=">")

        assert rule.field == "anxious"
        assert rule.threshold == 0.8
        assert rule.operator == ">"

    def test_evaluate_greater_than(self) -> None:
        """Should evaluate greater than correctly."""
        rule = TriggerRule(field="anxious", threshold=0.5, operator=">")

        assert rule.evaluate(0.7) is True
        assert rule.evaluate(0.5) is False
        assert rule.evaluate(0.3) is False

    def test_evaluate_less_than(self) -> None:
        """Should evaluate less than correctly."""
        rule = TriggerRule(field="cheerful", threshold=0.5, operator="<")

        assert rule.evaluate(0.3) is True
        assert rule.evaluate(0.5) is False
        assert rule.evaluate(0.7) is False

    def test_evaluate_greater_equal(self) -> None:
        """Should evaluate greater or equal correctly."""
        rule = TriggerRule(field="anxious", threshold=0.5, operator=">=")

        assert rule.evaluate(0.7) is True
        assert rule.evaluate(0.5) is True
        assert rule.evaluate(0.3) is False

    def test_evaluate_less_equal(self) -> None:
        """Should evaluate less or equal correctly."""
        rule = TriggerRule(field="cheerful", threshold=0.5, operator="<=")

        assert rule.evaluate(0.3) is True
        assert rule.evaluate(0.5) is True
        assert rule.evaluate(0.7) is False

    def test_evaluate_equal(self) -> None:
        """Should evaluate equality correctly."""
        rule = TriggerRule(field="anxious", threshold=0.5, operator="==")

        assert rule.evaluate(0.5) is True
        assert rule.evaluate(0.4) is False

    def test_evaluate_not_equal(self) -> None:
        """Should evaluate not equal correctly."""
        rule = TriggerRule(field="anxious", threshold=0.5, operator="!=")

        assert rule.evaluate(0.4) is True
        assert rule.evaluate(0.5) is False

    def test_evaluate_unknown_operator(self) -> None:
        """Should raise error for unknown operator."""
        rule = TriggerRule(field="anxious", threshold=0.5, operator="~")

        with pytest.raises(ValueError):
            rule.evaluate(0.5)

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        rule = TriggerRule(field="anxious", threshold=0.8, operator=">")

        data = rule.to_dict()

        assert data["field"] == "anxious"
        assert data["threshold"] == 0.8
        assert data["operator"] == ">"

    def test_from_dict(self) -> None:
        """Should deserialize from dictionary."""
        data = {"field": "cheerful", "threshold": 0.6, "operator": "<"}

        rule = TriggerRule.from_dict(data)

        assert rule.field == "cheerful"
        assert rule.threshold == 0.6
        assert rule.operator == "<"


class TestEmotionalTrigger:
    """Tests for EmotionalTrigger class."""

    def test_create_trigger(self) -> None:
        """Should create a trigger with basic attributes."""
        trigger = EmotionalTrigger(
            description="High anxiety",
            rules=[TriggerRule("anxious", 0.8, ">")],
        )

        assert trigger.description == "High anxiety"
        assert len(trigger.rules) == 1
        assert trigger.active is True

    def test_check_single_rule_match(self) -> None:
        """Should fire when single rule matches."""
        trigger = EmotionalTrigger(
            description="High anxiety",
            rules=[TriggerRule("anxious", 0.7, ">")],
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.9)

        assert trigger.check(state) is True

    def test_check_single_rule_no_match(self) -> None:
        """Should not fire when rule doesn't match."""
        trigger = EmotionalTrigger(
            description="High anxiety",
            rules=[TriggerRule("anxious", 0.7, ">")],
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.5)

        assert trigger.check(state) is False

    def test_check_multiple_rules_match_all(self) -> None:
        """Should require all rules when match_all is True."""
        trigger = EmotionalTrigger(
            description="Anxiety crisis",
            rules=[
                TriggerRule("anxious", 0.7, ">"),
                TriggerRule("helpless", 0.5, ">"),
            ],
            match_all=True,
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.change_emotion("helpless", 0.8)

        assert trigger.check(state) is True

        # One rule fails
        state.change_emotion("helpless", 0.3)
        assert trigger.check(state) is False

    def test_check_multiple_rules_match_any(self) -> None:
        """Should accept any rule when match_all is False."""
        trigger = EmotionalTrigger(
            description="Fear response",
            rules=[
                TriggerRule("anxious", 0.8, ">"),
                TriggerRule("helpless", 0.8, ">"),
            ],
            match_all=False,
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.change_emotion("helpless", 0.3)

        # Only one rule matches, but that's enough
        assert trigger.check(state) is True

    def test_check_inactive_trigger(self) -> None:
        """Should not fire when trigger is inactive."""
        trigger = EmotionalTrigger(
            description="High anxiety",
            rules=[TriggerRule("anxious", 0.7, ">")],
            active=False,
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.9)

        assert trigger.check(state) is False

    def test_check_no_rules(self) -> None:
        """Should not fire when no rules defined."""
        trigger = EmotionalTrigger(
            description="Empty trigger",
            rules=[],
        )

        state = EmotionalState()

        assert trigger.check(state) is False

    def test_add_rule(self) -> None:
        """Should add rules dynamically."""
        trigger = EmotionalTrigger(description="Dynamic")

        trigger.add_rule("anxious", 0.7, ">")
        trigger.add_rule("angry", 0.5, ">")

        assert len(trigger.rules) == 2

    def test_fire_with_mask_response(self) -> None:
        """Should apply mask when fired."""
        trigger = EmotionalTrigger(
            description="Crisis mode",
            rules=[TriggerRule("anxious", 0.7, ">")],
            response=STOIC_MASK,
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.change_emotion("angry", 0.7)

        modified = trigger.fire(state)

        # Stoic mask reduces these emotions
        assert modified.get_emotion("anxious") < state.get_emotion("anxious")
        assert modified.get_emotion("angry") < state.get_emotion("angry")

    def test_fire_with_dict_response(self) -> None:
        """Should apply emotion modifications when fired."""
        trigger = EmotionalTrigger(
            description="Calm down",
            rules=[TriggerRule("angry", 0.7, ">")],
            response={"angry": -0.3, "content": 0.2},
        )

        state = EmotionalState()
        state.change_emotion("angry", 0.8)
        state.change_emotion("content", 0.3)

        modified = trigger.fire(state)

        assert modified.get_emotion("angry") == pytest.approx(0.5, abs=0.01)
        assert modified.get_emotion("content") == pytest.approx(0.5, abs=0.01)

    def test_fire_no_response(self) -> None:
        """Should return same state when no response defined."""
        trigger = EmotionalTrigger(
            description="No response",
            rules=[TriggerRule("anxious", 0.7, ">")],
            response=None,
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.9)

        modified = trigger.fire(state)

        # Should be functionally equivalent
        assert modified.get_emotion("anxious") == state.get_emotion("anxious")

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        trigger = EmotionalTrigger(
            description="Test",
            rules=[TriggerRule("anxious", 0.7, ">")],
            match_all=True,
            priority=5,
        )

        data = trigger.to_dict()

        assert data["description"] == "Test"
        assert data["type"] == "emotional"
        assert len(data["rules"]) == 1
        assert data["match_all"] is True
        assert data["priority"] == 5

    def test_from_dict(self) -> None:
        """Should deserialize from dictionary."""
        data = {
            "description": "Restored",
            "type": "emotional",
            "rules": [{"field": "anxious", "threshold": 0.8, "operator": ">"}],
            "match_all": False,
            "active": True,
            "priority": 3,
            "response": None,
        }

        trigger = EmotionalTrigger.from_dict(data)

        assert trigger.description == "Restored"
        assert len(trigger.rules) == 1
        assert trigger.match_all is False


class TestCreateEmotionalTrigger:
    """Tests for create_emotional_trigger factory."""

    def test_create_basic(self) -> None:
        """Should create trigger with basic options."""
        trigger = create_emotional_trigger(
            description="High anxiety",
            rules=[{"emotion": "anxious", "threshold": 0.8}],
        )

        assert trigger.description == "High anxiety"
        assert len(trigger.rules) == 1

    def test_create_with_operator(self) -> None:
        """Should create trigger with custom operator."""
        trigger = create_emotional_trigger(
            description="Low mood",
            rules=[{"emotion": "cheerful", "threshold": 0.3, "operator": "<"}],
        )

        assert trigger.rules[0].operator == "<"

    def test_create_with_response(self) -> None:
        """Should create trigger with response."""
        trigger = create_emotional_trigger(
            description="Anger response",
            rules=[{"emotion": "angry", "threshold": 0.7, "operator": ">"}],
            response=STOIC_MASK,
        )

        assert trigger.response is STOIC_MASK

    def test_create_with_match_any(self) -> None:
        """Should create trigger with match_all=False."""
        trigger = create_emotional_trigger(
            description="Fear response",
            rules=[
                {"emotion": "anxious", "threshold": 0.8, "operator": ">"},
                {"emotion": "helpless", "threshold": 0.8, "operator": ">"},
            ],
            match_all=False,
        )

        assert trigger.match_all is False

    def test_create_with_priority(self) -> None:
        """Should create trigger with priority."""
        trigger = create_emotional_trigger(
            description="Important",
            rules=[{"emotion": "anxious", "threshold": 0.9, "operator": ">"}],
            priority=10,
        )

        assert trigger.priority == 10

    def test_create_with_field_key(self) -> None:
        """Should accept 'field' key for emotion."""
        trigger = create_emotional_trigger(
            description="Test",
            rules=[{"field": "anxious", "threshold": 0.8}],
        )

        assert trigger.rules[0].field == "anxious"


class TestEmotionalTriggerIntegration:
    """Integration tests for emotional triggers."""

    def test_anxiety_stoic_response(self) -> None:
        """Should activate stoic mask on high anxiety."""
        trigger = create_emotional_trigger(
            description="Anxiety crisis",
            rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
            response=STOIC_MASK,
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.change_emotion("angry", 0.6)
        state.change_emotion("cheerful", 0.4)

        if trigger.check(state):
            modified = trigger.fire(state)
            assert modified.get_emotion("anxious") < state.get_emotion("anxious")

    def test_combined_triggers(self) -> None:
        """Should handle multiple triggers with priorities."""
        # Low priority trigger
        low = create_emotional_trigger(
            description="Low priority",
            rules=[{"emotion": "anxious", "threshold": 0.5, "operator": ">"}],
            response={"content": 0.1},
            priority=1,
        )

        # High priority trigger
        high = create_emotional_trigger(
            description="High priority",
            rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
            response=STOIC_MASK,
            priority=10,
        )

        # Sort by priority
        triggers = sorted([low, high], key=lambda t: t.priority, reverse=True)

        assert triggers[0].priority == 10
        assert triggers[1].priority == 1
