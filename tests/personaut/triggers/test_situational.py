"""Tests for situational triggers."""

from __future__ import annotations

import pytest

from personaut.emotions.state import EmotionalState
from personaut.masks import GUARDED_MASK, STOIC_MASK
from personaut.triggers import (
    SituationalTrigger,
    TriggerRule,
    create_situational_trigger,
)


class TestSituationalTrigger:
    """Tests for SituationalTrigger class."""

    def test_create_trigger(self) -> None:
        """Should create a trigger with basic attributes."""
        trigger = SituationalTrigger(
            description="Dark spaces",
            rules=[TriggerRule("lighting", 0.3, "<")],
            keyword_triggers=["dark", "dim"],
        )

        assert trigger.description == "Dark spaces"
        assert len(trigger.rules) == 1
        assert len(trigger.keyword_triggers) == 2

    def test_check_keyword_match_string(self) -> None:
        """Should match keywords in string context."""
        trigger = SituationalTrigger(
            description="Dark spaces",
            keyword_triggers=["dark", "basement", "closet"],
        )

        assert trigger.check("Walking into a dark basement") is True
        assert trigger.check("Bright sunny day") is False

    def test_check_keyword_case_insensitive(self) -> None:
        """Should match keywords case-insensitively."""
        trigger = SituationalTrigger(
            description="Dark spaces",
            keyword_triggers=["DARK", "Basement"],
        )

        assert trigger.check("dark room") is True
        assert trigger.check("BASEMENT") is True

    def test_check_dict_with_description(self) -> None:
        """Should check keywords in dict description."""
        trigger = SituationalTrigger(
            description="Danger",
            keyword_triggers=["danger", "emergency"],
        )

        context = {"description": "Emergency situation at work"}

        assert trigger.check(context) is True

    def test_check_dict_with_rules(self) -> None:
        """Should check rules against dict values."""
        trigger = SituationalTrigger(
            description="Crowded",
            rules=[TriggerRule("crowd_level", 0.7, ">")],
        )

        crowded = {"crowd_level": 0.8}
        empty = {"crowd_level": 0.3}

        assert trigger.check(crowded) is True
        assert trigger.check(empty) is False

    def test_check_nested_dict_values(self) -> None:
        """Should access nested dict values with dot notation."""
        trigger = SituationalTrigger(
            description="Low lighting",
            rules=[TriggerRule("environment.lighting", 0.3, "<")],
        )

        dark = {"environment": {"lighting": 0.1}}
        bright = {"environment": {"lighting": 0.8}}

        assert trigger.check(dark) is True
        assert trigger.check(bright) is False

    def test_check_rules_match_all(self) -> None:
        """Should require all rules when match_all is True."""
        trigger = SituationalTrigger(
            description="Stressful environment",
            rules=[
                TriggerRule("noise_level", 0.7, ">"),
                TriggerRule("crowd_level", 0.7, ">"),
            ],
            match_all=True,
        )

        both_high = {"noise_level": 0.9, "crowd_level": 0.8}
        one_high = {"noise_level": 0.9, "crowd_level": 0.3}

        assert trigger.check(both_high) is True
        assert trigger.check(one_high) is False

    def test_check_rules_match_any(self) -> None:
        """Should accept any rule when match_all is False."""
        trigger = SituationalTrigger(
            description="Uncomfortable",
            rules=[
                TriggerRule("noise_level", 0.8, ">"),
                TriggerRule("crowd_level", 0.8, ">"),
            ],
            match_all=False,
        )

        one_high = {"noise_level": 0.9, "crowd_level": 0.3}

        assert trigger.check(one_high) is True

    def test_check_inactive_trigger(self) -> None:
        """Should not fire when trigger is inactive."""
        trigger = SituationalTrigger(
            description="Dark",
            keyword_triggers=["dark"],
            active=False,
        )

        assert trigger.check("dark room") is False

    def test_check_no_rules_or_keywords(self) -> None:
        """Should not fire when no rules or keywords."""
        trigger = SituationalTrigger(
            description="Empty",
            rules=[],
            keyword_triggers=[],
        )

        assert trigger.check("any situation") is False
        assert trigger.check({"any": "data"}) is False

    def test_check_missing_field(self) -> None:
        """Should return False when field is missing."""
        trigger = SituationalTrigger(
            description="Lighting",
            rules=[TriggerRule("lighting", 0.3, "<")],
        )

        assert trigger.check({"noise": 0.5}) is False

    def test_check_situational_context_object(self) -> None:
        """Should work with objects that have to_dict method."""

        class FakeContext:
            def to_dict(self) -> dict:
                return {"crowd_level": 0.9, "description": "Very crowded"}

        trigger = SituationalTrigger(
            description="Crowded",
            rules=[TriggerRule("crowd_level", 0.8, ">")],
        )

        assert trigger.check(FakeContext()) is True

    def test_add_rule(self) -> None:
        """Should add rules dynamically."""
        trigger = SituationalTrigger(description="Dynamic")

        trigger.add_rule("lighting", 0.3, "<")
        trigger.add_rule("noise_level", 0.7, ">")

        assert len(trigger.rules) == 2

    def test_add_keyword(self) -> None:
        """Should add keywords dynamically."""
        trigger = SituationalTrigger(description="Dynamic")

        trigger.add_keyword("dark")
        trigger.add_keyword("basement")

        assert len(trigger.keyword_triggers) == 2

    def test_add_keyword_no_duplicates(self) -> None:
        """Should not add duplicate keywords."""
        trigger = SituationalTrigger(description="Dynamic")

        trigger.add_keyword("dark")
        trigger.add_keyword("dark")

        assert len(trigger.keyword_triggers) == 1

    def test_fire_with_mask_response(self) -> None:
        """Should apply mask when fired."""
        trigger = SituationalTrigger(
            description="Danger",
            keyword_triggers=["danger"],
            response=GUARDED_MASK,
        )

        state = EmotionalState()
        state.change_emotion("trusting", 0.7)

        modified = trigger.fire(state)

        # Guarded mask reduces trust
        assert modified.get_emotion("trusting") < state.get_emotion("trusting")

    def test_fire_with_dict_response(self) -> None:
        """Should apply emotion modifications when fired."""
        trigger = SituationalTrigger(
            description="Dark space anxiety",
            keyword_triggers=["dark"],
            response={"anxious": 0.3, "helpless": 0.2},
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.4)
        state.change_emotion("helpless", 0.3)

        modified = trigger.fire(state)

        assert modified.get_emotion("anxious") == pytest.approx(0.7, abs=0.01)
        assert modified.get_emotion("helpless") == pytest.approx(0.5, abs=0.01)

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        trigger = SituationalTrigger(
            description="Test",
            rules=[TriggerRule("lighting", 0.3, "<")],
            keyword_triggers=["dark", "dim"],
            match_all=False,
        )

        data = trigger.to_dict()

        assert data["description"] == "Test"
        assert data["type"] == "situational"
        assert len(data["rules"]) == 1
        assert data["keyword_triggers"] == ["dark", "dim"]
        assert data["match_all"] is False

    def test_from_dict(self) -> None:
        """Should deserialize from dictionary."""
        data = {
            "description": "Restored",
            "type": "situational",
            "rules": [{"field": "lighting", "threshold": 0.3, "operator": "<"}],
            "keyword_triggers": ["basement"],
            "match_all": True,
            "active": True,
            "priority": 5,
            "response": None,
        }

        trigger = SituationalTrigger.from_dict(data)

        assert trigger.description == "Restored"
        assert len(trigger.rules) == 1
        assert trigger.keyword_triggers == ["basement"]


class TestCreateSituationalTrigger:
    """Tests for create_situational_trigger factory."""

    def test_create_with_keywords(self) -> None:
        """Should create trigger with keywords."""
        trigger = create_situational_trigger(
            description="Dark spaces",
            keywords=["dark", "basement", "closet"],
        )

        assert len(trigger.keyword_triggers) == 3
        assert trigger.check("In a dark basement") is True

    def test_create_with_rules(self) -> None:
        """Should create trigger with rules."""
        trigger = create_situational_trigger(
            description="Crowded",
            rules=[{"field": "crowd_level", "threshold": 0.7, "operator": ">"}],
        )

        assert len(trigger.rules) == 1
        assert trigger.check({"crowd_level": 0.9}) is True

    def test_create_with_both(self) -> None:
        """Should create trigger with keywords and rules."""
        trigger = create_situational_trigger(
            description="Stressful",
            rules=[{"field": "noise_level", "threshold": 0.8, "operator": ">"}],
            keywords=["emergency"],
        )

        # Keywords and rules both work
        assert trigger.check("emergency situation") is True
        assert trigger.check({"noise_level": 0.9}) is True

    def test_create_with_response(self) -> None:
        """Should create trigger with response."""
        trigger = create_situational_trigger(
            description="Danger",
            keywords=["danger"],
            response=GUARDED_MASK,
        )

        assert trigger.response is GUARDED_MASK

    def test_create_with_dict_response(self) -> None:
        """Should create trigger with dict response."""
        trigger = create_situational_trigger(
            description="Anxiety inducing",
            keywords=["scary"],
            response={"anxious": 0.4, "helpless": 0.3},
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.2)
        state.change_emotion("helpless", 0.2)

        modified = trigger.fire(state)

        assert modified.get_emotion("anxious") == pytest.approx(0.6, abs=0.01)

    def test_create_with_priority(self) -> None:
        """Should create trigger with priority."""
        trigger = create_situational_trigger(
            description="Important",
            keywords=["critical"],
            priority=10,
        )

        assert trigger.priority == 10

    def test_create_match_any(self) -> None:
        """Should create trigger with match_all=False."""
        trigger = create_situational_trigger(
            description="Uncomfortable",
            rules=[
                {"field": "noise", "threshold": 0.8, "operator": ">"},
                {"field": "crowd", "threshold": 0.8, "operator": ">"},
            ],
            match_all=False,
        )

        # Either condition works
        assert trigger.check({"noise": 0.9, "crowd": 0.3}) is True


class TestSituationalTriggerIntegration:
    """Integration tests for situational triggers."""

    def test_dark_space_phobia(self) -> None:
        """Should trigger anxiety response in dark spaces."""
        trigger = create_situational_trigger(
            description="Dark space phobia",
            keywords=["dark", "basement", "cave", "closet"],
            response={"anxious": 0.4, "helpless": 0.3, "insecure": 0.2},
        )

        state = EmotionalState()
        state.change_emotion("anxious", 0.2)
        state.change_emotion("cheerful", 0.6)

        situation = "Walking into a dark basement alone"

        if trigger.check(situation):
            modified = trigger.fire(state)
            assert modified.get_emotion("anxious") > state.get_emotion("anxious")

    def test_crowded_space_response(self) -> None:
        """Should trigger guarded response in crowded spaces."""
        trigger = create_situational_trigger(
            description="Crowd anxiety",
            rules=[{"field": "crowd_level", "threshold": 0.8, "operator": ">"}],
            response=GUARDED_MASK,
        )

        state = EmotionalState()
        state.change_emotion("trusting", 0.7)
        state.change_emotion("cheerful", 0.6)

        context = {"crowd_level": 0.9, "noise_level": 0.7}

        if trigger.check(context):
            modified = trigger.fire(state)
            assert modified.get_emotion("trusting") < state.get_emotion("trusting")

    def test_combined_keyword_and_rule_check(self) -> None:
        """Should handle combined keyword and rule triggers."""
        trigger = create_situational_trigger(
            description="Emergency",
            keywords=["emergency", "crisis"],
            rules=[{"field": "danger_level", "threshold": 0.9, "operator": ">"}],
            match_all=False,
            response=STOIC_MASK,
        )

        # Keyword match
        assert trigger.check("This is a crisis!") is True

        # Rule match
        assert trigger.check({"danger_level": 0.95}) is True

        # Keyword in dict description
        assert trigger.check({"description": "emergency situation"}) is True
