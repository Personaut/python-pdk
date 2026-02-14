"""Tests for conversation simulation."""

from __future__ import annotations

import json
import tempfile

from personaut.simulations.conversation import ConversationSimulation
from personaut.simulations.styles import SimulationStyle
from personaut.simulations.types import SimulationType
from tests.personaut.simulations.conftest import MockIndividual, MockSituation


class TestConversationSimulation:
    """Tests for ConversationSimulation class."""

    def test_create_conversation_simulation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test creating a conversation simulation."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
        )
        assert simulation.simulation_type == SimulationType.CONVERSATION
        assert len(simulation.individuals) == 2

    def test_default_style_is_script(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test default style is script."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.CONVERSATION,
        )
        assert simulation.style == SimulationStyle.SCRIPT

    def test_generate_conversation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test generating a conversation."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=4,
        )
        content = simulation._generate()

        # Should contain participant names
        assert "SARAH" in content or "Sarah" in content
        assert "MIKE" in content or "Mike" in content

    def test_max_turns_limits_output(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test max_turns limits conversation length."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=2,
        )
        simulation._generate()
        assert len(simulation._conversation_history) == 2

    def test_json_format(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test JSON format output."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            style=SimulationStyle.JSON,
            max_turns=2,
        )
        content = simulation._generate()

        # Should be valid JSON
        data = json.loads(content)
        assert data["simulation_type"] == "conversation"
        assert "turns" in data
        assert len(data["turns"]) == 2

    def test_script_format_header(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test script format includes header."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=2,
        )
        content = simulation._generate()

        assert "=== Conversation Simulation ===" in content
        assert "Situation:" in content
        assert "Participants:" in content

    def test_run_creates_files(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test run creates output files."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=2,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            results = simulation.run(num=1, dir=tmpdir)
            assert len(results) == 1
            assert results[0].output_path is not None
            assert results[0].output_path.exists()

    def test_include_actions_option(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test include_actions option."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            include_actions=True,
            max_turns=2,
        )
        assert simulation.include_actions is True


class TestConversationHistory:
    """Tests for conversation history tracking."""

    def test_history_is_recorded(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test conversation history is recorded."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=4,
        )
        simulation._generate()

        assert len(simulation._conversation_history) == 4
        for turn in simulation._conversation_history:
            assert "speaker" in turn
            assert "content" in turn

    def test_history_alternates_speakers(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test speakers alternate in history."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=4,
        )
        simulation._generate()

        speakers = [turn["speaker"] for turn in simulation._conversation_history]
        # Should alternate between Sarah and Mike
        assert speakers[0] != speakers[1]
        assert speakers[2] != speakers[3]

    def test_history_is_reset_between_runs(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test history is reset between generate calls."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=2,
        )

        # First run
        simulation._generate()
        simulation._conversation_history.copy()

        # Second run
        simulation._generate()

        # History should be fresh (same length, not accumulated)
        assert len(simulation._conversation_history) == 2


class TestEmotionalInfluence:
    """Tests for emotional state influence on conversation."""

    def test_anxious_individual_response(
        self,
        mock_situation: MockSituation,
        mock_individual_anxious: MockIndividual,
    ) -> None:
        """Test anxious individual produces appropriate responses."""
        simulation = ConversationSimulation(
            situation=mock_situation,
            individuals=[mock_individual_anxious],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=1,
        )
        content = simulation._generate()
        # Should produce some content
        assert content
