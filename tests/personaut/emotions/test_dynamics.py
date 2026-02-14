"""Tests for emotional dynamics: decay, trait modulation, antagonism, and mood baseline.

These features make the EmotionalState simulate realistic human emotional
behavior rather than acting as a static dictionary of values.
"""

from __future__ import annotations

from personaut.emotions.state import EmotionalState


# ──────────────────────────────────────────────────────────────
# Decay
# ──────────────────────────────────────────────────────────────


class TestDecay:
    """Emotions should naturally fade toward their mood baseline."""

    def test_decay_reduces_intensity(self):
        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        initial = state.get_emotion("anxious")
        state.decay(turns_elapsed=1)
        assert state.get_emotion("anxious") < initial

    def test_decay_multiple_turns(self):
        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.decay(turns_elapsed=1)
        after_one = state.get_emotion("anxious")
        state.change_emotion("anxious", 0.9)
        state.decay(turns_elapsed=5)
        after_five = state.get_emotion("anxious")
        # More turns = more decay
        assert after_five < after_one

    def test_decay_toward_baseline(self):
        state = EmotionalState()
        state.change_emotion("cheerful", 0.8)
        # Manually set mood baseline higher
        state._mood_baseline["cheerful"] = 0.5
        state.decay(turns_elapsed=3)
        # Should decay TOWARD 0.5, not toward 0.0
        assert state.get_emotion("cheerful") < 0.8
        assert state.get_emotion("cheerful") > 0.5

    def test_decay_zero_turns_is_noop(self):
        state = EmotionalState()
        state.change_emotion("angry", 0.7)
        state.decay(turns_elapsed=0)
        assert state.get_emotion("angry") == 0.7

    def test_decay_negative_turns_is_noop(self):
        state = EmotionalState()
        state.change_emotion("angry", 0.7)
        state.decay(turns_elapsed=-1)
        assert state.get_emotion("angry") == 0.7

    def test_decay_preserves_neutral_emotions(self):
        state = EmotionalState()
        # Emotion at 0.0 with baseline at 0.0 should stay 0.0
        assert state.get_emotion("angry") == 0.0
        state.decay(turns_elapsed=5)
        assert state.get_emotion("angry") == 0.0

    def test_decay_custom_rate(self):
        state1 = EmotionalState()
        state1.change_emotion("excited", 0.9)
        state1.decay(turns_elapsed=1, rate=0.1)
        slow_decay = 0.9 - state1.get_emotion("excited")

        state2 = EmotionalState()
        state2.change_emotion("excited", 0.9)
        state2.decay(turns_elapsed=1, rate=0.5)
        fast_decay = 0.9 - state2.get_emotion("excited")

        assert fast_decay > slow_decay


# ──────────────────────────────────────────────────────────────
# Apply Delta
# ──────────────────────────────────────────────────────────────


class TestApplyDelta:
    """Emotions should be nudged by deltas rather than overwritten."""

    def test_positive_delta(self):
        state = EmotionalState()
        state.change_emotion("anxious", 0.4)
        state.apply_delta({"anxious": 0.3})
        assert abs(state.get_emotion("anxious") - 0.7) < 0.001

    def test_negative_delta(self):
        state = EmotionalState()
        state.change_emotion("cheerful", 0.6)
        state.apply_delta({"cheerful": -0.2})
        assert abs(state.get_emotion("cheerful") - 0.4) < 0.001

    def test_clamped_to_max(self):
        state = EmotionalState()
        state.change_emotion("excited", 0.9)
        state.apply_delta({"excited": 0.5})
        assert state.get_emotion("excited") == 1.0

    def test_clamped_to_zero(self):
        state = EmotionalState()
        state.change_emotion("hopeful", 0.2)
        state.apply_delta({"hopeful": -0.5})
        assert state.get_emotion("hopeful") == 0.0

    def test_intensity_scale(self):
        state = EmotionalState()
        state.change_emotion("angry", 0.5)
        state.apply_delta({"angry": 0.2}, intensity_scale=0.5)
        # 0.5 + (0.2 * 0.5) = 0.6
        assert abs(state.get_emotion("angry") - 0.6) < 0.001

    def test_unknown_emotions_skipped(self):
        state = EmotionalState()
        state.apply_delta({"nonexistent_emotion": 0.5})  # No error

    def test_multiple_deltas(self):
        state = EmotionalState()
        state.change_emotion("anxious", 0.3)
        state.change_emotion("cheerful", 0.5)
        state.apply_delta({"anxious": 0.2, "cheerful": -0.1})
        assert abs(state.get_emotion("anxious") - 0.5) < 0.001
        assert abs(state.get_emotion("cheerful") - 0.4) < 0.001


# ──────────────────────────────────────────────────────────────
# Trait-Modulated Changes
# ──────────────────────────────────────────────────────────────


class TestTraitModulatedChange:
    """Personality traits should shape how strongly emotions shift."""

    def test_no_traits_applies_raw(self):
        state = EmotionalState()
        state.apply_trait_modulated_change(
            {"anxious": 0.7, "cheerful": 0.3},
            trait_profile=None,
        )
        assert abs(state.get_emotion("anxious") - 0.7) < 0.001
        assert abs(state.get_emotion("cheerful") - 0.3) < 0.001

    def test_high_stability_dampens_negative(self):
        """High emotional_stability should reduce negative emotional shifts."""
        stable = EmotionalState()
        reactive = EmotionalState()

        # Same starting point
        stable.change_emotion("anxious", 0.3)
        reactive.change_emotion("anxious", 0.3)

        # Apply the same update with different personality
        stable.apply_trait_modulated_change(
            {"anxious": 0.8},
            trait_profile={"emotional_stability": 0.9, "sensitivity": 0.5},
        )
        reactive.apply_trait_modulated_change(
            {"anxious": 0.8},
            trait_profile={"emotional_stability": 0.2, "sensitivity": 0.5},
        )

        # The emotionally stable person should have less anxiety increase
        assert stable.get_emotion("anxious") < reactive.get_emotion("anxious")

    def test_high_sensitivity_amplifies(self):
        """High sensitivity should amplify emotional shifts."""
        sensitive = EmotionalState()
        tough = EmotionalState()

        # Same starting point
        sensitive.change_emotion("hurt", 0.2)
        tough.change_emotion("hurt", 0.2)

        sensitive.apply_trait_modulated_change(
            {"hurt": 0.6},
            trait_profile={"sensitivity": 0.9, "emotional_stability": 0.5},
        )
        tough.apply_trait_modulated_change(
            {"hurt": 0.6},
            trait_profile={"sensitivity": 0.2, "emotional_stability": 0.5},
        )

        # Sensitive person should feel the hurt more
        assert sensitive.get_emotion("hurt") > tough.get_emotion("hurt")

    def test_trait_coefficients_affect_specific_emotions(self):
        """Trait-emotion coefficients should modulate specific emotions."""
        state = EmotionalState()
        # Warmth has coefficient 0.4 for "loving"
        state.apply_trait_modulated_change(
            {"loving": 0.5},
            trait_profile={"warmth": 0.9, "emotional_stability": 0.5},
        )
        # High warmth should boost loving
        assert state.get_emotion("loving") > 0.5

    def test_average_traits_near_raw(self):
        """Average traits (all 0.5) should produce near-raw changes."""
        state = EmotionalState()
        state.apply_trait_modulated_change(
            {"cheerful": 0.6},
            trait_profile={
                "emotional_stability": 0.5,
                "sensitivity": 0.5,
                "apprehension": 0.5,
                "tension": 0.5,
            },
        )
        # Should be close to raw value since all modifiers are near neutral
        assert abs(state.get_emotion("cheerful") - 0.6) < 0.15


# ──────────────────────────────────────────────────────────────
# Antagonistic Suppression
# ──────────────────────────────────────────────────────────────


class TestAntagonism:
    """Contradictory emotions should suppress each other."""

    def test_cheerful_suppresses_depressed(self):
        state = EmotionalState()
        state.change_state({"cheerful": 0.8, "depressed": 0.4})
        state.apply_antagonism()
        # Depressed should be reduced
        assert state.get_emotion("depressed") < 0.4
        # Cheerful shouldn't be touched (it's the stronger one)
        assert state.get_emotion("cheerful") == 0.8

    def test_stronger_always_wins(self):
        state = EmotionalState()
        state.change_state({"trusting": 0.3, "hostile": 0.9})
        state.apply_antagonism()
        # Trusting (weaker) should be suppressed
        assert state.get_emotion("trusting") < 0.3
        assert state.get_emotion("hostile") == 0.9

    def test_no_suppression_below_threshold(self):
        state = EmotionalState()
        state.change_state({"cheerful": 0.8, "depressed": 0.05})
        state.apply_antagonism()
        # Depressed is below 0.1 threshold, shouldn't be affected
        assert state.get_emotion("depressed") == 0.05

    def test_both_low_no_effect(self):
        state = EmotionalState()
        state.change_state({"hopeful": 0.05, "helpless": 0.05})
        state.apply_antagonism()
        assert state.get_emotion("hopeful") == 0.05
        assert state.get_emotion("helpless") == 0.05

    def test_strength_parameter(self):
        state1 = EmotionalState()
        state1.change_state({"content": 0.8, "angry": 0.5})
        state1.apply_antagonism(strength=0.1)
        mild_suppression = 0.5 - state1.get_emotion("angry")

        state2 = EmotionalState()
        state2.change_state({"content": 0.8, "angry": 0.5})
        state2.apply_antagonism(strength=0.8)
        strong_suppression = 0.5 - state2.get_emotion("angry")

        assert strong_suppression > mild_suppression

    def test_multiple_pairs(self):
        state = EmotionalState()
        state.change_state(
            {
                "cheerful": 0.8,
                "depressed": 0.4,
                "trusting": 0.7,
                "hostile": 0.3,
            }
        )
        state.apply_antagonism()
        # Both weaker sides should be reduced
        assert state.get_emotion("depressed") < 0.4
        assert state.get_emotion("hostile") < 0.3


# ──────────────────────────────────────────────────────────────
# Mood Baseline
# ──────────────────────────────────────────────────────────────


class TestMoodBaseline:
    """The mood baseline should shift slowly toward current emotions."""

    def test_baseline_starts_at_init_value(self):
        state = EmotionalState()
        assert state.get_mood_baseline("anxious") == 0.0

    def test_baseline_shifts_toward_current(self):
        state = EmotionalState()
        state.change_emotion("anxious", 0.8)
        state.update_mood_baseline(learning_rate=0.1)
        # Baseline should have moved toward 0.8
        assert state.get_mood_baseline("anxious") > 0.0

    def test_repeated_updates_accumulate(self):
        state = EmotionalState()
        state.change_emotion("anxious", 0.8)
        state.update_mood_baseline(learning_rate=0.1)
        after_one = state.get_mood_baseline("anxious")
        state.update_mood_baseline(learning_rate=0.1)
        after_two = state.get_mood_baseline("anxious")
        assert after_two > after_one

    def test_high_learning_rate(self):
        state = EmotionalState()
        state.change_emotion("cheerful", 0.9)
        state.update_mood_baseline(learning_rate=0.5)
        # Should be about halfway
        assert abs(state.get_mood_baseline("cheerful") - 0.45) < 0.05

    def test_decay_respects_elevated_baseline(self):
        """If baseline is high, emotions should decay TO that level, not below."""
        state = EmotionalState()
        state._mood_baseline["cheerful"] = 0.4
        state.change_emotion("cheerful", 0.9)
        for _ in range(10):
            state.decay(turns_elapsed=1)
        # After many decays, should approach baseline, not go to zero
        assert state.get_emotion("cheerful") > 0.35


# ──────────────────────────────────────────────────────────────
# Emotional Volatility
# ──────────────────────────────────────────────────────────────


class TestVolatility:
    """Volatility measures how far current emotions deviate from baseline."""

    def test_at_baseline_is_zero(self):
        state = EmotionalState()
        # All at 0.0, baseline at 0.0
        assert state.get_emotional_volatility() == 0.0

    def test_high_emotion_means_high_volatility(self):
        state = EmotionalState()
        state.change_emotion("anxious", 0.9)
        state.change_emotion("excited", 0.8)
        assert state.get_emotional_volatility() > 0

    def test_emotion_matching_baseline_is_low(self):
        state = EmotionalState()
        state.change_emotion("cheerful", 0.5)
        state._mood_baseline["cheerful"] = 0.5
        # Only one emotion deviated, but baseline matches
        # Other emotions still at 0 with 0 baseline, so low volatility
        assert state.get_emotional_volatility() < 0.02


# ──────────────────────────────────────────────────────────────
# Copy preserves dynamics state
# ──────────────────────────────────────────────────────────────


class TestCopyDynamics:
    """copy() should preserve mood baseline and turn counter."""

    def test_copy_preserves_mood_baseline(self):
        state = EmotionalState()
        state.change_emotion("anxious", 0.8)
        state.update_mood_baseline(learning_rate=0.3)
        copy = state.copy()
        assert copy.get_mood_baseline("anxious") == state.get_mood_baseline("anxious")

    def test_copy_is_independent(self):
        state = EmotionalState()
        state.change_emotion("cheerful", 0.5)
        copy = state.copy()
        copy.change_emotion("cheerful", 0.9)
        assert state.get_emotion("cheerful") == 0.5

    def test_copy_preserves_turn_counter(self):
        state = EmotionalState()
        state.decay(turns_elapsed=5)
        copy = state.copy()
        assert copy._last_update_turn == state._last_update_turn


# ──────────────────────────────────────────────────────────────
# Integration: Full Emotional Dynamics Cycle
# ──────────────────────────────────────────────────────────────


class TestFullCycle:
    """Test the complete emotional processing pipeline."""

    def test_full_cycle(self):
        """Simulate a realistic emotional processing turn."""
        state = EmotionalState()
        # Starting state: slightly cheerful
        state.change_emotion("cheerful", 0.6)
        state.change_emotion("content", 0.4)

        # Step 1: Decay (emotions fade slightly)
        state.decay(turns_elapsed=1)
        assert state.get_emotion("cheerful") < 0.6

        # Step 2: Apply new emotions from analysis (someone was rude)
        state.apply_trait_modulated_change(
            {"angry": 0.5, "hurt": 0.3, "cheerful": 0.2},
            trait_profile={"emotional_stability": 0.7, "sensitivity": 0.4},
        )

        # Step 3: Antagonism (anger suppresses content)
        state.apply_antagonism()

        # Step 4: Mood baseline shifts
        state.update_mood_baseline()

        # Verify plausible result
        assert state.get_emotion("angry") > 0  # Got angry
        assert state.get_emotion("cheerful") < 0.5  # Less cheerful
        assert state.get_mood_baseline("angry") > 0  # Baseline shifted

    def test_emotionally_stable_vs_reactive(self):
        """An emotionally stable person should weather the same insult better."""
        # Create two states with same starting emotions
        stable = EmotionalState()
        reactive = EmotionalState()
        for state in (stable, reactive):
            state.change_emotion("cheerful", 0.5)
            state.change_emotion("content", 0.4)

        # Same "insult" trigger
        insult_emotions = {"angry": 0.7, "hurt": 0.5, "cheerful": 0.1}

        stable.apply_trait_modulated_change(
            insult_emotions,
            trait_profile={"emotional_stability": 0.9, "sensitivity": 0.3},
        )
        reactive.apply_trait_modulated_change(
            insult_emotions,
            trait_profile={"emotional_stability": 0.2, "sensitivity": 0.8},
        )

        # The reactive person should be angrier and more hurt
        assert reactive.get_emotion("angry") > stable.get_emotion("angry")
        assert reactive.get_emotion("hurt") > stable.get_emotion("hurt")
