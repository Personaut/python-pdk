"""Tests for Mask class and mask functionality."""

from __future__ import annotations

import pytest

from personaut.emotions.state import EmotionalState
from personaut.masks import (
    CASUAL_MASK,
    DEFAULT_MASKS,
    ENTHUSIASTIC_MASK,
    GUARDED_MASK,
    NURTURING_MASK,
    PROFESSIONAL_MASK,
    STOIC_MASK,
    Mask,
    create_mask,
    get_mask_by_name,
)


class TestMask:
    """Tests for Mask class."""

    def test_create_mask(self) -> None:
        """Should create a mask with basic attributes."""
        mask = Mask(
            name="test",
            emotional_modifications={"anxious": -0.3},
            trigger_situations=["meeting"],
        )

        assert mask.name == "test"
        assert mask.emotional_modifications == {"anxious": -0.3}
        assert mask.trigger_situations == ["meeting"]
        assert mask.active_by_default is False

    def test_create_mask_with_defaults(self) -> None:
        """Should create mask with default values."""
        mask = Mask(name="simple")

        assert mask.name == "simple"
        assert mask.emotional_modifications == {}
        assert mask.trigger_situations == []
        assert mask.active_by_default is False
        assert mask.description == ""

    def test_mask_validation_bounds(self) -> None:
        """Should validate modification values are within bounds."""
        with pytest.raises(ValueError):
            Mask(name="invalid", emotional_modifications={"angry": 1.5})

        with pytest.raises(ValueError):
            Mask(name="invalid", emotional_modifications={"anxious": -1.5})

    def test_apply_reduces_emotion(self) -> None:
        """Should reduce emotions with negative modifications."""
        mask = Mask(
            name="suppress_anger",
            emotional_modifications={"angry": -0.5},
        )

        state = EmotionalState()
        state.change_emotion("angry", 0.8)

        modified = mask.apply(state)

        assert modified.get_emotion("angry") == pytest.approx(0.3, abs=0.01)

    def test_apply_increases_emotion(self) -> None:
        """Should increase emotions with positive modifications."""
        mask = Mask(
            name="boost_joy",
            emotional_modifications={"cheerful": 0.4},
        )

        state = EmotionalState()
        state.change_emotion("cheerful", 0.3)

        modified = mask.apply(state)

        assert modified.get_emotion("cheerful") == pytest.approx(0.7, abs=0.01)

    def test_apply_clamps_to_bounds(self) -> None:
        """Should clamp modified values to [0, 1]."""
        mask = Mask(
            name="extreme",
            emotional_modifications={"angry": -0.8, "cheerful": 0.8},
        )

        state = EmotionalState()
        state.change_emotion("angry", 0.3)  # 0.3 - 0.8 = -0.5 -> clamped to 0
        state.change_emotion("cheerful", 0.8)  # 0.8 + 0.8 = 1.6 -> clamped to 1

        modified = mask.apply(state)

        assert modified.get_emotion("angry") == 0.0
        assert modified.get_emotion("cheerful") == 1.0

    def test_apply_does_not_modify_original(self) -> None:
        """Should not modify the original emotional state."""
        mask = Mask(
            name="test",
            emotional_modifications={"angry": -0.5},
        )

        state = EmotionalState()
        state.change_emotion("angry", 0.8)

        mask.apply(state)

        # Original should be unchanged
        assert state.get_emotion("angry") == 0.8

    def test_should_trigger_with_keyword(self) -> None:
        """Should trigger when keyword is found."""
        mask = Mask(
            name="work",
            trigger_situations=["office", "meeting"],
        )

        assert mask.should_trigger("Going to an office meeting") is True
        assert mask.should_trigger("At the beach") is False

    def test_should_trigger_case_insensitive(self) -> None:
        """Should match keywords case-insensitively."""
        mask = Mask(
            name="work",
            trigger_situations=["Office", "MEETING"],
        )

        assert mask.should_trigger("office") is True
        assert mask.should_trigger("OFFICE") is True

    def test_should_trigger_active_by_default(self) -> None:
        """Should always trigger when active_by_default is True."""
        mask = Mask(
            name="always",
            active_by_default=True,
        )

        assert mask.should_trigger("any situation") is True
        assert mask.should_trigger("") is True

    def test_get_modification(self) -> None:
        """Should return modification value for emotion."""
        mask = Mask(
            name="test",
            emotional_modifications={"angry": -0.5, "cheerful": 0.3},
        )

        assert mask.get_modification("angry") == -0.5
        assert mask.get_modification("cheerful") == 0.3
        assert mask.get_modification("unknown") == 0.0

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        mask = Mask(
            name="test",
            emotional_modifications={"angry": -0.3},
            trigger_situations=["office"],
            active_by_default=False,
            description="Test mask",
        )

        data = mask.to_dict()

        assert data["name"] == "test"
        assert data["emotional_modifications"] == {"angry": -0.3}
        assert data["trigger_situations"] == ["office"]
        assert data["active_by_default"] is False
        assert data["description"] == "Test mask"

    def test_from_dict(self) -> None:
        """Should deserialize from dictionary."""
        data = {
            "name": "restored",
            "emotional_modifications": {"anxious": -0.4},
            "trigger_situations": ["interview"],
            "active_by_default": True,
            "description": "Restored mask",
        }

        mask = Mask.from_dict(data)

        assert mask.name == "restored"
        assert mask.emotional_modifications == {"anxious": -0.4}
        assert mask.trigger_situations == ["interview"]
        assert mask.active_by_default is True


class TestCreateMask:
    """Tests for create_mask factory function."""

    def test_create_basic(self) -> None:
        """Should create mask with required fields."""
        mask = create_mask(name="simple")

        assert mask.name == "simple"

    def test_create_with_modifications(self) -> None:
        """Should create mask with emotional modifications."""
        mask = create_mask(
            name="suppress",
            emotional_modifications={"angry": -0.5, "anxious": -0.3},
        )

        assert mask.emotional_modifications == {"angry": -0.5, "anxious": -0.3}

    def test_create_with_triggers(self) -> None:
        """Should create mask with trigger situations."""
        mask = create_mask(
            name="work",
            trigger_situations=["office", "meeting", "client"],
        )

        assert len(mask.trigger_situations) == 3
        assert "office" in mask.trigger_situations

    def test_create_with_all_options(self) -> None:
        """Should create mask with all options."""
        mask = create_mask(
            name="full",
            emotional_modifications={"cheerful": 0.3},
            trigger_situations=["party"],
            active_by_default=True,
            description="Full featured mask",
        )

        assert mask.name == "full"
        assert mask.active_by_default is True
        assert mask.description == "Full featured mask"


class TestDefaultMasks:
    """Tests for predefined default masks."""

    def test_all_default_masks_defined(self) -> None:
        """Should have all expected default masks."""
        assert len(DEFAULT_MASKS) >= 6

    def test_professional_mask_defined(self) -> None:
        """PROFESSIONAL_MASK should be properly defined."""
        assert PROFESSIONAL_MASK.name == "professional"
        assert "angry" in PROFESSIONAL_MASK.emotional_modifications
        assert "office" in PROFESSIONAL_MASK.trigger_situations

    def test_casual_mask_defined(self) -> None:
        """CASUAL_MASK should be properly defined."""
        assert CASUAL_MASK.name == "casual"
        assert len(CASUAL_MASK.trigger_situations) > 0

    def test_stoic_mask_defined(self) -> None:
        """STOIC_MASK should be properly defined."""
        assert STOIC_MASK.name == "stoic"
        assert STOIC_MASK.emotional_modifications.get("anxious", 0) < 0
        assert "crisis" in STOIC_MASK.trigger_situations

    def test_enthusiastic_mask_defined(self) -> None:
        """ENTHUSIASTIC_MASK should be properly defined."""
        assert ENTHUSIASTIC_MASK.name == "enthusiastic"
        assert ENTHUSIASTIC_MASK.emotional_modifications.get("excited", 0) > 0

    def test_nurturing_mask_defined(self) -> None:
        """NURTURING_MASK should be properly defined."""
        assert NURTURING_MASK.name == "nurturing"
        assert NURTURING_MASK.emotional_modifications.get("nurturing", 0) > 0

    def test_guarded_mask_defined(self) -> None:
        """GUARDED_MASK should be properly defined."""
        assert GUARDED_MASK.name == "guarded"
        assert GUARDED_MASK.emotional_modifications.get("trusting", 0) < 0

    def test_get_mask_by_name(self) -> None:
        """Should retrieve mask by name."""
        mask = get_mask_by_name("professional")

        assert mask is PROFESSIONAL_MASK

    def test_get_mask_by_name_case_insensitive(self) -> None:
        """Should retrieve mask case-insensitively."""
        mask = get_mask_by_name("STOIC")

        assert mask is STOIC_MASK

    def test_get_mask_by_name_not_found(self) -> None:
        """Should return None for unknown mask."""
        mask = get_mask_by_name("nonexistent")

        assert mask is None

    def test_professional_mask_triggers_on_office(self) -> None:
        """Professional mask should trigger on office keywords."""
        assert PROFESSIONAL_MASK.should_trigger("Going to the office")
        assert PROFESSIONAL_MASK.should_trigger("Have a meeting with client")
        assert not PROFESSIONAL_MASK.should_trigger("Relaxing at beach")

    def test_stoic_mask_triggers_on_crisis(self) -> None:
        """Stoic mask should trigger on crisis keywords."""
        assert STOIC_MASK.should_trigger("This is a crisis situation")
        assert STOIC_MASK.should_trigger("Emergency at work")
        assert not STOIC_MASK.should_trigger("Normal day at office")


class TestMaskApplication:
    """Integration tests for mask application."""

    def test_professional_mask_suppresses_anger(self) -> None:
        """Professional mask should suppress anger in emotional state."""
        state = EmotionalState()
        state.change_emotion("angry", 0.8)
        state.change_emotion("cheerful", 0.5)

        modified = PROFESSIONAL_MASK.apply(state)

        assert modified.get_emotion("angry") < state.get_emotion("angry")

    def test_enthusiastic_mask_boosts_excitement(self) -> None:
        """Enthusiastic mask should boost excitement."""
        state = EmotionalState()
        state.change_emotion("excited", 0.4)
        state.change_emotion("cheerful", 0.3)

        modified = ENTHUSIASTIC_MASK.apply(state)

        assert modified.get_emotion("excited") > state.get_emotion("excited")
        assert modified.get_emotion("cheerful") > state.get_emotion("cheerful")

    def test_stoic_mask_reduces_reactivity(self) -> None:
        """Stoic mask should reduce emotional reactivity."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.change_emotion("angry", 0.7)
        state.change_emotion("excited", 0.6)

        modified = STOIC_MASK.apply(state)

        # All reactive emotions should be reduced
        assert modified.get_emotion("anxious") < state.get_emotion("anxious")
        assert modified.get_emotion("angry") < state.get_emotion("angry")
        assert modified.get_emotion("excited") < state.get_emotion("excited")
