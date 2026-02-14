"""Tests for StateCalculator class."""

from __future__ import annotations

import pytest

from personaut.emotions.state import EmotionalState
from personaut.states.calculator import StateCalculator
from personaut.states.mode import StateMode


class TestStateCalculatorCreation:
    """Tests for StateCalculator initialization."""

    def test_default_creation(self) -> None:
        """Default creation should use AVERAGE mode."""
        calc = StateCalculator()
        assert calc.mode == StateMode.AVERAGE, calc.mode
        assert calc.history_size == 10
        assert len(calc) == 0

    def test_creation_with_mode(self) -> None:
        """Should accept different modes."""
        calc = StateCalculator(mode=StateMode.MAXIMUM)
        assert calc.mode == StateMode.MAXIMUM

    def test_creation_with_history_size(self) -> None:
        """Should accept custom history size."""
        calc = StateCalculator(history_size=5)
        assert calc.history_size == 5

    def test_creation_with_custom_function(self) -> None:
        """CUSTOM mode should require a function."""

        def custom_fn(history: list[EmotionalState]) -> EmotionalState:
            return history[-1].copy()

        calc = StateCalculator(mode=StateMode.CUSTOM, custom_function=custom_fn)
        assert calc.mode == StateMode.CUSTOM

    def test_custom_mode_without_function_raises(self) -> None:
        """CUSTOM mode without function should raise ValueError."""
        with pytest.raises(ValueError, match="custom_function is required"):
            StateCalculator(mode=StateMode.CUSTOM)

    def test_invalid_history_size_raises(self) -> None:
        """History size < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="history_size must be at least 1"):
            StateCalculator(history_size=0)

    def test_invalid_decay_factor_raises(self) -> None:
        """Decay factor outside [0,1] should raise ValueError."""
        with pytest.raises(ValueError, match="decay_factor must be between"):
            StateCalculator(decay_factor=1.5)


class TestAddState:
    """Tests for add_state method."""

    def test_add_single_state(self) -> None:
        """Should add a state to history."""
        calc = StateCalculator()
        state = EmotionalState()
        state.change_emotion("anxious", 0.7)
        calc.add_state(state)
        assert len(calc) == 1

    def test_add_multiple_states(self) -> None:
        """Should maintain multiple states."""
        calc = StateCalculator(history_size=5)
        for i in range(3):
            state = EmotionalState()
            state.change_emotion("anxious", i * 0.3)
            calc.add_state(state)
        assert len(calc) == 3

    def test_history_size_limit(self) -> None:
        """Should trim to history_size when exceeded."""
        calc = StateCalculator(history_size=3)
        for _i in range(5):
            calc.add_state(EmotionalState())
        assert len(calc) == 3

    def test_adds_copy_not_reference(self) -> None:
        """Should add a copy of the state."""
        calc = StateCalculator()
        state = EmotionalState()
        state.change_emotion("anxious", 0.5)
        calc.add_state(state)

        # Modify original
        state.change_emotion("anxious", 0.9)

        # History should be unchanged
        history = calc.get_history()
        assert history[0].get_emotion("anxious") == 0.5


class TestClearHistory:
    """Tests for clear_history method."""

    def test_clear_removes_all(self) -> None:
        """Should remove all states from history."""
        calc = StateCalculator()
        calc.add_state(EmotionalState())
        calc.add_state(EmotionalState())
        calc.clear_history()
        assert len(calc) == 0


class TestGetHistory:
    """Tests for get_history method."""

    def test_returns_copy(self) -> None:
        """Should return a copy of history."""
        calc = StateCalculator()
        state = EmotionalState()
        state.change_emotion("anxious", 0.5)
        calc.add_state(state)

        history = calc.get_history()
        history[0].change_emotion("anxious", 0.9)

        # Internal history should be unchanged
        internal = calc.get_history()
        assert internal[0].get_emotion("anxious") == 0.5


class TestCalculateAverage:
    """Tests for AVERAGE calculation mode."""

    def test_average_single_state(self) -> None:
        """Single state should return that state's values."""
        calc = StateCalculator(mode=StateMode.AVERAGE)
        state = EmotionalState()
        state.change_emotion("anxious", 0.8)
        calc.add_state(state)

        result = calc.get_calculated_state()
        assert result.get_emotion("anxious") == 0.8

    def test_average_multiple_states(self) -> None:
        """Multiple states should average values."""
        calc = StateCalculator(mode=StateMode.AVERAGE)

        state1 = EmotionalState()
        state1.change_emotion("anxious", 0.8)
        calc.add_state(state1)

        state2 = EmotionalState()
        state2.change_emotion("anxious", 0.4)
        calc.add_state(state2)

        result = calc.get_calculated_state()
        assert abs(result.get_emotion("anxious") - 0.6) < 0.001


class TestCalculateMaximum:
    """Tests for MAXIMUM calculation mode."""

    def test_maximum_returns_max(self) -> None:
        """Should return maximum value for each emotion."""
        calc = StateCalculator(mode=StateMode.MAXIMUM)

        state1 = EmotionalState()
        state1.change_emotion("anxious", 0.3)
        calc.add_state(state1)

        state2 = EmotionalState()
        state2.change_emotion("anxious", 0.9)
        calc.add_state(state2)

        state3 = EmotionalState()
        state3.change_emotion("anxious", 0.5)
        calc.add_state(state3)

        result = calc.get_calculated_state()
        assert result.get_emotion("anxious") == 0.9


class TestCalculateMinimum:
    """Tests for MINIMUM calculation mode."""

    def test_minimum_returns_min(self) -> None:
        """Should return minimum value for each emotion."""
        calc = StateCalculator(mode=StateMode.MINIMUM)

        state1 = EmotionalState()
        state1.change_emotion("anxious", 0.3)
        calc.add_state(state1)

        state2 = EmotionalState()
        state2.change_emotion("anxious", 0.9)
        calc.add_state(state2)

        state3 = EmotionalState()
        state3.change_emotion("anxious", 0.5)
        calc.add_state(state3)

        result = calc.get_calculated_state()
        assert result.get_emotion("anxious") == 0.3


class TestCalculateRecent:
    """Tests for RECENT calculation mode."""

    def test_recent_weights_newer_more(self) -> None:
        """More recent states should have higher weight."""
        calc = StateCalculator(mode=StateMode.RECENT, decay_factor=0.5)

        # Add old state with low value
        state1 = EmotionalState()
        state1.change_emotion("anxious", 0.0)
        calc.add_state(state1)

        # Add recent state with high value
        state2 = EmotionalState()
        state2.change_emotion("anxious", 1.0)
        calc.add_state(state2)

        result = calc.get_calculated_state()
        # Result should be closer to 1.0 than 0.0
        assert result.get_emotion("anxious") > 0.5


class TestCalculateCustom:
    """Tests for CUSTOM calculation mode."""

    def test_custom_function_called(self) -> None:
        """Custom function should be called."""

        def always_zero(_history: list[EmotionalState]) -> EmotionalState:
            return EmotionalState()

        calc = StateCalculator(mode=StateMode.CUSTOM, custom_function=always_zero)
        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        calc.add_state(state)

        result = calc.get_calculated_state()
        assert result.get_emotion("anxious") == 0.0

    def test_custom_receives_history(self) -> None:
        """Custom function should receive the history."""
        received_history: list[EmotionalState] = []

        def capture_history(history: list[EmotionalState]) -> EmotionalState:
            received_history.extend(history)
            return history[-1]

        calc = StateCalculator(mode=StateMode.CUSTOM, custom_function=capture_history)
        calc.add_state(EmotionalState())
        calc.add_state(EmotionalState())
        calc.get_calculated_state()

        assert len(received_history) == 2


class TestEmptyHistory:
    """Tests for behavior with empty history."""

    def test_empty_history_returns_neutral(self) -> None:
        """Empty history should return neutral state."""
        calc = StateCalculator()
        result = calc.get_calculated_state()
        assert result.get_emotion("anxious") == 0.0

    def test_calculate_empty_raises(self) -> None:
        """calculate() with empty list should raise."""
        calc = StateCalculator()
        with pytest.raises(ValueError, match="Cannot calculate from empty"):
            calc.calculate([])


class TestDunderMethods:
    """Tests for dunder methods."""

    def test_len(self) -> None:
        """len() should return history size."""
        calc = StateCalculator()
        assert len(calc) == 0
        calc.add_state(EmotionalState())
        assert len(calc) == 1

    def test_repr(self) -> None:
        """repr should show mode and history info."""
        calc = StateCalculator(mode=StateMode.MAXIMUM, history_size=5)
        calc.add_state(EmotionalState())
        repr_str = repr(calc)
        assert "StateCalculator" in repr_str
        assert "maximum" in repr_str
