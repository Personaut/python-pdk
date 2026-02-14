"""Tests for emotion definitions."""

from __future__ import annotations

from personaut.emotions.emotion import (
    ALL_EMOTIONS,
    ANGER_EMOTIONS,
    ANGRY,
    ANXIOUS,
    EMOTION_METADATA,
    FEAR_EMOTIONS,
    HOPEFUL,
    JOY_EMOTIONS,
    PEACEFUL_EMOTIONS,
    POWERFUL_EMOTIONS,
    SAD_EMOTIONS,
    Emotion,
    get_emotion_metadata,
    is_valid_emotion,
)


class TestEmotionConstants:
    """Tests for emotion constants."""

    def test_all_emotions_count(self) -> None:
        """ALL_EMOTIONS should contain exactly 36 emotions."""
        assert len(ALL_EMOTIONS) == 36

    def test_all_emotions_are_lowercase(self) -> None:
        """All emotion values should be lowercase strings."""
        for emotion in ALL_EMOTIONS:
            assert emotion == emotion.lower()
            assert isinstance(emotion, str)

    def test_all_emotions_unique(self) -> None:
        """All emotions should be unique."""
        assert len(ALL_EMOTIONS) == len(set(ALL_EMOTIONS))

    def test_emotion_constants_values(self) -> None:
        """Emotion constants should have correct string values."""
        assert ANGRY == "angry"
        assert ANXIOUS == "anxious"
        assert HOPEFUL == "hopeful"


class TestEmotionCategoryLists:
    """Tests for category emotion lists."""

    def test_anger_emotions_count(self) -> None:
        """ANGER_EMOTIONS should contain 6 emotions."""
        assert len(ANGER_EMOTIONS) == 6

    def test_sad_emotions_count(self) -> None:
        """SAD_EMOTIONS should contain 6 emotions."""
        assert len(SAD_EMOTIONS) == 6

    def test_fear_emotions_count(self) -> None:
        """FEAR_EMOTIONS should contain 6 emotions."""
        assert len(FEAR_EMOTIONS) == 6

    def test_joy_emotions_count(self) -> None:
        """JOY_EMOTIONS should contain 6 emotions."""
        assert len(JOY_EMOTIONS) == 6

    def test_powerful_emotions_count(self) -> None:
        """POWERFUL_EMOTIONS should contain 6 emotions."""
        assert len(POWERFUL_EMOTIONS) == 6

    def test_peaceful_emotions_count(self) -> None:
        """PEACEFUL_EMOTIONS should contain 6 emotions."""
        assert len(PEACEFUL_EMOTIONS) == 6

    def test_category_lists_sum_to_all(self) -> None:
        """Category lists should sum to all 36 emotions."""
        all_from_categories = (
            ANGER_EMOTIONS + SAD_EMOTIONS + FEAR_EMOTIONS + JOY_EMOTIONS + POWERFUL_EMOTIONS + PEACEFUL_EMOTIONS
        )
        assert len(all_from_categories) == 36
        assert set(all_from_categories) == set(ALL_EMOTIONS)


class TestEmotionClass:
    """Tests for Emotion dataclass."""

    def test_emotion_creation(self) -> None:
        """Emotion should be creatable with name, category, description."""
        emotion = Emotion("test", "category", "A test emotion")
        assert emotion.name == "test"
        assert emotion.category == "category"
        assert emotion.description == "A test emotion"

    def test_emotion_str(self) -> None:
        """Emotion should return its name when converted to string."""
        emotion = Emotion("test", "category", "A test emotion")
        assert str(emotion) == "test"

    def test_emotion_is_frozen(self) -> None:
        """Emotion should be immutable."""
        emotion = Emotion("test", "category", "A test emotion")
        try:
            emotion.name = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised FrozenInstanceError")
        except Exception:
            pass  # Expected


class TestEmotionMetadata:
    """Tests for EMOTION_METADATA registry."""

    def test_all_emotions_have_metadata(self) -> None:
        """All 36 emotions should have metadata entries."""
        assert len(EMOTION_METADATA) == 36

    def test_metadata_matches_emotions(self) -> None:
        """Metadata keys should match ALL_EMOTIONS."""
        assert set(EMOTION_METADATA.keys()) == set(ALL_EMOTIONS)

    def test_metadata_has_valid_categories(self) -> None:
        """All metadata should have valid category names."""
        valid_categories = {"anger", "sad", "fear", "joy", "powerful", "peaceful"}
        for emotion, metadata in EMOTION_METADATA.items():
            assert metadata.category in valid_categories, f"{emotion} has invalid category"

    def test_metadata_names_match_keys(self) -> None:
        """Metadata emotion names should match their dictionary keys."""
        for emotion, metadata in EMOTION_METADATA.items():
            assert metadata.name == emotion


class TestGetEmotionMetadata:
    """Tests for get_emotion_metadata function."""

    def test_get_valid_emotion(self) -> None:
        """get_emotion_metadata should return correct data for valid emotions."""
        metadata = get_emotion_metadata("anxious")
        assert metadata.name == "anxious"
        assert metadata.category == "fear"
        assert len(metadata.description) > 0

    def test_get_invalid_emotion(self) -> None:
        """get_emotion_metadata should raise KeyError for unknown emotions."""
        try:
            get_emotion_metadata("happiness")
            raise AssertionError("Should have raised KeyError")
        except KeyError:
            pass


class TestIsValidEmotion:
    """Tests for is_valid_emotion function."""

    def test_valid_emotion(self) -> None:
        """is_valid_emotion should return True for valid emotions."""
        assert is_valid_emotion("anxious") is True
        assert is_valid_emotion("hopeful") is True
        assert is_valid_emotion("angry") is True

    def test_invalid_emotion(self) -> None:
        """is_valid_emotion should return False for invalid emotions."""
        assert is_valid_emotion("happiness") is False
        assert is_valid_emotion("ANXIOUS") is False  # Case sensitive
        assert is_valid_emotion("") is False
