"""Tests for EmotionalState class."""

from __future__ import annotations

import pytest

from personaut.emotions.categories import EmotionCategory
from personaut.emotions.state import EmotionalState
from personaut.types.exceptions import EmotionNotFoundError, EmotionValueError


class TestEmotionalStateCreation:
    """Tests for EmotionalState initialization."""

    def test_default_creation(self) -> None:
        """Default creation should include all 36 emotions at 0.0."""
        state = EmotionalState()
        assert len(state) == 36
        assert state.get_emotion("anxious") == 0.0

    def test_creation_with_baseline(self) -> None:
        """Creation with baseline should set all emotions to that value."""
        state = EmotionalState(baseline=0.5)
        assert state.get_emotion("anxious") == 0.5
        assert state.get_emotion("hopeful") == 0.5

    def test_creation_with_subset(self) -> None:
        """Creation with emotion list should only track those emotions."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        assert len(state) == 2
        assert "anxious" in state
        assert "hopeful" in state
        assert "angry" not in state

    def test_creation_with_invalid_baseline(self) -> None:
        """Creation with invalid baseline should raise EmotionValueError."""
        with pytest.raises(EmotionValueError):
            EmotionalState(baseline=1.5)
        with pytest.raises(EmotionValueError):
            EmotionalState(baseline=-0.1)

    def test_creation_with_invalid_emotion(self) -> None:
        """Creation with unknown emotion should raise EmotionNotFoundError."""
        with pytest.raises(EmotionNotFoundError):
            EmotionalState(emotions=["anxious", "happiness"])


class TestChangeEmotion:
    """Tests for change_emotion method."""

    def test_change_valid_emotion(self) -> None:
        """Should change emotion value successfully."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.7)
        assert state.get_emotion("anxious") == 0.7

    def test_change_emotion_boundary_values(self) -> None:
        """Should accept boundary values 0.0 and 1.0."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.0)
        assert state.get_emotion("anxious") == 0.0
        state.change_emotion("anxious", 1.0)
        assert state.get_emotion("anxious") == 1.0

    def test_change_unknown_emotion(self) -> None:
        """Should raise EmotionNotFoundError for unknown emotions."""
        state = EmotionalState()
        with pytest.raises(EmotionNotFoundError):
            state.change_emotion("happiness", 0.5)

    def test_change_emotion_invalid_value_high(self) -> None:
        """Should raise EmotionValueError for values > 1.0."""
        state = EmotionalState()
        with pytest.raises(EmotionValueError):
            state.change_emotion("anxious", 1.1)

    def test_change_emotion_invalid_value_low(self) -> None:
        """Should raise EmotionValueError for values < 0.0."""
        state = EmotionalState()
        with pytest.raises(EmotionValueError):
            state.change_emotion("anxious", -0.1)


class TestChangeState:
    """Tests for change_state method."""

    def test_change_multiple_emotions(self) -> None:
        """Should change multiple emotions at once."""
        state = EmotionalState()
        state.change_state({"anxious": 0.7, "hopeful": 0.3})
        assert state.get_emotion("anxious") == 0.7
        assert state.get_emotion("hopeful") == 0.3

    def test_change_state_with_fill(self) -> None:
        """Should set unspecified emotions to fill value."""
        state = EmotionalState(emotions=["anxious", "hopeful", "angry"])
        state.change_state({"anxious": 0.8}, fill=0.1)
        assert state.get_emotion("anxious") == 0.8
        assert state.get_emotion("hopeful") == 0.1
        assert state.get_emotion("angry") == 0.1

    def test_change_state_without_fill(self) -> None:
        """Should leave unspecified emotions unchanged without fill."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        state.change_emotion("hopeful", 0.5)
        state.change_state({"anxious": 0.8})
        assert state.get_emotion("anxious") == 0.8
        assert state.get_emotion("hopeful") == 0.5  # Unchanged

    def test_change_state_invalid_fill(self) -> None:
        """Should raise EmotionValueError for invalid fill value."""
        state = EmotionalState()
        with pytest.raises(EmotionValueError):
            state.change_state({"anxious": 0.5}, fill=1.5)


class TestReset:
    """Tests for reset method."""

    def test_reset_to_zero(self) -> None:
        """Should reset all emotions to 0.0 by default."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.change_emotion("hopeful", 0.7)
        state.reset()
        assert state.get_emotion("anxious") == 0.0
        assert state.get_emotion("hopeful") == 0.0

    def test_reset_to_value(self) -> None:
        """Should reset all emotions to specified value."""
        state = EmotionalState()
        state.reset(0.3)
        assert state.get_emotion("anxious") == 0.3
        assert state.get_emotion("hopeful") == 0.3

    def test_reset_invalid_value(self) -> None:
        """Should raise EmotionValueError for invalid value."""
        state = EmotionalState()
        with pytest.raises(EmotionValueError):
            state.reset(1.5)


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict_returns_copy(self) -> None:
        """Should return a copy of the internal dictionary."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        state.change_emotion("anxious", 0.5)
        result = state.to_dict()
        result["anxious"] = 1.0  # Modify the returned dict
        assert state.get_emotion("anxious") == 0.5  # Original unchanged

    def test_to_dict_contents(self) -> None:
        """Should return dictionary with correct values."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        state.change_emotion("anxious", 0.5)
        result = state.to_dict()
        assert result == {"anxious": 0.5, "hopeful": 0.0}


class TestGetCategoryEmotions:
    """Tests for get_category_emotions method."""

    def test_get_fear_emotions(self) -> None:
        """Should return fear emotions with their values."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.8)
        state.change_emotion("helpless", 0.4)
        result = state.get_category_emotions(EmotionCategory.FEAR)
        assert result["anxious"] == 0.8
        assert result["helpless"] == 0.4

    def test_get_category_with_subset(self) -> None:
        """Should only return tracked emotions in category."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        result = state.get_category_emotions(EmotionCategory.FEAR)
        assert "anxious" in result
        assert "helpless" not in result


class TestGetCategoryAverage:
    """Tests for get_category_average method."""

    def test_average_calculation(self) -> None:
        """Should calculate correct average for a category."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.6)
        # All other fear emotions are 0.0, so average = 0.6/6 = 0.1
        avg = state.get_category_average(EmotionCategory.FEAR)
        assert abs(avg - 0.1) < 0.001

    def test_average_empty_category(self) -> None:
        """Should return 0.0 if no category emotions are tracked."""
        state = EmotionalState(emotions=["hopeful"])
        avg = state.get_category_average(EmotionCategory.ANGER)
        assert avg == 0.0


class TestGetDominant:
    """Tests for get_dominant method."""

    def test_get_dominant_single(self) -> None:
        """Should return the highest emotion."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.change_emotion("hopeful", 0.7)
        dominant = state.get_dominant()
        assert dominant == ("anxious", 0.9)

    def test_get_dominant_tie(self) -> None:
        """Should return first alphabetically on tie."""
        state = EmotionalState(emotions=["anxious", "angry"])
        state.change_emotion("anxious", 0.5)
        state.change_emotion("angry", 0.5)
        dominant = state.get_dominant()
        assert dominant == ("angry", 0.5)  # "angry" comes before "anxious"

    def test_get_dominant_all_zero(self) -> None:
        """Should return first emotion at 0.0 if all zeros."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        dominant = state.get_dominant()
        assert dominant[1] == 0.0


class TestGetTop:
    """Tests for get_top method."""

    def test_get_top_default(self) -> None:
        """Should return top 5 emotions by default."""
        state = EmotionalState()
        state.change_state(
            {
                "anxious": 0.9,
                "hopeful": 0.8,
                "angry": 0.7,
                "depressed": 0.6,  # Use valid emotion name
                "excited": 0.5,
                "content": 0.4,
            }
        )
        top = state.get_top()
        assert len(top) == 5
        assert top[0] == ("anxious", 0.9)
        assert top[1] == ("hopeful", 0.8)

    def test_get_top_custom_n(self) -> None:
        """Should return custom number of emotions."""
        state = EmotionalState()
        state.change_state({"anxious": 0.9, "hopeful": 0.8, "angry": 0.7})
        top = state.get_top(2)
        assert len(top) == 2

    def test_get_top_sorted(self) -> None:
        """Should be sorted by value descending."""
        state = EmotionalState()
        state.change_state({"anxious": 0.5, "hopeful": 0.9, "angry": 0.7})
        top = state.get_top(3)
        assert top[0][1] >= top[1][1] >= top[2][1]


class TestAnyAbove:
    """Tests for any_above method."""

    def test_any_above_true(self) -> None:
        """Should return True if any emotion exceeds threshold."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.8)
        assert state.any_above(0.7) is True

    def test_any_above_false(self) -> None:
        """Should return False if no emotion exceeds threshold."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.5)
        assert state.any_above(0.7) is False

    def test_any_above_with_category(self) -> None:
        """Should only check emotions in specified category."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.8)  # Fear
        assert state.any_above(0.7, category=EmotionCategory.FEAR) is True
        assert state.any_above(0.7, category=EmotionCategory.JOY) is False


class TestValenceAndArousal:
    """Tests for valence and arousal calculations."""

    def test_positive_valence(self) -> None:
        """High positive emotions should give positive valence."""
        state = EmotionalState()
        state.change_emotion("hopeful", 0.9)
        assert state.get_valence() > 0

    def test_negative_valence(self) -> None:
        """High negative emotions should give negative valence."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        assert state.get_valence() < 0

    def test_high_arousal(self) -> None:
        """High arousal emotions should give high arousal."""
        state = EmotionalState()
        state.change_emotion("angry", 0.9)
        assert state.get_arousal() > 0.5

    def test_neutral_state_valence(self) -> None:
        """All-zero state should have zero valence."""
        state = EmotionalState()
        assert state.get_valence() == 0.0


class TestCopy:
    """Tests for copy method."""

    def test_copy_creates_independent_state(self) -> None:
        """Copy should be independent of original."""
        state1 = EmotionalState()
        state1.change_emotion("anxious", 0.5)
        state2 = state1.copy()
        state2.change_emotion("anxious", 0.9)
        assert state1.get_emotion("anxious") == 0.5
        assert state2.get_emotion("anxious") == 0.9


class TestDunderMethods:
    """Tests for dunder methods."""

    def test_len(self) -> None:
        """len() should return number of tracked emotions."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        assert len(state) == 2

    def test_contains(self) -> None:
        """in operator should check if emotion is tracked."""
        state = EmotionalState(emotions=["anxious"])
        assert "anxious" in state
        assert "hopeful" not in state

    def test_iter(self) -> None:
        """Should be iterable over emotion names."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        emotions = list(state)
        assert "anxious" in emotions
        assert "hopeful" in emotions

    def test_eq(self) -> None:
        """Equality should compare emotion values."""
        state1 = EmotionalState(emotions=["anxious"])
        state2 = EmotionalState(emotions=["anxious"])
        state1.change_emotion("anxious", 0.5)
        state2.change_emotion("anxious", 0.5)
        assert state1 == state2

    def test_repr(self) -> None:
        """repr should show top emotions."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.8)
        repr_str = repr(state)
        assert "EmotionalState" in repr_str
        assert "anxious" in repr_str

    def test_repr_neutral(self) -> None:
        """repr should show neutral for all-zero state."""
        state = EmotionalState()
        assert "neutral" in repr(state)
