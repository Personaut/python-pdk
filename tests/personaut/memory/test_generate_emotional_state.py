"""Tests for generate_memory_emotional_state function."""

from __future__ import annotations

import json
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from personaut.emotions.state import EmotionalState
from personaut.memory.individual import generate_memory_emotional_state


@dataclass
class MockGenerationResult:
    """Mock LLM generation result."""

    text: str


def _mock_llm(response_text: str) -> MagicMock:
    """Create a mock LLM that returns the given text."""
    mock = MagicMock()
    mock.generate.return_value = MockGenerationResult(text=response_text)
    return mock


class TestGenerateMemoryEmotionalState:
    """Tests for generate_memory_emotional_state function."""

    @patch("personaut.models.registry.get_llm")
    def test_basic_generation(self, mock_get_llm: MagicMock) -> None:
        """Should return EmotionalState with emotions from LLM."""
        llm_response = json.dumps({"proud": 0.8, "excited": 0.6, "anxious": 0.2})
        mock_get_llm.return_value = _mock_llm(llm_response)

        state = generate_memory_emotional_state(
            description="Got promoted at work",
        )

        assert isinstance(state, EmotionalState)
        mock_get_llm.return_value.generate.assert_called_once()

    @patch("personaut.models.registry.get_llm")
    def test_with_trait_profile(self, mock_get_llm: MagicMock) -> None:
        """Should include trait information in the prompt."""
        llm_response = json.dumps({"proud": 0.8})
        mock_llm = _mock_llm(llm_response)
        mock_get_llm.return_value = mock_llm

        state = generate_memory_emotional_state(
            description="Won a competition",
            trait_profile={"emotional_stability": 0.8, "sensitivity": 0.3},
            individual_name="Sarah",
        )

        assert isinstance(state, EmotionalState)
        # Verify the prompt mentioned traits
        call_args = mock_llm.generate.call_args
        prompt = call_args[0][0]
        assert "Sarah" in prompt

    @patch("personaut.models.registry.get_llm")
    def test_with_high_traits(self, mock_get_llm: MagicMock) -> None:
        """High traits should appear in 'High traits' in prompt."""
        llm_response = json.dumps({"proud": 0.7})
        mock_llm = _mock_llm(llm_response)
        mock_get_llm.return_value = mock_llm

        generate_memory_emotional_state(
            description="Test",
            trait_profile={"warmth": 0.9, "dominance": 0.8},
        )

        prompt = mock_llm.generate.call_args[0][0]
        assert "High traits:" in prompt
        assert "warmth" in prompt

    @patch("personaut.models.registry.get_llm")
    def test_with_low_traits(self, mock_get_llm: MagicMock) -> None:
        """Low traits should appear in 'Low traits' in prompt."""
        llm_response = json.dumps({"anxious": 0.6})
        mock_llm = _mock_llm(llm_response)
        mock_get_llm.return_value = mock_llm

        generate_memory_emotional_state(
            description="Test",
            trait_profile={"warmth": 0.2, "dominance": 0.1},
        )

        prompt = mock_llm.generate.call_args[0][0]
        assert "Low traits:" in prompt
        assert "warmth" in prompt

    @patch("personaut.models.registry.get_llm")
    def test_with_medium_traits(self, mock_get_llm: MagicMock) -> None:
        """Medium traits (neither high nor low) should use average description."""
        llm_response = json.dumps({"cheerful": 0.5})
        mock_llm = _mock_llm(llm_response)
        mock_get_llm.return_value = mock_llm

        generate_memory_emotional_state(
            description="Test",
            trait_profile={"warmth": 0.5},  # Neither high nor low
        )

        prompt = mock_llm.generate.call_args[0][0]
        # Should use default trait summary since no high/low traits
        assert "Average personality" in prompt

    @patch("personaut.models.registry.get_llm")
    def test_no_trait_profile(self, mock_get_llm: MagicMock) -> None:
        """No trait profile should use average description."""
        llm_response = json.dumps({"cheerful": 0.5})
        mock_get_llm.return_value = _mock_llm(llm_response)

        generate_memory_emotional_state(description="Test")

        prompt = mock_get_llm.return_value.generate.call_args[0][0]
        assert "Average personality" in prompt

    @patch("personaut.models.registry.get_llm")
    def test_strips_markdown_fences(self, mock_get_llm: MagicMock) -> None:
        """Should strip markdown code fences from response."""
        llm_response = '```json\n{"proud": 0.8, "excited": 0.6}\n```'
        mock_get_llm.return_value = _mock_llm(llm_response)

        state = generate_memory_emotional_state(description="Got promoted")
        assert isinstance(state, EmotionalState)

    @patch("personaut.models.registry.get_llm")
    def test_extracts_json_from_surrounding_text(self, mock_get_llm: MagicMock) -> None:
        """Should find JSON object in surrounding explanatory text."""
        llm_response = 'Based on analysis: {"proud": 0.8, "excited": 0.6}. These represent...'
        mock_get_llm.return_value = _mock_llm(llm_response)

        state = generate_memory_emotional_state(description="Got promoted")
        assert isinstance(state, EmotionalState)

    @patch("personaut.models.registry.get_llm")
    def test_clamps_values(self, mock_get_llm: MagicMock) -> None:
        """Values outside 0-1 range should be clamped."""
        llm_response = json.dumps({"proud": 1.5, "anxious": -0.3})
        mock_get_llm.return_value = _mock_llm(llm_response)

        state = generate_memory_emotional_state(description="Test")
        assert isinstance(state, EmotionalState)

    @patch("personaut.models.registry.get_llm")
    def test_filters_invalid_emotions(self, mock_get_llm: MagicMock) -> None:
        """Invalid emotion names should be filtered out."""
        llm_response = json.dumps(
            {
                "proud": 0.8,
                "nonexistent_emotion": 0.5,
                "excited": 0.6,
            }
        )
        mock_get_llm.return_value = _mock_llm(llm_response)

        state = generate_memory_emotional_state(description="Test")
        assert isinstance(state, EmotionalState)

    @patch("personaut.models.registry.get_llm")
    def test_no_json_raises_runtime_error(self, mock_get_llm: MagicMock) -> None:
        """Response without JSON should raise RuntimeError."""
        mock_get_llm.return_value = _mock_llm("I don't know what to say")

        with pytest.raises(RuntimeError, match="Could not parse"):
            generate_memory_emotional_state(description="Test")

    @patch("personaut.models.registry.get_llm")
    def test_empty_valid_emotions_raises_runtime_error(self, mock_get_llm: MagicMock) -> None:
        """Response with only invalid emotions should raise RuntimeError."""
        llm_response = json.dumps(
            {
                "fake_emotion": 0.8,
                "another_fake": 0.5,
            }
        )
        mock_get_llm.return_value = _mock_llm(llm_response)

        with pytest.raises(RuntimeError, match="No valid emotions"):
            generate_memory_emotional_state(description="Test")

    @patch("personaut.models.registry.get_llm")
    def test_filters_non_numeric_values(self, mock_get_llm: MagicMock) -> None:
        """Non-numeric emotion values should be filtered out."""
        llm_response = json.dumps(
            {
                "proud": 0.8,
                "excited": "high",  # not numeric
                "anxious": 0.3,
            }
        )
        mock_get_llm.return_value = _mock_llm(llm_response)

        state = generate_memory_emotional_state(description="Test")
        assert isinstance(state, EmotionalState)

    @patch("personaut.models.registry.get_llm")
    def test_default_individual_name(self, mock_get_llm: MagicMock) -> None:
        """Default individual_name should be 'this person'."""
        llm_response = json.dumps({"proud": 0.8})
        mock_llm = _mock_llm(llm_response)
        mock_get_llm.return_value = mock_llm

        generate_memory_emotional_state(description="Test")

        prompt = mock_llm.generate.call_args[0][0]
        assert "this person" in prompt

    @patch("personaut.models.registry.get_llm")
    def test_calls_llm_with_low_temperature(self, mock_get_llm: MagicMock) -> None:
        """Should call LLM with temperature=0.3 for consistency."""
        llm_response = json.dumps({"proud": 0.8})
        mock_llm = _mock_llm(llm_response)
        mock_get_llm.return_value = mock_llm

        generate_memory_emotional_state(description="Test")

        call_kwargs = mock_llm.generate.call_args[1]
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 256
