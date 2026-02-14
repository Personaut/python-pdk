"""Tests for trait-emotion coefficients."""

from __future__ import annotations

from personaut.traits.coefficients import (
    TRAIT_COEFFICIENTS,
    calculate_emotion_modifier,
    get_affected_emotions,
    get_coefficient,
    get_traits_affecting_emotion,
)
from personaut.traits.trait import ALL_TRAITS


class TestTraitCoefficients:
    """Tests for TRAIT_COEFFICIENTS mapping."""

    def test_all_traits_have_coefficients(self) -> None:
        """All 17 traits should have coefficient entries."""
        assert len(TRAIT_COEFFICIENTS) == 17

    def test_coefficients_match_traits(self) -> None:
        """Coefficient keys should match ALL_TRAITS."""
        assert set(TRAIT_COEFFICIENTS.keys()) == set(ALL_TRAITS)

    def test_coefficient_values_in_range(self) -> None:
        """All coefficients should be between -1.0 and 1.0."""
        for trait, coeffs in TRAIT_COEFFICIENTS.items():
            for emotion, value in coeffs.items():
                assert -1.0 <= value <= 1.0, f"{trait}->{emotion}: {value}"


class TestGetCoefficient:
    """Tests for get_coefficient function."""

    def test_existing_coefficient(self) -> None:
        """Should return correct coefficient for known pair."""
        coeff = get_coefficient("warmth", "loving")
        assert coeff == 0.4

    def test_no_relationship(self) -> None:
        """Should return 0.0 for emotions not affected by trait."""
        coeff = get_coefficient("warmth", "excited")
        assert coeff == 0.0

    def test_unknown_trait(self) -> None:
        """Should return 0.0 for unknown trait."""
        coeff = get_coefficient("charisma", "loving")
        assert coeff == 0.0

    def test_negative_coefficient(self) -> None:
        """Should handle negative coefficients."""
        coeff = get_coefficient("warmth", "hostile")
        assert coeff == -0.5


class TestGetAffectedEmotions:
    """Tests for get_affected_emotions function."""

    def test_warmth_emotions(self) -> None:
        """Warmth should affect multiple emotions."""
        emotions = get_affected_emotions("warmth")
        assert "loving" in emotions
        assert "trusting" in emotions
        assert "hostile" in emotions

    def test_unknown_trait(self) -> None:
        """Unknown trait should return empty list."""
        emotions = get_affected_emotions("charisma")
        assert emotions == []


class TestGetTraitsAffectingEmotion:
    """Tests for get_traits_affecting_emotion function."""

    def test_anxious_traits(self) -> None:
        """Multiple traits should affect anxious."""
        traits = get_traits_affecting_emotion("anxious")
        assert "emotional_stability" in traits
        assert "apprehension" in traits
        assert "tension" in traits

    def test_unknown_emotion(self) -> None:
        """Unknown emotion should return empty dict."""
        traits = get_traits_affecting_emotion("happiness")
        assert traits == {}

    def test_returns_coefficients(self) -> None:
        """Should return the actual coefficient values."""
        traits = get_traits_affecting_emotion("anxious")
        assert traits["emotional_stability"] == -0.5
        assert traits["apprehension"] == 0.4


class TestCalculateEmotionModifier:
    """Tests for calculate_emotion_modifier function."""

    def test_high_warmth_increases_loving(self) -> None:
        """High warmth should increase loving modifier."""
        traits = {"warmth": 0.9}
        modifier = calculate_emotion_modifier(traits, "loving")
        assert modifier > 0

    def test_low_warmth_decreases_loving(self) -> None:
        """Low warmth should decrease loving modifier."""
        traits = {"warmth": 0.1}
        modifier = calculate_emotion_modifier(traits, "loving")
        assert modifier < 0

    def test_average_trait_no_effect(self) -> None:
        """Average trait value should have no effect."""
        traits = {"warmth": 0.5}
        modifier = calculate_emotion_modifier(traits, "loving")
        assert modifier == 0.0

    def test_high_emotional_stability_decreases_anxious(self) -> None:
        """High emotional stability should decrease anxious."""
        traits = {"emotional_stability": 0.9}
        modifier = calculate_emotion_modifier(traits, "anxious")
        assert modifier < 0

    def test_multiple_traits_combine(self) -> None:
        """Multiple traits should combine their effects."""
        # Both warmth and sensitivity increase loving
        traits = {"warmth": 0.9, "sensitivity": 0.9}
        modifier = calculate_emotion_modifier(traits, "loving")
        single_modifier = calculate_emotion_modifier({"warmth": 0.9}, "loving")
        assert modifier > single_modifier

    def test_unrelated_emotion(self) -> None:
        """Unrelated emotion should have zero modifier."""
        traits = {"warmth": 0.9}
        modifier = calculate_emotion_modifier(traits, "bored")
        assert modifier == 0.0
