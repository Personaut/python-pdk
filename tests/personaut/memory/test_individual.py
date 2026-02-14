"""Tests for IndividualMemory class."""

from __future__ import annotations

import pytest

from personaut.memory import IndividualMemory, MemoryType, create_individual_memory


class TestIndividualMemory:
    """Tests for IndividualMemory class."""

    def test_create_individual_memory(self) -> None:
        """Should create an individual memory."""
        memory = IndividualMemory(
            owner_id="sarah_123",
            description="My first day at work",
        )

        assert memory.owner_id == "sarah_123"
        assert memory.description == "My first day at work"
        assert memory.memory_type == MemoryType.INDIVIDUAL
        assert memory.salience == 0.5  # Default

    def test_memory_type_forced_to_individual(self) -> None:
        """Memory type should always be INDIVIDUAL."""
        # Even if we try to set a different type
        memory = IndividualMemory(
            owner_id="test",
            description="Test",
        )

        assert memory.memory_type == MemoryType.INDIVIDUAL

    def test_salience_validation(self) -> None:
        """Salience must be between 0 and 1."""
        with pytest.raises(ValueError, match="Salience must be between"):
            IndividualMemory(
                owner_id="test",
                description="Test",
                salience=1.5,
            )

        with pytest.raises(ValueError, match="Salience must be between"):
            IndividualMemory(
                owner_id="test",
                description="Test",
                salience=-0.1,
            )

    def test_valid_salience_values(self) -> None:
        """Valid salience values should work."""
        low = IndividualMemory(owner_id="a", description="Low", salience=0.0)
        high = IndividualMemory(owner_id="b", description="High", salience=1.0)
        mid = IndividualMemory(owner_id="c", description="Mid", salience=0.5)

        assert low.salience == 0.0
        assert high.salience == 1.0
        assert mid.salience == 0.5

    def test_belongs_to(self) -> None:
        """Should check ownership correctly."""
        memory = IndividualMemory(
            owner_id="sarah_123",
            description="Personal memory",
        )

        assert memory.belongs_to("sarah_123") is True
        assert memory.belongs_to("mike_456") is False

    def test_to_dict(self) -> None:
        """Should include individual-specific fields."""
        memory = IndividualMemory(
            owner_id="sarah_123",
            description="Test",
            salience=0.8,
        )

        data = memory.to_dict()

        assert data["owner_id"] == "sarah_123"
        assert data["salience"] == 0.8
        assert data["memory_type"] == "individual"

    def test_from_dict(self) -> None:
        """Should restore from dictionary."""
        data = {
            "id": "mem_test",
            "description": "Restored memory",
            "owner_id": "sarah_123",
            "salience": 0.9,
        }

        memory = IndividualMemory.from_dict(data)

        assert memory.id == "mem_test"
        assert memory.owner_id == "sarah_123"
        assert memory.salience == 0.9

    def test_from_dict_with_emotional_state(self) -> None:
        """Should restore with emotional state."""
        data = {
            "description": "Test",
            "owner_id": "test",
            "emotional_state": {"cheerful": 0.8},
        }

        memory = IndividualMemory.from_dict(data)

        assert memory.emotional_state is not None
        assert memory.emotional_state.get_emotion("cheerful") == 0.8

    def test_from_dict_with_context(self) -> None:
        """Should restore with situational context."""
        data = {
            "description": "Test",
            "owner_id": "test",
            "context": {
                "facts": [
                    {"category": "location", "key": "city", "value": "Miami"},
                ],
            },
        }

        memory = IndividualMemory.from_dict(data)

        assert memory.context is not None
        assert memory.get_context_value("city") == "Miami"


class TestCreateIndividualMemory:
    """Tests for create_individual_memory factory."""

    def test_create_basic(self) -> None:
        """Should create with required fields."""
        memory = create_individual_memory(
            owner_id="sarah_123",
            description="Test memory",
        )

        assert memory.owner_id == "sarah_123"
        assert memory.description == "Test memory"

    def test_create_with_emotional_state(self) -> None:
        """Should create with emotional state."""
        from personaut.emotions.state import EmotionalState

        state = EmotionalState()
        state.change_emotion("proud", 0.9)

        memory = create_individual_memory(
            owner_id="sarah_123",
            description="Got promoted",
            emotional_state=state,
        )

        assert memory.emotional_state is state

    def test_create_with_context(self) -> None:
        """Should create with situational context."""
        from personaut.facts import SituationalContext

        ctx = SituationalContext()
        ctx.add_location("venue_type", "office")

        memory = create_individual_memory(
            owner_id="sarah_123",
            description="Promotion announcement",
            context=ctx,
        )

        assert memory.context is ctx

    def test_create_with_salience(self) -> None:
        """Should create with specified salience."""
        memory = create_individual_memory(
            owner_id="sarah_123",
            description="Very important memory",
            salience=0.95,
        )

        assert memory.salience == 0.95

    def test_create_with_metadata(self) -> None:
        """Should create with metadata."""
        memory = create_individual_memory(
            owner_id="sarah_123",
            description="Tagged memory",
            metadata={"category": "work"},
        )

        assert memory.metadata == {"category": "work"}
