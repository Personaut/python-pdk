"""Markov chain transitions for emotional state.

This module provides the MarkovTransitionMatrix class for probabilistic
transitions between emotional states, influenced by personality traits.

Example:
    >>> from personaut.states.markov import MarkovTransitionMatrix
    >>> from personaut.emotions import EmotionalState
    >>>
    >>> matrix = MarkovTransitionMatrix()
    >>> current = EmotionalState()
    >>> current.change_emotion("anxious", 0.8)
    >>> next_state = matrix.next_state(current)
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from personaut.emotions.categories import EmotionCategory, get_category
from personaut.emotions.emotion import ALL_EMOTIONS
from personaut.traits.coefficients import get_coefficient


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.types.common import TraitDict


# Default transition probabilities between emotion categories
# Higher values = more likely to transition
DEFAULT_CATEGORY_TRANSITIONS: dict[EmotionCategory, dict[EmotionCategory, float]] = {
    EmotionCategory.ANGER: {
        EmotionCategory.ANGER: 0.4,
        EmotionCategory.SAD: 0.2,
        EmotionCategory.FEAR: 0.15,
        EmotionCategory.JOY: 0.05,
        EmotionCategory.POWERFUL: 0.1,
        EmotionCategory.PEACEFUL: 0.1,
    },
    EmotionCategory.SAD: {
        EmotionCategory.ANGER: 0.15,
        EmotionCategory.SAD: 0.4,
        EmotionCategory.FEAR: 0.2,
        EmotionCategory.JOY: 0.05,
        EmotionCategory.POWERFUL: 0.05,
        EmotionCategory.PEACEFUL: 0.15,
    },
    EmotionCategory.FEAR: {
        EmotionCategory.ANGER: 0.1,
        EmotionCategory.SAD: 0.2,
        EmotionCategory.FEAR: 0.4,
        EmotionCategory.JOY: 0.05,
        EmotionCategory.POWERFUL: 0.1,
        EmotionCategory.PEACEFUL: 0.15,
    },
    EmotionCategory.JOY: {
        EmotionCategory.ANGER: 0.05,
        EmotionCategory.SAD: 0.05,
        EmotionCategory.FEAR: 0.05,
        EmotionCategory.JOY: 0.5,
        EmotionCategory.POWERFUL: 0.2,
        EmotionCategory.PEACEFUL: 0.15,
    },
    EmotionCategory.POWERFUL: {
        EmotionCategory.ANGER: 0.1,
        EmotionCategory.SAD: 0.05,
        EmotionCategory.FEAR: 0.05,
        EmotionCategory.JOY: 0.25,
        EmotionCategory.POWERFUL: 0.4,
        EmotionCategory.PEACEFUL: 0.15,
    },
    EmotionCategory.PEACEFUL: {
        EmotionCategory.ANGER: 0.05,
        EmotionCategory.SAD: 0.1,
        EmotionCategory.FEAR: 0.05,
        EmotionCategory.JOY: 0.2,
        EmotionCategory.POWERFUL: 0.15,
        EmotionCategory.PEACEFUL: 0.45,
    },
}


class MarkovTransitionMatrix:
    """Manages probabilistic transitions between emotional states.

    The transition matrix defines probabilities of moving from one
    emotional category to another. These probabilities can be modified
    by personality traits to create individual-specific transition patterns.

    Attributes:
        transitions: Category-to-category transition probabilities.
        volatility: How much emotions can change per transition (0-1).

    Example:
        >>> matrix = MarkovTransitionMatrix(volatility=0.3)
        >>> current = EmotionalState()
        >>> current.change_emotion("anxious", 0.8)
        >>> next_state = matrix.next_state(current, {"emotional_stability": 0.9})
    """

    __slots__ = ("_transitions", "_volatility")

    def __init__(
        self,
        transitions: dict[EmotionCategory, dict[EmotionCategory, float]] | None = None,
        volatility: float = 0.2,
    ) -> None:
        """Initialize a MarkovTransitionMatrix.

        Args:
            transitions: Custom transition probabilities. If None, uses defaults.
            volatility: How much emotions change per transition (0-1).
                Higher volatility = larger emotional swings.

        Raises:
            ValueError: If volatility is not between 0 and 1.

        Example:
            >>> matrix = MarkovTransitionMatrix(volatility=0.5)
        """
        if not 0.0 <= volatility <= 1.0:
            msg = f"volatility must be between 0 and 1, got {volatility}"
            raise ValueError(msg)

        self._transitions = transitions or dict(DEFAULT_CATEGORY_TRANSITIONS)
        self._volatility = volatility

    @property
    def volatility(self) -> float:
        """Get the volatility factor."""
        return self._volatility

    def get_transition_probability(
        self,
        from_category: EmotionCategory,
        to_category: EmotionCategory,
    ) -> float:
        """Get the base transition probability between categories.

        Args:
            from_category: The source emotional category.
            to_category: The target emotional category.

        Returns:
            The probability of transitioning (0.0 to 1.0).

        Example:
            >>> matrix = MarkovTransitionMatrix()
            >>> prob = matrix.get_transition_probability(
            ...     EmotionCategory.FEAR, EmotionCategory.JOY
            ... )
            >>> prob
            0.05
        """
        from_probs = self._transitions.get(from_category, {})
        return from_probs.get(to_category, 0.0)

    def apply_trait_modifiers(
        self,
        base_probability: float,
        target_emotion: str,
        traits: TraitDict,
    ) -> float:
        """Apply trait-based modifiers to a transition probability.

        Args:
            base_probability: The base transition probability.
            target_emotion: The emotion being transitioned to.
            traits: Dictionary of trait names to their values.

        Returns:
            Modified probability, clamped to [0.0, 1.0].

        Example:
            >>> matrix = MarkovTransitionMatrix()
            >>> prob = matrix.apply_trait_modifiers(
            ...     0.5, "anxious", {"emotional_stability": 0.9}
            ... )
            >>> prob < 0.5  # High stability reduces anxiety probability
            True
        """
        modifier = 0.0

        for trait, value in traits.items():
            coeff = get_coefficient(trait, target_emotion)
            # Normalize trait value around 0.5
            normalized = value - 0.5
            modifier += coeff * normalized

        # Apply modifier to probability
        modified = base_probability * (1 + modifier)

        # Clamp to valid range
        return max(0.0, min(1.0, modified))

    def next_state(
        self,
        current: EmotionalState,
        traits: TraitDict | None = None,
    ) -> EmotionalState:
        """Calculate the next emotional state based on transitions.

        Args:
            current: The current emotional state.
            traits: Optional personality traits to influence transitions.

        Returns:
            A new EmotionalState representing the next state.

        Example:
            >>> matrix = MarkovTransitionMatrix()
            >>> current = EmotionalState()
            >>> current.change_emotion("anxious", 0.8)
            >>> next_s = matrix.next_state(current)
        """
        traits = traits or {}

        # Find dominant category
        dominant_emotion, _ = current.get_dominant()
        try:
            dominant_category = get_category(dominant_emotion)
        except (KeyError, ValueError):
            # Default to peaceful if can't determine
            dominant_category = EmotionCategory.PEACEFUL

        # Get transition probabilities for this category
        category_probs = self._transitions.get(
            dominant_category,
            self._transitions[EmotionCategory.PEACEFUL],
        )

        # Choose next category based on probabilities
        categories = list(category_probs.keys())
        weights = list(category_probs.values())

        # Normalize weights
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]

        next_category = random.choices(categories, weights=weights, k=1)[0]

        # Create next state based on current with modifications
        next_state = current.copy()

        # Apply changes based on volatility and trait modifiers
        for emotion in ALL_EMOTIONS:
            try:
                emotion_category = get_category(emotion)
            except (KeyError, ValueError):
                continue

            current_value = current.get_emotion(emotion) if emotion in current else 0.0

            # Calculate target value based on whether this emotion's category matches
            if emotion_category == next_category:
                # Increase emotions in target category
                target = min(1.0, current_value + self._volatility * 0.5)
            else:
                # Decrease emotions in other categories
                target = max(0.0, current_value - self._volatility * 0.25)

            # Apply trait modifiers
            if traits:
                target = self.apply_trait_modifiers(target, emotion, traits)

            # Move toward target based on volatility
            delta = (target - current_value) * self._volatility
            new_value = max(0.0, min(1.0, current_value + delta))

            if emotion in next_state:
                next_state.change_emotion(emotion, new_value)

        return next_state

    def simulate_trajectory(
        self,
        initial: EmotionalState,
        steps: int,
        traits: TraitDict | None = None,
    ) -> list[EmotionalState]:
        """Simulate a trajectory of emotional states.

        Args:
            initial: The starting emotional state.
            steps: Number of transition steps to simulate.
            traits: Optional personality traits.

        Returns:
            List of states including the initial state.

        Example:
            >>> matrix = MarkovTransitionMatrix()
            >>> initial = EmotionalState()
            >>> trajectory = matrix.simulate_trajectory(initial, steps=5)
            >>> len(trajectory)
            6
        """
        trajectory = [initial.copy()]
        current = initial

        for _ in range(steps):
            current = self.next_state(current, traits)
            trajectory.append(current)

        return trajectory

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"MarkovTransitionMatrix(volatility={self._volatility})"


__all__ = [
    "DEFAULT_CATEGORY_TRANSITIONS",
    "MarkovTransitionMatrix",
]
