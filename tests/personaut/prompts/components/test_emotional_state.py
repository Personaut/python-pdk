"""Tests for EmotionalStateComponent."""

import pytest

from personaut.emotions.state import EmotionalState
from personaut.prompts.components.emotional_state import (
    EmotionalStateComponent,
    get_intensity_description,
    get_intensity_label,
)


class TestGetIntensityLabel:
    """Tests for get_intensity_label function."""

    def test_minimal_intensity(self) -> None:
        """Test minimal intensity label."""
        assert get_intensity_label(0.0) == "minimal"
        assert get_intensity_label(0.1) == "minimal"

    def test_slight_intensity(self) -> None:
        """Test slight intensity label."""
        assert get_intensity_label(0.2) == "slight"
        assert get_intensity_label(0.3) == "slight"

    def test_noticeable_intensity(self) -> None:
        """Test noticeable intensity label."""
        assert get_intensity_label(0.4) == "noticeable"
        assert get_intensity_label(0.5) == "noticeable"

    def test_significant_intensity(self) -> None:
        """Test significant intensity label."""
        assert get_intensity_label(0.6) == "significant"
        assert get_intensity_label(0.7) == "significant"

    def test_overwhelming_intensity(self) -> None:
        """Test overwhelming intensity label."""
        assert get_intensity_label(0.8) == "overwhelming"
        assert get_intensity_label(1.0) == "overwhelming"


class TestGetIntensityDescription:
    """Tests for get_intensity_description function."""

    def test_creates_description(self) -> None:
        """Test that description combines intensity and emotion."""
        desc = get_intensity_description("anxious", 0.7)
        assert "significant" in desc
        assert "anxious" in desc

    def test_different_emotions(self) -> None:
        """Test with different emotions."""
        assert "hopeful" in get_intensity_description("hopeful", 0.5)
        assert "angry" in get_intensity_description("angry", 0.9)


class TestEmotionalStateComponent:
    """Tests for EmotionalStateComponent class."""

    @pytest.fixture
    def component(self) -> EmotionalStateComponent:
        """Create a component for testing."""
        return EmotionalStateComponent()

    @pytest.fixture
    def neutral_state(self) -> EmotionalState:
        """Create a neutral emotional state."""
        return EmotionalState()

    @pytest.fixture
    def anxious_state(self) -> EmotionalState:
        """Create an anxious emotional state."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.7)
        return state

    @pytest.fixture
    def mixed_state(self) -> EmotionalState:
        """Create a mixed emotional state."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.7)
        state.change_emotion("hopeful", 0.5)
        state.change_emotion("confused", 0.3)
        return state

    def test_format_neutral_state(
        self,
        component: EmotionalStateComponent,
        neutral_state: EmotionalState,
    ) -> None:
        """Test formatting a neutral state."""
        text = component.format(neutral_state)
        assert "neutral" in text.lower()

    def test_format_single_emotion(
        self,
        component: EmotionalStateComponent,
        anxious_state: EmotionalState,
    ) -> None:
        """Test formatting a single elevated emotion."""
        text = component.format(anxious_state)
        assert "anxious" in text.lower()

    def test_format_mixed_emotions(
        self,
        component: EmotionalStateComponent,
        mixed_state: EmotionalState,
    ) -> None:
        """Test formatting multiple emotions."""
        text = component.format(mixed_state)
        assert "anxious" in text.lower()
        assert "hopeful" in text.lower()

    def test_highlight_dominant(
        self,
        component: EmotionalStateComponent,
        mixed_state: EmotionalState,
    ) -> None:
        """Test highlighting the dominant emotion."""
        text = component.format(mixed_state, highlight_dominant=True)
        assert "primarily" in text.lower()
        assert "anxious" in text.lower()

    def test_custom_name(
        self,
        component: EmotionalStateComponent,
        anxious_state: EmotionalState,
    ) -> None:
        """Test using a custom name."""
        text = component.format(anxious_state, name="Sarah")
        assert "Sarah" in text

    def test_intensity_threshold(self, anxious_state: EmotionalState) -> None:
        """Test that intensity threshold filters emotions."""
        component = EmotionalStateComponent(intensity_threshold=0.8)
        text = component.format(anxious_state)
        # 0.7 is below 0.8, should not be included
        assert "neutral" in text.lower()

    def test_max_emotions(self, mixed_state: EmotionalState) -> None:
        """Test limiting number of emotions."""
        component = EmotionalStateComponent(max_emotions=1)
        text = component.format(mixed_state)
        # Should only include dominant emotion
        assert "anxious" in text.lower()

    def test_format_brief(
        self,
        component: EmotionalStateComponent,
        anxious_state: EmotionalState,
    ) -> None:
        """Test brief format."""
        text = component.format_brief(anxious_state)
        assert "anxious" in text.lower()

    def test_format_brief_neutral(
        self,
        component: EmotionalStateComponent,
        neutral_state: EmotionalState,
    ) -> None:
        """Test brief format for neutral state."""
        text = component.format_brief(neutral_state)
        assert text == "neutral"
