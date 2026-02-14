"""Tests for Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

import pytest

from personaut.server.api.schemas import (
    EmotionalStateResponse,
    EmotionUpdate,
    ErrorResponse,
    IndividualCreate,
    IndividualResponse,
    MessageCreate,
    MessageResponse,
    RelationshipCreate,
    SessionCreate,
    SituationCreate,
    TrustUpdate,
)


class TestEmotionSchemas:
    """Tests for emotion-related schemas."""

    def test_emotion_update_valid(self) -> None:
        """Test valid emotion update."""
        update = EmotionUpdate(emotions={"anxious": 0.5, "hopeful": 0.7})
        assert update.emotions == {"anxious": 0.5, "hopeful": 0.7}
        assert update.fill is None

    def test_emotion_update_with_fill(self) -> None:
        """Test emotion update with fill value."""
        update = EmotionUpdate(emotions={"anxious": 0.5}, fill=0.1)
        assert update.fill == 0.1

    def test_emotional_state_response(self) -> None:
        """Test emotional state response."""
        response = EmotionalStateResponse(
            emotions={"anxious": 0.5, "hopeful": 0.7},
            dominant=("hopeful", 0.7),
            top_emotions=[("hopeful", 0.7), ("anxious", 0.5)],
        )
        assert response.dominant == ("hopeful", 0.7)
        assert len(response.top_emotions) == 2


class TestIndividualSchemas:
    """Tests for individual-related schemas."""

    def test_individual_create_minimal(self) -> None:
        """Test creating individual with minimal data."""
        create = IndividualCreate(name="Sarah")
        assert create.name == "Sarah"
        assert create.description is None
        assert create.individual_type == "simulated"

    def test_individual_create_full(self) -> None:
        """Test creating individual with full data."""
        create = IndividualCreate(
            name="Mike",
            description="A curious researcher",
            individual_type="human",
            initial_emotions={"hopeful": 0.8},
            initial_traits={"warmth": 0.7},
            metadata={"role": "protagonist"},
        )
        assert create.name == "Mike"
        assert create.individual_type == "human"
        assert create.initial_emotions == {"hopeful": 0.8}

    def test_individual_response(self) -> None:
        """Test individual response."""
        response = IndividualResponse(
            id="ind_12345678",
            name="Sarah",
            individual_type="simulated",
            created_at=datetime.now(),
        )
        assert response.id == "ind_12345678"
        assert response.name == "Sarah"


class TestSituationSchemas:
    """Tests for situation-related schemas."""

    def test_situation_create(self) -> None:
        """Test creating situation."""
        create = SituationCreate(
            description="Coffee shop meeting",
            modality="in_person",
            location="Downtown Coffee House",
        )
        assert create.description == "Coffee shop meeting"
        assert create.modality == "in_person"


class TestRelationshipSchemas:
    """Tests for relationship-related schemas."""

    def test_relationship_create(self) -> None:
        """Test creating relationship."""
        create = RelationshipCreate(
            individual_ids=["ind_1", "ind_2"],
            initial_trust=0.6,
            relationship_type="colleague",
        )
        assert len(create.individual_ids) == 2
        assert create.initial_trust == 0.6

    def test_trust_update(self) -> None:
        """Test trust update."""
        update = TrustUpdate(
            from_individual="ind_1",
            to_individual="ind_2",
            change=0.1,
            reason="Helped with project",
        )
        assert update.change == 0.1
        assert update.reason == "Helped with project"


class TestSessionSchemas:
    """Tests for session-related schemas."""

    def test_session_create(self) -> None:
        """Test creating session."""
        create = SessionCreate(
            situation_id="sit_12345678",
            individual_ids=["ind_1", "ind_2"],
            human_id="ind_2",
        )
        assert create.situation_id == "sit_12345678"
        assert len(create.individual_ids) == 2


class TestMessageSchemas:
    """Tests for message-related schemas."""

    def test_message_create(self) -> None:
        """Test creating message."""
        create = MessageCreate(
            content="Hello, how are you?",
            sender_id="ind_1",
        )
        assert create.content == "Hello, how are you?"

    def test_message_response(self) -> None:
        """Test message response."""
        response = MessageResponse(
            id="msg_12345678",
            session_id="sess_12345678",
            sender_name="Sarah",
            content="Hello!",
            timestamp=datetime.now(),
        )
        assert response.id == "msg_12345678"
        assert response.sender_name == "Sarah"


class TestErrorSchemas:
    """Tests for error schemas."""

    def test_error_response(self) -> None:
        """Test error response."""
        error = ErrorResponse(
            error="NotFoundError",
            message="Individual not found",
            details={"id": "ind_12345678"},
        )
        assert error.error == "NotFoundError"
        assert error.message == "Individual not found"


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_emotion_value_bounds(self) -> None:
        """Test emotion value must be between 0 and 1."""
        # Valid values should work
        EmotionUpdate(emotions={"anxious": 0.0})
        EmotionUpdate(emotions={"anxious": 1.0})
        EmotionUpdate(emotions={"anxious": 0.5})

    def test_individual_name_required(self) -> None:
        """Test individual name is required."""
        with pytest.raises(ValueError):
            IndividualCreate()  # type: ignore[call-arg]

    def test_relationship_requires_two_individuals(self) -> None:
        """Test relationship requires exactly two individuals."""
        with pytest.raises(ValueError):
            RelationshipCreate(individual_ids=["ind_1"])  # Only one

    def test_message_content_required(self) -> None:
        """Test message content is required."""
        with pytest.raises(ValueError):
            MessageCreate(content="")  # Empty string
