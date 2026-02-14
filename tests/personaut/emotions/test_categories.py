"""Tests for emotion categories."""

from __future__ import annotations

import pytest

from personaut.emotions.categories import (
    CATEGORY_EMOTIONS,
    EmotionCategory,
    get_category,
    get_emotions_in_category,
    get_negative_emotions,
    get_positive_emotions,
    parse_category,
)
from personaut.emotions.emotion import ALL_EMOTIONS


class TestEmotionCategoryEnum:
    """Tests for EmotionCategory enum."""

    def test_all_categories_defined(self) -> None:
        """All 6 categories should be defined."""
        assert len(EmotionCategory) == 6

    def test_category_values(self) -> None:
        """Categories should have correct string values."""
        assert EmotionCategory.ANGER.value == "anger"
        assert EmotionCategory.SAD.value == "sad"
        assert EmotionCategory.FEAR.value == "fear"
        assert EmotionCategory.JOY.value == "joy"
        assert EmotionCategory.POWERFUL.value == "powerful"
        assert EmotionCategory.PEACEFUL.value == "peaceful"


class TestCategoryDescription:
    """Tests for category description property."""

    def test_all_categories_have_descriptions(self) -> None:
        """All categories should have descriptions."""
        for category in EmotionCategory:
            assert category.description
            assert len(category.description) > 10


class TestCategoryPolarity:
    """Tests for is_positive and is_negative properties."""

    def test_positive_categories(self) -> None:
        """JOY, POWERFUL, PEACEFUL should be positive."""
        assert EmotionCategory.JOY.is_positive is True
        assert EmotionCategory.POWERFUL.is_positive is True
        assert EmotionCategory.PEACEFUL.is_positive is True

    def test_negative_categories(self) -> None:
        """ANGER, SAD, FEAR should be negative."""
        assert EmotionCategory.ANGER.is_negative is True
        assert EmotionCategory.SAD.is_negative is True
        assert EmotionCategory.FEAR.is_negative is True

    def test_positive_not_negative(self) -> None:
        """Positive categories should not be negative."""
        for category in EmotionCategory:
            if category.is_positive:
                assert category.is_negative is False

    def test_negative_not_positive(self) -> None:
        """Negative categories should not be positive."""
        for category in EmotionCategory:
            if category.is_negative:
                assert category.is_positive is False


class TestCategoryValence:
    """Tests for valence property."""

    def test_positive_categories_positive_valence(self) -> None:
        """Positive categories should have positive valence."""
        assert EmotionCategory.JOY.valence > 0
        assert EmotionCategory.POWERFUL.valence > 0
        assert EmotionCategory.PEACEFUL.valence > 0

    def test_negative_categories_negative_valence(self) -> None:
        """Negative categories should have negative valence."""
        assert EmotionCategory.ANGER.valence < 0
        assert EmotionCategory.SAD.valence < 0
        assert EmotionCategory.FEAR.valence < 0

    def test_valence_range(self) -> None:
        """Valence should be between -1.0 and 1.0."""
        for category in EmotionCategory:
            assert -1.0 <= category.valence <= 1.0


class TestCategoryArousal:
    """Tests for arousal property."""

    def test_high_arousal_categories(self) -> None:
        """ANGER and FEAR should have high arousal."""
        assert EmotionCategory.ANGER.arousal >= 0.8
        assert EmotionCategory.FEAR.arousal >= 0.7

    def test_low_arousal_categories(self) -> None:
        """SAD and PEACEFUL should have low arousal."""
        assert EmotionCategory.SAD.arousal <= 0.3
        assert EmotionCategory.PEACEFUL.arousal <= 0.3

    def test_arousal_range(self) -> None:
        """Arousal should be between 0.0 and 1.0."""
        for category in EmotionCategory:
            assert 0.0 <= category.arousal <= 1.0


class TestCategoryEmotions:
    """Tests for CATEGORY_EMOTIONS mapping."""

    def test_all_categories_have_emotions(self) -> None:
        """Each category should have emotions mapped."""
        for category in EmotionCategory:
            assert category in CATEGORY_EMOTIONS
            assert len(CATEGORY_EMOTIONS[category]) > 0

    def test_each_category_has_six_emotions(self) -> None:
        """Each category should have exactly 6 emotions."""
        for category in EmotionCategory:
            assert len(CATEGORY_EMOTIONS[category]) == 6

    def test_all_emotions_covered(self) -> None:
        """All 36 emotions should be in category mappings."""
        all_mapped = []
        for emotions in CATEGORY_EMOTIONS.values():
            all_mapped.extend(emotions)
        assert len(all_mapped) == 36
        assert set(all_mapped) == set(ALL_EMOTIONS)


class TestGetCategory:
    """Tests for get_category function."""

    def test_get_category_anger(self) -> None:
        """Anger emotions should return ANGER category."""
        assert get_category("angry") == EmotionCategory.ANGER
        assert get_category("hostile") == EmotionCategory.ANGER

    def test_get_category_fear(self) -> None:
        """Fear emotions should return FEAR category."""
        assert get_category("anxious") == EmotionCategory.FEAR
        assert get_category("helpless") == EmotionCategory.FEAR

    def test_get_category_joy(self) -> None:
        """Joy emotions should return JOY category."""
        assert get_category("hopeful") == EmotionCategory.JOY
        assert get_category("excited") == EmotionCategory.JOY

    def test_get_category_invalid(self) -> None:
        """Invalid emotion should raise KeyError."""
        with pytest.raises(KeyError):
            get_category("happiness")


class TestGetEmotionsInCategory:
    """Tests for get_emotions_in_category function."""

    def test_get_fear_emotions(self) -> None:
        """Should return all fear emotions."""
        emotions = get_emotions_in_category(EmotionCategory.FEAR)
        assert "anxious" in emotions
        assert "helpless" in emotions
        assert len(emotions) == 6

    def test_get_joy_emotions(self) -> None:
        """Should return all joy emotions."""
        emotions = get_emotions_in_category(EmotionCategory.JOY)
        assert "hopeful" in emotions
        assert "excited" in emotions
        assert len(emotions) == 6

    def test_returns_list_copy(self) -> None:
        """Should return a copy, not the original list."""
        emotions = get_emotions_in_category(EmotionCategory.FEAR)
        emotions.append("test")
        # Original should not be modified
        assert len(get_emotions_in_category(EmotionCategory.FEAR)) == 6


class TestGetPositiveNegativeEmotions:
    """Tests for get_positive_emotions and get_negative_emotions."""

    def test_positive_emotions_count(self) -> None:
        """Should return 18 positive emotions (3 categories x 6)."""
        positive = get_positive_emotions()
        assert len(positive) == 18

    def test_negative_emotions_count(self) -> None:
        """Should return 18 negative emotions (3 categories x 6)."""
        negative = get_negative_emotions()
        assert len(negative) == 18

    def test_positive_contains_joy(self) -> None:
        """Positive emotions should include joy emotions."""
        positive = get_positive_emotions()
        assert "hopeful" in positive
        assert "excited" in positive

    def test_negative_contains_fear(self) -> None:
        """Negative emotions should include fear emotions."""
        negative = get_negative_emotions()
        assert "anxious" in negative
        assert "helpless" in negative

    def test_no_overlap(self) -> None:
        """Positive and negative emotions should not overlap."""
        positive = set(get_positive_emotions())
        negative = set(get_negative_emotions())
        assert len(positive & negative) == 0


class TestParseCategory:
    """Tests for parse_category function."""

    def test_parse_string(self) -> None:
        """Should parse string to EmotionCategory."""
        assert parse_category("joy") == EmotionCategory.JOY
        assert parse_category("fear") == EmotionCategory.FEAR

    def test_parse_enum(self) -> None:
        """Should pass through EmotionCategory values."""
        assert parse_category(EmotionCategory.JOY) == EmotionCategory.JOY

    def test_parse_invalid(self) -> None:
        """Should raise ValueError for invalid strings."""
        with pytest.raises(ValueError, match="Invalid emotion category"):
            parse_category("happiness")
