"""Tests for SharedMemory class."""

from __future__ import annotations

from personaut.memory import MemoryType, SharedMemory, create_shared_memory


class TestSharedMemory:
    """Tests for SharedMemory class."""

    def test_create_shared_memory(self) -> None:
        """Should create a shared memory."""
        memory = SharedMemory(
            description="Team celebration",
            participant_ids=["alice", "bob", "carol"],
        )

        assert memory.description == "Team celebration"
        assert memory.memory_type == MemoryType.SHARED
        assert "alice" in memory.participant_ids
        assert "bob" in memory.participant_ids

    def test_memory_type_forced_to_shared(self) -> None:
        """Memory type should always be SHARED."""
        memory = SharedMemory(description="Test")

        assert memory.memory_type == MemoryType.SHARED

    def test_add_participant(self) -> None:
        """Should add participants."""
        memory = SharedMemory(description="Meeting")

        memory.add_participant("alice")
        memory.add_participant("bob")
        memory.add_participant("alice")  # Duplicate

        assert "alice" in memory.participant_ids
        assert "bob" in memory.participant_ids
        assert memory.participant_ids.count("alice") == 1  # No duplicate

    def test_set_perspective(self) -> None:
        """Should set individual perspectives."""
        memory = SharedMemory(
            description="The argument",
            participant_ids=["alice", "bob"],
        )

        memory.set_perspective("alice", "Bob was being unreasonable")
        memory.set_perspective("bob", "I was just trying to help")

        assert memory.perspectives["alice"] == "Bob was being unreasonable"
        assert memory.perspectives["bob"] == "I was just trying to help"

    def test_set_perspective_adds_participant(self) -> None:
        """Setting perspective should add participant if not present."""
        memory = SharedMemory(description="Event")

        memory.set_perspective("carol", "I enjoyed it")

        assert "carol" in memory.participant_ids
        assert memory.perspectives["carol"] == "I enjoyed it"

    def test_get_perspective(self) -> None:
        """Should retrieve perspectives."""
        memory = SharedMemory(
            description="Dinner",
            perspectives={"alice": "Great food"},
        )

        assert memory.get_perspective("alice") == "Great food"
        assert memory.get_perspective("bob") is None

    def test_set_emotional_state(self) -> None:
        """Should store individual emotional states."""
        from personaut.emotions.state import EmotionalState

        memory = SharedMemory(description="Event")

        alice_state = EmotionalState()
        alice_state.change_emotion("cheerful", 0.8)

        memory.set_emotional_state("alice", alice_state)

        assert "alice" in memory.emotional_states

    def test_get_emotional_state(self) -> None:
        """Should retrieve individual emotional states."""
        from personaut.emotions.state import EmotionalState

        memory = SharedMemory(description="Event")

        state = EmotionalState()
        state.change_emotion("excited", 0.9)
        memory.set_emotional_state("alice", state)

        retrieved = memory.get_emotional_state("alice")

        assert retrieved is not None
        assert retrieved.get_emotion("excited") == 0.9

    def test_get_emotional_state_not_found(self) -> None:
        """Should return None for unknown participant."""
        memory = SharedMemory(description="Event")

        assert memory.get_emotional_state("unknown") is None

    def test_is_participant(self) -> None:
        """Should check participation."""
        memory = SharedMemory(
            description="Meeting",
            participant_ids=["alice", "bob"],
        )

        assert memory.is_participant("alice") is True
        assert memory.is_participant("carol") is False

    def test_to_embedding_text_basic(self) -> None:
        """Should generate basic embedding text."""
        memory = SharedMemory(description="Group dinner")

        text = memory.to_embedding_text()

        assert "Group dinner" in text

    def test_to_embedding_text_with_perspective(self) -> None:
        """Should include perspective-specific text."""
        memory = SharedMemory(
            description="Team meeting",
            perspectives={"alice": "Very productive discussion"},
        )

        text = memory.to_embedding_text(perspective_id="alice")

        assert "Team meeting" in text
        assert "Very productive discussion" in text

    def test_to_embedding_text_with_perspective_emotional_state(self) -> None:
        """Should include perspective-specific emotional state."""
        from personaut.emotions.state import EmotionalState

        memory = SharedMemory(description="Event")

        state = EmotionalState()
        state.change_emotion("cheerful", 0.9)
        memory.set_emotional_state("alice", state)

        text = memory.to_embedding_text(perspective_id="alice")

        assert "cheerful" in text.lower()

    def test_to_dict(self) -> None:
        """Should include shared-specific fields."""
        memory = SharedMemory(
            description="Team event",
            participant_ids=["alice", "bob"],
            perspectives={"alice": "Great time"},
        )

        data = memory.to_dict()

        assert data["memory_type"] == "shared"
        assert data["participant_ids"] == ["alice", "bob"]
        assert data["perspectives"] == {"alice": "Great time"}

    def test_from_dict(self) -> None:
        """Should restore from dictionary."""
        data = {
            "id": "mem_shared",
            "description": "Restored event",
            "participant_ids": ["alice", "bob"],
            "perspectives": {"alice": "My view"},
            "emotional_states": {"alice": {"cheerful": 0.8}},
        }

        memory = SharedMemory.from_dict(data)

        assert memory.id == "mem_shared"
        assert memory.participant_ids == ["alice", "bob"]
        assert memory.perspectives["alice"] == "My view"


class TestCreateSharedMemory:
    """Tests for create_shared_memory factory."""

    def test_create_basic(self) -> None:
        """Should create with required fields."""
        memory = create_shared_memory(description="Team lunch")

        assert memory.description == "Team lunch"
        assert memory.memory_type == MemoryType.SHARED

    def test_create_with_participants(self) -> None:
        """Should create with participants."""
        memory = create_shared_memory(
            description="Meeting",
            participant_ids=["alice", "bob", "carol"],
        )

        assert len(memory.participant_ids) == 3

    def test_create_with_perspectives(self) -> None:
        """Should create with perspectives."""
        memory = create_shared_memory(
            description="Event",
            perspectives={
                "alice": "Loved it",
                "bob": "It was okay",
            },
        )

        assert memory.perspectives["alice"] == "Loved it"
        assert memory.perspectives["bob"] == "It was okay"

    def test_create_with_context(self) -> None:
        """Should create with situational context."""
        from personaut.facts import SituationalContext

        ctx = SituationalContext()
        ctx.add_location("venue_type", "restaurant")

        memory = create_shared_memory(
            description="Dinner",
            context=ctx,
        )

        assert memory.context is ctx
        assert memory.get_context_value("venue_type") == "restaurant"

    def test_create_with_emotional_state(self) -> None:
        """Should create with shared emotional state."""
        from personaut.emotions.state import EmotionalState

        state = EmotionalState()
        state.change_emotion("excited", 0.8)

        memory = create_shared_memory(
            description="Celebration",
            emotional_state=state,
        )

        assert memory.emotional_state is state
