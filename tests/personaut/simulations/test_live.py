"""Tests for live simulation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from personaut.simulations.live import (
    ChatMessage,
    LiveSimulation,
)
from personaut.simulations.styles import SimulationStyle
from personaut.simulations.types import SimulationType
from tests.personaut.simulations.conftest import MockIndividual, MockSituation


class TestChatMessage:
    """Tests for ChatMessage dataclass."""

    def test_create_message(self) -> None:
        """Test creating a chat message."""
        message = ChatMessage(
            sender="Sarah",
            content="Hello!",
        )
        assert message.sender == "Sarah"
        assert message.content == "Hello!"
        assert message.action is None

    def test_message_with_action(self) -> None:
        """Test message with action."""
        message = ChatMessage(
            sender="Sarah",
            content="Hello!",
            action="waves hello",
        )
        assert message.action == "waves hello"

    def test_message_to_dict(self) -> None:
        """Test converting message to dictionary."""
        message = ChatMessage(
            sender="Sarah",
            content="Hello!",
        )
        data = message.to_dict()
        assert data["sender"] == "Sarah"
        assert data["content"] == "Hello!"
        assert "timestamp" in data


class TestLiveSimulation:
    """Tests for LiveSimulation class."""

    def test_create_live_simulation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test creating a live simulation."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        assert simulation.simulation_type == SimulationType.LIVE_CONVERSATION

    def test_default_style_is_json(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test default style is JSON."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        assert simulation.style == SimulationStyle.JSON

    def test_create_chat_session(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test creating a chat session."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()

        assert session is not None
        assert session.session_id.startswith("session_")

    def test_get_session_by_id(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test getting session by ID."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()

        retrieved = simulation.get_session(session.session_id)
        assert retrieved is session

    def test_get_nonexistent_session(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test getting non-existent session returns None."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )

        retrieved = simulation.get_session("nonexistent")
        assert retrieved is None


class TestChatSession:
    """Tests for ChatSession class."""

    def test_send_message(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test sending a message."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()

        response = session.send("Hello!")

        assert response is not None
        assert response.content
        assert len(session.messages) == 2  # User + AI response

    def test_send_action(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test sending an action."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()

        response = session.send_action("waves hello")

        assert response is not None
        assert len(session.messages) == 2

    def test_get_state(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test getting session state."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()
        session.send("Hello!")

        state = session.get_state()

        assert "session_id" in state
        assert "active" in state
        assert "message_count" in state
        assert state["message_count"] == 2

    def test_get_history(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test getting message history."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()
        session.send("Hello!")

        history = session.get_history()

        assert len(history) == 2
        assert isinstance(history[0], dict)

    def test_end_session(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test ending a session."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()

        session.end()

        assert not session._active
        assert session.ended_at is not None

    def test_send_after_end_raises(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test sending message after session ends raises error."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()
        session.end()

        with pytest.raises(RuntimeError, match="not active"):
            session.send("Hello!")


class TestSessionPersistence:
    """Tests for session save/load functionality."""

    def test_save_session(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test saving a session."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()
        session.send("Hello!")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "session.json"
            simulation.save_session(session, path)

            assert path.exists()
            data = json.loads(path.read_text())
            assert "session_id" in data
            assert "messages" in data

    def test_load_session(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test loading a session."""
        simulation = LiveSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.LIVE_CONVERSATION,
        )
        session = simulation.create_chat_session()
        session.send("Hello!")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "session.json"
            simulation.save_session(session, path)

            loaded = simulation.load_session(path)

            assert loaded.session_id == session.session_id
            assert len(loaded.messages) == len(session.messages)
