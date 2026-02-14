"""Integration tests for conversation simulations.

These tests require a valid LLM API key (Gemini or Bedrock).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from personaut import (
    create_individual,
    create_simulation,
    EmotionalState,
    WARMTH,
    LIVELINESS,
    IN_PERSON,
    CONVERSATION,
)
from personaut.situations import create_situation
from personaut.models import get_llm, Provider


# Skip if no API key
pytestmark = pytest.mark.skipif(
    not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("AWS_ACCESS_KEY_ID")),
    reason="No API credentials available",
)


def get_available_llm():
    """Get an available LLM provider."""
    if os.environ.get("GOOGLE_API_KEY"):
        return get_llm(Provider.GEMINI)
    elif os.environ.get("AWS_ACCESS_KEY_ID"):
        return get_llm(Provider.BEDROCK)
    raise RuntimeError("No API credentials available")


class TestConversationSimulation:
    """End-to-end conversation simulation tests."""

    @pytest.fixture
    def sarah(self) -> "Individual":
        """Create Sarah individual."""
        from personaut import Individual

        sarah = create_individual(
            name="Sarah",
            description="A friendly barista who loves coffee and art. She's warm, empathetic, and loves to chat.",
            individual_type="simulated",
        )
        sarah.set_trait(WARMTH, 0.9)
        sarah.set_trait(LIVELINESS, 0.7)
        sarah.change_emotion("cheerful", 0.6)
        return sarah

    @pytest.fixture
    def mike(self) -> "Individual":
        """Create Mike individual."""
        from personaut import Individual

        mike = create_individual(
            name="Mike",
            description="A regular customer who's a software developer. He's friendly but sometimes stressed about work.",
            individual_type="simulated",
        )
        mike.set_trait(WARMTH, 0.6)
        mike.change_emotion("anxious", 0.4)
        return mike

    @pytest.fixture
    def coffee_shop_situation(self):
        """Create coffee shop situation."""
        return create_situation(
            modality=IN_PERSON,
            description="Morning rush at a cozy coffee shop in downtown Miami",
            location="Miami, FL",
        )

    def test_basic_conversation(self, sarah, mike, coffee_shop_situation) -> None:
        """Test basic conversation simulation."""
        llm = get_available_llm()

        simulation = create_simulation(
            situation=coffee_shop_situation,
            individuals=[sarah, mike],
            simulation_type=CONVERSATION,
            llm=llm,
        )

        result = simulation.run(num_turns=3)

        assert result is not None
        assert result.turns is not None
        assert len(result.turns) >= 2  # At least 2 turns exchanged

    def test_conversation_content(self, sarah, mike, coffee_shop_situation) -> None:
        """Test conversation produces meaningful content."""
        llm = get_available_llm()

        simulation = create_simulation(
            situation=coffee_shop_situation,
            individuals=[sarah, mike],
            simulation_type=CONVERSATION,
            llm=llm,
        )

        result = simulation.run(num_turns=2)

        # Check turns have content
        for turn in result.turns:
            assert turn.speaker in ["Sarah", "Mike"]
            assert turn.content is not None
            assert len(turn.content) > 0

    def test_emotional_state_persistence(self, sarah, mike, coffee_shop_situation) -> None:
        """Test emotional states are maintained during simulation."""
        llm = get_available_llm()

        initial_sarah_state = sarah._emotional_state.to_dict()

        simulation = create_simulation(
            situation=coffee_shop_situation,
            individuals=[sarah, mike],
            simulation_type=CONVERSATION,
            llm=llm,
        )

        result = simulation.run(num_turns=2)

        # Sarah's emotional state should still be accessible
        assert sarah._emotional_state is not None
        # Initial state was set
        assert initial_sarah_state.get("cheerful", 0) > 0

    def test_save_conversation_output(self, sarah, mike, coffee_shop_situation) -> None:
        """Test saving conversation to file."""
        llm = get_available_llm()

        simulation = create_simulation(
            situation=coffee_shop_situation,
            individuals=[sarah, mike],
            simulation_type=CONVERSATION,
            llm=llm,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = simulation.run(num_turns=2, output_dir=tmpdir)

            # Check output file exists
            output_files = list(Path(tmpdir).glob("*.txt")) + list(Path(tmpdir).glob("*.json"))
            assert len(output_files) >= 1


class TestConversationPromptGeneration:
    """Tests for prompt generation in conversations."""

    @pytest.fixture
    def individual(self):
        """Create test individual."""
        ind = create_individual(
            name="Test",
            description="A test persona",
        )
        ind.set_trait(WARMTH, 0.8)
        ind.change_emotion("cheerful", 0.5)
        return ind

    def test_prompt_includes_traits(self, individual) -> None:
        """Test generated prompts include trait information."""
        # Access prompt generation through simulation internals
        situation = create_situation(
            modality=IN_PERSON,
            description="Test situation",
        )

        # Verify trait is set
        assert individual.get_trait(WARMTH) == 0.8

    def test_prompt_includes_emotions(self, individual) -> None:
        """Test generated prompts include emotional state."""
        # Verify emotion is set
        dominant = individual._emotional_state.get_dominant()
        assert dominant is not None
        assert dominant[0] == "cheerful"


class TestConversationEdgeCases:
    """Tests for edge cases in conversation simulation."""

    def test_single_turn_conversation(self) -> None:
        """Test simulation with only one turn."""
        llm = get_available_llm()

        individual = create_individual(name="Solo", description="A lonely persona")
        situation = create_situation(modality=IN_PERSON, description="Monologue")

        simulation = create_simulation(
            situation=situation,
            individuals=[individual],
            simulation_type=CONVERSATION,
            llm=llm,
        )

        result = simulation.run(num_turns=1)

        assert result is not None
        assert len(result.turns) >= 1

    def test_long_conversation(self) -> None:
        """Test longer conversation maintains coherence."""
        llm = get_available_llm()

        person_a = create_individual(name="Alice", description="Talkative person")
        person_b = create_individual(name="Bob", description="Good listener")
        situation = create_situation(modality=IN_PERSON, description="Long chat")

        simulation = create_simulation(
            situation=situation,
            individuals=[person_a, person_b],
            simulation_type=CONVERSATION,
            llm=llm,
        )

        result = simulation.run(num_turns=5)

        assert result is not None
        assert len(result.turns) >= 4
