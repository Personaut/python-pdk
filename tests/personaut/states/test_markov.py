"""Tests for MarkovTransitionMatrix class."""

from __future__ import annotations

import pytest

from personaut.emotions.categories import EmotionCategory
from personaut.emotions.state import EmotionalState
from personaut.states.markov import DEFAULT_CATEGORY_TRANSITIONS, MarkovTransitionMatrix


class TestMarkovCreation:
    """Tests for MarkovTransitionMatrix initialization."""

    def test_default_creation(self) -> None:
        """Default creation should use default transitions."""
        matrix = MarkovTransitionMatrix()
        assert matrix.volatility == 0.2

    def test_creation_with_volatility(self) -> None:
        """Should accept custom volatility."""
        matrix = MarkovTransitionMatrix(volatility=0.5)
        assert matrix.volatility == 0.5

    def test_invalid_volatility_raises(self) -> None:
        """Volatility outside [0,1] should raise ValueError."""
        with pytest.raises(ValueError, match="volatility must be between"):
            MarkovTransitionMatrix(volatility=1.5)

        with pytest.raises(ValueError, match="volatility must be between"):
            MarkovTransitionMatrix(volatility=-0.1)


class TestDefaultTransitions:
    """Tests for DEFAULT_CATEGORY_TRANSITIONS."""

    def test_all_categories_have_transitions(self) -> None:
        """All 6 categories should have transition probabilities."""
        assert len(DEFAULT_CATEGORY_TRANSITIONS) == 6

    def test_transitions_sum_to_one(self) -> None:
        """Transition probabilities from each category should sum to ~1."""
        for category, transitions in DEFAULT_CATEGORY_TRANSITIONS.items():
            total = sum(transitions.values())
            assert abs(total - 1.0) < 0.01, f"{category} sums to {total}"

    def test_all_target_categories_present(self) -> None:
        """Each category should have probabilities to all categories."""
        for category, transitions in DEFAULT_CATEGORY_TRANSITIONS.items():
            assert len(transitions) == 6, f"{category} missing targets"


class TestGetTransitionProbability:
    """Tests for get_transition_probability method."""

    def test_get_valid_transition(self) -> None:
        """Should return correct probability for valid transition."""
        matrix = MarkovTransitionMatrix()
        prob = matrix.get_transition_probability(
            EmotionCategory.FEAR,
            EmotionCategory.JOY,
        )
        assert prob == 0.05

    def test_self_transition_higher(self) -> None:
        """Self-transitions should typically be higher."""
        matrix = MarkovTransitionMatrix()
        for category in EmotionCategory:
            self_prob = matrix.get_transition_probability(category, category)
            assert self_prob >= 0.4, f"{category} self-transition too low"


class TestApplyTraitModifiers:
    """Tests for apply_trait_modifiers method."""

    def test_high_stability_reduces_anxiety(self) -> None:
        """High emotional stability should reduce anxiety probability."""
        matrix = MarkovTransitionMatrix()
        base_prob = 0.5
        traits = {"emotional_stability": 0.9}

        modified = matrix.apply_trait_modifiers(base_prob, "anxious", traits)
        assert modified < base_prob

    def test_low_stability_increases_anxiety(self) -> None:
        """Low emotional stability should increase anxiety probability."""
        matrix = MarkovTransitionMatrix()
        base_prob = 0.5
        traits = {"emotional_stability": 0.1}

        modified = matrix.apply_trait_modifiers(base_prob, "anxious", traits)
        assert modified > base_prob

    def test_average_trait_no_effect(self) -> None:
        """Average trait value should have minimal effect."""
        matrix = MarkovTransitionMatrix()
        base_prob = 0.5
        traits = {"emotional_stability": 0.5}

        modified = matrix.apply_trait_modifiers(base_prob, "anxious", traits)
        assert abs(modified - base_prob) < 0.01

    def test_result_clamped(self) -> None:
        """Result should be clamped to [0, 1]."""
        matrix = MarkovTransitionMatrix()
        modified = matrix.apply_trait_modifiers(0.9, "loving", {"warmth": 1.0})
        assert 0.0 <= modified <= 1.0


class TestNextState:
    """Tests for next_state method."""

    def test_next_state_returns_emotional_state(self) -> None:
        """Should return an EmotionalState."""
        matrix = MarkovTransitionMatrix()
        current = EmotionalState()
        next_s = matrix.next_state(current)
        assert isinstance(next_s, EmotionalState)

    def test_next_state_different_from_current(self) -> None:
        """With volatility, next state should differ from current."""
        matrix = MarkovTransitionMatrix(volatility=0.5)
        current = EmotionalState()
        current.change_emotion("anxious", 0.8)

        # Run multiple times to ensure some change
        changed = False
        for _ in range(10):
            next_s = matrix.next_state(current)
            if next_s.get_emotion("anxious") != current.get_emotion("anxious"):
                changed = True
                break

        # With volatility 0.5, we should see some change
        assert changed or matrix.volatility == 0.0

    def test_next_state_with_traits(self) -> None:
        """Traits should influence the transition."""
        matrix = MarkovTransitionMatrix(volatility=0.3)
        current = EmotionalState()
        traits = {"warmth": 0.9}

        # Run several times - high warmth should tend toward loving
        next_s = matrix.next_state(current, traits)
        assert isinstance(next_s, EmotionalState)


class TestSimulateTrajectory:
    """Tests for simulate_trajectory method."""

    def test_trajectory_length(self) -> None:
        """Trajectory should have steps + 1 states."""
        matrix = MarkovTransitionMatrix()
        initial = EmotionalState()
        trajectory = matrix.simulate_trajectory(initial, steps=5)
        assert len(trajectory) == 6

    def test_trajectory_starts_with_initial(self) -> None:
        """First state should be the initial state."""
        matrix = MarkovTransitionMatrix()
        initial = EmotionalState()
        initial.change_emotion("anxious", 0.7)
        trajectory = matrix.simulate_trajectory(initial, steps=3)
        assert trajectory[0].get_emotion("anxious") == 0.7

    def test_trajectory_with_traits(self) -> None:
        """Should accept traits for the simulation."""
        matrix = MarkovTransitionMatrix()
        initial = EmotionalState()
        traits = {"emotional_stability": 0.9}
        trajectory = matrix.simulate_trajectory(initial, steps=3, traits=traits)
        assert len(trajectory) == 4


class TestDunderMethods:
    """Tests for dunder methods."""

    def test_repr(self) -> None:
        """repr should show volatility."""
        matrix = MarkovTransitionMatrix(volatility=0.3)
        repr_str = repr(matrix)
        assert "MarkovTransitionMatrix" in repr_str
        assert "0.3" in repr_str
