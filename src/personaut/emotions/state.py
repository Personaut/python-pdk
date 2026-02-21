"""EmotionalState class for Personaut PDK.

This module provides the EmotionalState class, which represents the
current emotional condition of an individual with values for each
emotion ranging from 0.0 to 1.0.

Example:
    >>> from personaut.emotions.state import EmotionalState
    >>> state = EmotionalState()
    >>> state.change_emotion("anxious", 0.7)
    >>> state.change_emotion("hopeful", 0.4)
    >>> dominant = state.get_dominant()
    >>> print(f"Dominant emotion: {dominant[0]} at {dominant[1]}")
    Dominant emotion: anxious at 0.7
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from personaut.emotions.categories import CATEGORY_EMOTIONS, EmotionCategory, get_category
from personaut.emotions.emotion import ALL_EMOTIONS, is_valid_emotion
from personaut.types.exceptions import EmotionNotFoundError, EmotionValueError


if TYPE_CHECKING:
    from collections.abc import Iterator

    from personaut.types.common import EmotionDict


class EmotionalState:
    """Represents the emotional state of an individual.

    EmotionalState tracks the intensity of various emotions, each ranging
    from 0.0 (not present) to 1.0 (maximum intensity). It provides methods
    for querying, modifying, and analyzing emotional states.

    Attributes:
        emotions: Dictionary mapping emotion names to their current values.

    Example:
        >>> state = EmotionalState(baseline=0.2)
        >>> state.change_emotion("anxious", 0.8)
        >>> state.get_emotion("anxious")
        0.8
        >>> state.get_dominant()
        ('anxious', 0.8)
    """

    # Antagonistic emotion pairs: when one rises, the other is dampened.
    # Based on affective circumplex (valence × arousal opposition).
    _ANTAGONISTIC_PAIRS: list[tuple[str, str]] = [
        # Joy ↔ Sad
        ("cheerful", "depressed"),
        ("hopeful", "helpless"),
        ("excited", "apathetic"),
        ("energetic", "bored"),
        # Powerful ↔ Fear
        ("proud", "ashamed"),
        ("respected", "rejected"),
        ("important", "insecure"),
        ("satisfied", "guilty"),
        # Peaceful ↔ Anger
        ("content", "angry"),
        ("loving", "hateful"),
        ("trusting", "hostile"),
        ("nurturing", "critical"),
        # Within-category oppositions
        ("creative", "confused"),
        ("faithful", "selfish"),
    ]

    __slots__ = ("_emotions", "_last_update_turn", "_mood_baseline")

    def __init__(
        self,
        emotions: list[str] | None = None,
        baseline: float = 0.0,
    ) -> None:
        """Initialize an EmotionalState.

        Args:
            emotions: Optional list of emotions to track. If None, tracks
                all 36 standard emotions.
            baseline: Initial value for all emotions (0.0 to 1.0).

        Raises:
            EmotionValueError: If baseline is outside [0.0, 1.0].
            EmotionNotFoundError: If any emotion in the list is unknown.

        Example:
            >>> state = EmotionalState()  # All 36 emotions at 0.0
            >>> state = EmotionalState(baseline=0.5)  # All at 0.5
            >>> state = EmotionalState(["anxious", "hopeful"])  # Only these two
        """
        if not 0.0 <= baseline <= 1.0:
            raise EmotionValueError("baseline", baseline)

        emotion_list = emotions if emotions is not None else ALL_EMOTIONS

        # Validate all emotions
        for emotion in emotion_list:
            if not is_valid_emotion(emotion):
                raise EmotionNotFoundError(emotion, available=ALL_EMOTIONS[:5])

        self._emotions: EmotionDict = dict.fromkeys(emotion_list, baseline)
        # Mood baseline: the emotional 'resting point' that emotions decay toward.
        # This shifts slowly over multiple interactions — distinct from transient spikes.
        self._mood_baseline: EmotionDict = dict.fromkeys(emotion_list, baseline)
        # Turn counter for decay calculations
        self._last_update_turn: int = 0

    def change_emotion(self, emotion: str, value: float) -> None:
        """Change the value of a single emotion.

        Args:
            emotion: Name of the emotion to change.
            value: New value for the emotion (0.0 to 1.0).

        Raises:
            EmotionNotFoundError: If the emotion is not tracked.
            EmotionValueError: If value is outside [0.0, 1.0].

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.7)
            >>> state.get_emotion("anxious")
            0.7
        """
        if emotion not in self._emotions:
            raise EmotionNotFoundError(emotion, available=list(self._emotions.keys()))

        if not 0.0 <= value <= 1.0:
            raise EmotionValueError(emotion, value)

        self._emotions[emotion] = value

    def change_state(
        self,
        emotions: EmotionDict,
        fill: float | None = None,
    ) -> None:
        """Change multiple emotions at once.

        Args:
            emotions: Dictionary mapping emotion names to new values.
            fill: If provided, set all unspecified emotions to this value.
                If None, unspecified emotions are left unchanged.

        Raises:
            EmotionNotFoundError: If any emotion is not tracked.
            EmotionValueError: If any value is outside [0.0, 1.0].

        Example:
            >>> state = EmotionalState()
            >>> state.change_state({"anxious": 0.7, "hopeful": 0.3})
            >>> # Set only specified emotions, leave others at 0.0

            >>> state.change_state({"anxious": 0.7}, fill=0.1)
            >>> # anxious=0.7, all others=0.1
        """
        # Validate fill value
        if fill is not None and not 0.0 <= fill <= 1.0:
            raise EmotionValueError("fill", fill)

        # Validate all emotions and values first
        for emotion, value in emotions.items():
            if emotion not in self._emotions:
                raise EmotionNotFoundError(emotion, available=list(self._emotions.keys()))
            if not 0.0 <= value <= 1.0:
                raise EmotionValueError(emotion, value)

        # Apply fill if specified
        if fill is not None:
            for emotion in self._emotions:
                self._emotions[emotion] = fill

        # Apply specified emotions
        for emotion, value in emotions.items():
            self._emotions[emotion] = value

    def reset(self, value: float = 0.0) -> None:
        """Reset all emotions to a specified value.

        Args:
            value: Value to set all emotions to (0.0 to 1.0).

        Raises:
            EmotionValueError: If value is outside [0.0, 1.0].

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.9)
            >>> state.reset()  # All emotions now 0.0
            >>> state.get_emotion("anxious")
            0.0
        """
        if not 0.0 <= value <= 1.0:
            raise EmotionValueError("reset", value)

        for emotion in self._emotions:
            self._emotions[emotion] = value

    def to_dict(self) -> EmotionDict:
        """Convert emotional state to a dictionary.

        Returns:
            A copy of the internal emotion dictionary.

        Example:
            >>> state = EmotionalState(["anxious", "hopeful"])
            >>> state.change_emotion("anxious", 0.5)
            >>> state.to_dict()
            {'anxious': 0.5, 'hopeful': 0.0}
        """
        return dict(self._emotions)

    def get_emotion(self, emotion: str) -> float:
        """Get the current value of an emotion.

        Args:
            emotion: Name of the emotion to query.

        Returns:
            Current value of the emotion (0.0 to 1.0).

        Raises:
            EmotionNotFoundError: If the emotion is not tracked.

        Example:
            >>> state = EmotionalState()
            >>> state.get_emotion("anxious")
            0.0
        """
        if emotion not in self._emotions:
            raise EmotionNotFoundError(emotion, available=list(self._emotions.keys()))
        return self._emotions[emotion]

    def get_category_emotions(self, category: EmotionCategory) -> EmotionDict:
        """Get all emotions in a category with their values.

        Args:
            category: The emotion category to query.

        Returns:
            Dictionary of emotion names to values for emotions in
            this category that are being tracked.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.8)
            >>> fear_emotions = state.get_category_emotions(EmotionCategory.FEAR)
            >>> fear_emotions["anxious"]
            0.8
        """
        category_emotions = CATEGORY_EMOTIONS.get(category, [])
        return {emotion: self._emotions[emotion] for emotion in category_emotions if emotion in self._emotions}

    def get_category_average(self, category: EmotionCategory) -> float:
        """Get the average intensity of emotions in a category.

        Args:
            category: The emotion category to query.

        Returns:
            Average value of emotions in this category, or 0.0 if
            no emotions from this category are tracked.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.8)
            >>> state.change_emotion("helpless", 0.4)
            >>> state.get_category_average(EmotionCategory.FEAR)
            0.2  # (0.8 + 0.4 + 0 + 0 + 0 + 0) / 6
        """
        category_values = self.get_category_emotions(category)
        if not category_values:
            return 0.0
        return sum(category_values.values()) / len(category_values)

    def get_dominant(self) -> tuple[str, float]:
        """Get the emotion with the highest value.

        Returns:
            Tuple of (emotion_name, value) for the dominant emotion.
            If multiple emotions share the maximum value, returns
            the first one alphabetically.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.9)
            >>> state.change_emotion("hopeful", 0.7)
            >>> state.get_dominant()
            ('anxious', 0.9)
        """
        if not self._emotions:
            return ("", 0.0)

        # Find max value
        max_value = max(self._emotions.values())

        # Get all emotions with max value, return first alphabetically
        max_emotions = [e for e, v in self._emotions.items() if v == max_value]
        max_emotions.sort()
        return (max_emotions[0], max_value)

    def get_top(self, n: int = 5) -> list[tuple[str, float]]:
        """Get the top N emotions by intensity.

        Args:
            n: Number of emotions to return.

        Returns:
            List of (emotion_name, value) tuples, sorted by value
            descending, then alphabetically for ties.

        Example:
            >>> state = EmotionalState()
            >>> state.change_state({"anxious": 0.9, "hopeful": 0.7, "depressed": 0.5})
            >>> state.get_top(2)
            [('anxious', 0.9), ('hopeful', 0.7)]
        """
        sorted_emotions = sorted(
            self._emotions.items(),
            key=lambda x: (-x[1], x[0]),  # Sort by value desc, then name asc
        )
        return sorted_emotions[:n]

    def any_above(
        self,
        threshold: float,
        category: EmotionCategory | None = None,
    ) -> bool:
        """Check if any emotion exceeds a threshold.

        Args:
            threshold: Value to compare against.
            category: If provided, only check emotions in this category.

        Returns:
            True if any (optionally category-filtered) emotion
            exceeds the threshold.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.8)
            >>> state.any_above(0.7)
            True
            >>> state.any_above(0.7, category=EmotionCategory.JOY)
            False
        """
        emotions = self.get_category_emotions(category) if category is not None else self._emotions

        return any(value > threshold for value in emotions.values())

    def get_valence(self) -> float:
        """Calculate overall emotional valence (positive/negative).

        Returns:
            A value from -1.0 (very negative) to 1.0 (very positive),
            based on the weighted average of category valences.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("hopeful", 0.9)  # Positive
            >>> state.get_valence()  # Positive valence
        """
        total_weighted_valence = 0.0
        total_intensity = 0.0

        for emotion, value in self._emotions.items():
            if value > 0:
                try:
                    category = get_category(emotion)
                    total_weighted_valence += category.valence * value
                    total_intensity += value
                except KeyError:
                    pass

        if total_intensity == 0:
            return 0.0

        return total_weighted_valence / total_intensity

    def get_arousal(self) -> float:
        """Calculate overall emotional arousal (activation level).

        Returns:
            A value from 0.0 (calm) to 1.0 (highly activated),
            based on the weighted average of category arousal levels.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("angry", 0.9)  # High arousal
            >>> state.get_arousal()  # High arousal level
        """
        total_weighted_arousal = 0.0
        total_intensity = 0.0

        for emotion, value in self._emotions.items():
            if value > 0:
                try:
                    category = get_category(emotion)
                    total_weighted_arousal += category.arousal * value
                    total_intensity += value
                except KeyError:
                    pass

        if total_intensity == 0:
            return 0.0

        return total_weighted_arousal / total_intensity

    # ------------------------------------------------------------------
    # Emotional dynamics: decay, delta, antagonism, trait modulation
    # ------------------------------------------------------------------

    def decay(self, turns_elapsed: int = 1, rate: float = 0.15) -> None:
        """Naturally decay emotions toward their mood baseline.

        Real emotions don't persist at peak intensity — they fade
        toward a resting state. Strong emotions decay faster (nonlinear).
        The mood baseline itself shifts very slowly toward neutral.

        Args:
            turns_elapsed: Number of conversational turns since last decay.
            rate: Decay rate per turn (0.0-1.0). Default 0.15 means
                ~15% of the gap toward baseline closes per turn.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.9)
            >>> state.decay(turns_elapsed=3)
            >>> state.get_emotion("anxious")  # Decayed toward 0.0
        """
        if turns_elapsed <= 0:
            return

        # Effective decay: 1 - (1 - rate)^turns  (compound decay)
        effective = 1.0 - math.pow(1.0 - min(rate, 0.99), turns_elapsed)

        for emotion in self._emotions:
            current = self._emotions[emotion]
            baseline = self._mood_baseline.get(emotion, 0.0)
            if abs(current - baseline) < 0.01:
                self._emotions[emotion] = baseline
                continue
            # Decay toward baseline
            self._emotions[emotion] = current + (baseline - current) * effective
            # Clamp
            self._emotions[emotion] = max(0.0, min(1.0, self._emotions[emotion]))

        # Mood baseline itself drifts slowly toward neutral (0.1-0.2 range)
        mood_drift = 1.0 - math.pow(0.97, turns_elapsed)  # ~3% per turn
        resting_neutral = 0.1  # Slight positive resting state (humans default mildly content)
        for emotion in self._mood_baseline:
            mb = self._mood_baseline[emotion]
            if abs(mb - resting_neutral) > 0.01:
                self._mood_baseline[emotion] = mb + (resting_neutral - mb) * mood_drift

        self._last_update_turn += turns_elapsed

    def apply_delta(
        self,
        deltas: dict[str, float],
        *,
        intensity_scale: float = 1.0,
    ) -> None:
        """Shift emotions by a delta amount rather than setting absolutely.

        This is more realistic than change_emotion() because it adjusts
        relative to current state — a 'nudge' rather than an overwrite.
        Values are clamped to [0.0, 1.0] after application.

        Args:
            deltas: Dict mapping emotion names to delta values.
                Positive increases, negative decreases.
            intensity_scale: Multiplier for all deltas (e.g., 0.5
                for dampened reactivity, 1.5 for heightened).

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.4)
            >>> state.apply_delta({"anxious": 0.3, "hopeful": -0.1})
            >>> state.get_emotion("anxious")  # 0.4 + 0.3 = 0.7
            0.7
        """
        for emotion, delta in deltas.items():
            if emotion not in self._emotions:
                continue  # Silently skip unknown emotions
            current = self._emotions[emotion]
            new_value = current + (delta * intensity_scale)
            self._emotions[emotion] = max(0.0, min(1.0, new_value))

    def apply_trait_modulated_change(
        self,
        raw_updates: dict[str, float],
        trait_profile: dict[str, float] | Any | None = None,
    ) -> None:
        """Apply emotional changes modulated by personality traits.

        A person's traits affect HOW they respond emotionally:
        - High emotional_stability → smaller emotional shifts
        - High sensitivity → larger emotional shifts
        - High apprehension → amplified negative emotions
        - High tension → faster anger/anxiety escalation

        The raw_updates dict maps emotion names to target values
        from the LLM emotion analysis. This method applies them as
        deltas modulated by traits rather than absolute overwrites.

        Args:
            raw_updates: Dict of emotion names to raw target values.
            trait_profile: Dict of trait names to values (0.0-1.0),
                or a TraitProfile object (converted via to_dict()).
                If None, applies changes with no modulation.
        """
        if not trait_profile:
            # No traits — apply as simple deltas from current
            for emotion, target in raw_updates.items():
                if emotion in self._emotions:
                    self._emotions[emotion] = max(0.0, min(1.0, target))
            return

        # Normalize TraitProfile objects to plain dicts
        if hasattr(trait_profile, "to_dict"):
            trait_profile = trait_profile.to_dict()

        # Import coefficients lazily to avoid circular imports
        from personaut.traits.coefficients import get_coefficient

        # Calculate overall reactivity modifier from traits
        # emotional_stability DAMPENS reactivity, sensitivity AMPLIFIES it
        stability = trait_profile.get("emotional_stability", 0.5)
        sensitivity_val = trait_profile.get("sensitivity", 0.5)
        apprehension = trait_profile.get("apprehension", 0.5)
        tension = trait_profile.get("tension", 0.5)

        # Base reactivity: 1.0 at average traits
        # stability pulls it down, sensitivity + apprehension push it up
        base_reactivity = 1.0 + (sensitivity_val - 0.5) * 0.6 - (stability - 0.5) * 0.8
        base_reactivity = max(0.3, min(2.0, base_reactivity))  # Clamp

        for emotion, target in raw_updates.items():
            if emotion not in self._emotions:
                continue

            current = self._emotions[emotion]
            raw_delta = target - current

            # Per-emotion trait modulation via coefficients
            trait_modifier = 0.0
            for trait_name, trait_value in trait_profile.items():
                coeff = get_coefficient(trait_name, emotion)
                if coeff != 0.0:
                    # Trait deviation from average * coefficient
                    trait_modifier += (trait_value - 0.5) * coeff

            # Final reactivity for this emotion
            reactivity = base_reactivity + trait_modifier

            # Amplify negative emotions for high-apprehension individuals
            try:
                cat = get_category(emotion)
                if cat.is_negative and apprehension > 0.6:
                    reactivity *= 1.0 + (apprehension - 0.6) * 0.5
                # Amplify anger/anxiety for high-tension individuals
                if cat == EmotionCategory.ANGER and tension > 0.6:
                    reactivity *= 1.0 + (tension - 0.6) * 0.4
            except KeyError:
                pass

            reactivity = max(0.2, min(2.5, reactivity))

            # Apply modulated delta — positive deltas scaled up/down,
            # but don't invert the direction
            modulated_delta = raw_delta * reactivity
            new_value = current + modulated_delta
            self._emotions[emotion] = max(0.0, min(1.0, new_value))

    def apply_antagonism(self, strength: float = 0.3) -> None:
        """Suppress contradictory emotions (antagonistic pairs).

        When opposite emotions are both elevated, the stronger one
        suppresses the weaker. This models the psychological finding
        that people experience mixed emotions but true contradictions
        resolve toward the dominant pole.

        Args:
            strength: How aggressively to suppress (0.0-1.0).
                0.3 means the weaker emotion loses 30% of its value
                per application.

        Example:
            >>> state = EmotionalState()
            >>> state.change_state({"cheerful": 0.8, "depressed": 0.6})
            >>> state.apply_antagonism()
            >>> state.get_emotion("depressed")  # Suppressed by cheerful
        """
        for e1, e2 in self._ANTAGONISTIC_PAIRS:
            if e1 not in self._emotions or e2 not in self._emotions:
                continue
            v1 = self._emotions[e1]
            v2 = self._emotions[e2]
            if v1 > 0.1 and v2 > 0.1:
                # Stronger wins — weaker gets suppressed proportionally
                if v1 >= v2:
                    suppression = min(v2, strength * v1)
                    self._emotions[e2] = max(0.0, v2 - suppression)
                else:
                    suppression = min(v1, strength * v2)
                    self._emotions[e1] = max(0.0, v1 - suppression)

    def update_mood_baseline(self, learning_rate: float = 0.1) -> None:
        """Shift the mood baseline toward current emotional state.

        This models how repeated emotional experiences shift a person's
        baseline mood. If someone has been anxious for many turns, their
        resting anxiety level rises.

        Args:
            learning_rate: How fast the baseline adapts (0.0-1.0).
                0.1 means 10% of the gap between current and baseline
                is absorbed per call.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.8)
            >>> for _ in range(5):
            ...     state.update_mood_baseline()
            >>> state.get_mood_baseline("anxious")  # Has risen
        """
        for emotion in self._emotions:
            current = self._emotions[emotion]
            baseline = self._mood_baseline.get(emotion, 0.0)
            self._mood_baseline[emotion] = baseline + (current - baseline) * learning_rate

    def get_mood_baseline(self, emotion: str) -> float:
        """Get the mood baseline for an emotion.

        Args:
            emotion: Name of the emotion.

        Returns:
            The mood baseline value (resting point for this emotion).
        """
        return self._mood_baseline.get(emotion, 0.0)

    def get_emotional_volatility(self) -> float:
        """Calculate how far current emotions deviate from mood baseline.

        High volatility means the person is in an emotionally charged
        state far from their resting point. Low volatility means they're
        near their emotional equilibrium.

        Returns:
            Average deviation from baseline (0.0 = at rest, ~1.0 = extreme).
        """
        if not self._emotions:
            return 0.0
        deviations = [abs(self._emotions[e] - self._mood_baseline.get(e, 0.0)) for e in self._emotions]
        return sum(deviations) / len(deviations)

    def copy(self) -> EmotionalState:
        """Create a copy of this emotional state.

        Returns:
            A new EmotionalState with the same emotion values.

        Example:
            >>> state1 = EmotionalState()
            >>> state1.change_emotion("anxious", 0.5)
            >>> state2 = state1.copy()
            >>> state2.change_emotion("anxious", 0.9)
            >>> state1.get_emotion("anxious")  # Unchanged
            0.5
        """
        new_state = EmotionalState(emotions=list(self._emotions.keys()))
        new_state._emotions = dict(self._emotions)
        new_state._mood_baseline = dict(self._mood_baseline)
        new_state._last_update_turn = self._last_update_turn
        return new_state

    def __len__(self) -> int:
        """Return the number of tracked emotions."""
        return len(self._emotions)

    def __contains__(self, emotion: str) -> bool:
        """Check if an emotion is tracked."""
        return emotion in self._emotions

    def __iter__(self) -> Iterator[str]:
        """Iterate over tracked emotion names."""
        return iter(self._emotions)

    def __eq__(self, other: object) -> bool:
        """Check equality with another EmotionalState."""
        if not isinstance(other, EmotionalState):
            return NotImplemented
        return self._emotions == other._emotions

    def __repr__(self) -> str:
        """Return a string representation of the emotional state."""
        top_emotions = self.get_top(3)
        if not top_emotions or top_emotions[0][1] == 0:
            return "EmotionalState(neutral)"

        emotion_strs = [f"{e}={v:.2f}" for e, v in top_emotions if v > 0]
        return f"EmotionalState({', '.join(emotion_strs)})"


__all__ = [
    "EmotionalState",
]
