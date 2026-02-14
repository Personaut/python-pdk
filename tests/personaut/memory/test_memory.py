"""Tests for Memory base class and MemoryType enum."""

from __future__ import annotations

from datetime import datetime

from personaut.memory import Memory, MemoryType, create_memory


class TestMemoryType:
    """Tests for MemoryType enum."""

    def test_all_types_defined(self) -> None:
        """All memory types should be defined."""
        assert MemoryType.INDIVIDUAL.value == "individual"
        assert MemoryType.SHARED.value == "shared"
        assert MemoryType.PRIVATE.value == "private"

    def test_type_descriptions(self) -> None:
        """Each type should have a description."""
        for memory_type in MemoryType:
            assert memory_type.description
            assert isinstance(memory_type.description, str)

    def test_requires_trust_check(self) -> None:
        """Only PRIVATE type should require trust check."""
        assert MemoryType.PRIVATE.requires_trust_check is True
        assert MemoryType.INDIVIDUAL.requires_trust_check is False
        assert MemoryType.SHARED.requires_trust_check is False


class TestMemory:
    """Tests for Memory base class."""

    def test_create_basic_memory(self) -> None:
        """Should create a memory with description."""
        memory = Memory(description="Test memory")

        assert memory.description == "Test memory"
        assert memory.id.startswith("mem_")
        assert memory.memory_type == MemoryType.INDIVIDUAL
        assert memory.emotional_state is None
        assert memory.context is None
        assert memory.embedding is None

    def test_memory_has_created_at(self) -> None:
        """Memory should have creation timestamp."""
        before = datetime.now()
        memory = Memory(description="Test")
        after = datetime.now()

        assert before <= memory.created_at <= after

    def test_memory_unique_ids(self) -> None:
        """Each memory should have a unique ID."""
        memory1 = Memory(description="First")
        memory2 = Memory(description="Second")

        assert memory1.id != memory2.id

    def test_to_embedding_text_basic(self) -> None:
        """Should generate embedding text from description."""
        memory = Memory(description="Met Sarah at the coffee shop")

        text = memory.to_embedding_text()

        assert "Met Sarah at the coffee shop" in text

    def test_to_embedding_text_with_emotional_state(self) -> None:
        """Should include emotional state in embedding text."""
        from personaut.emotions.state import EmotionalState

        state = EmotionalState()
        state.change_emotion("cheerful", 0.8)

        memory = Memory(
            description="Great day",
            emotional_state=state,
        )

        text = memory.to_embedding_text()

        assert "Great day" in text
        assert "cheerful" in text.lower()
        assert "high" in text.lower() or "very high" in text.lower()

    def test_to_embedding_text_with_context(self) -> None:
        """Should include situational context in embedding text."""
        from personaut.facts import SituationalContext

        ctx = SituationalContext()
        ctx.add_location("city", "Miami, FL")
        ctx.add_location("venue_type", "coffee shop")

        memory = Memory(
            description="Coffee date",
            context=ctx,
        )

        text = memory.to_embedding_text()

        assert "Coffee date" in text
        assert "Miami" in text
        assert "coffee shop" in text

    def test_get_context_value_with_context(self) -> None:
        """Should get values from context."""
        from personaut.facts import SituationalContext

        ctx = SituationalContext()
        ctx.add_location("city", "Miami, FL")

        memory = Memory(description="Test", context=ctx)

        assert memory.get_context_value("city") == "Miami, FL"
        assert memory.get_context_value("unknown") is None
        assert memory.get_context_value("unknown", "default") == "default"

    def test_get_context_value_without_context(self) -> None:
        """Should return default when no context."""
        memory = Memory(description="Test")

        assert memory.get_context_value("city") is None
        assert memory.get_context_value("city", "N/A") == "N/A"

    def test_has_context(self) -> None:
        """Should detect presence of context."""
        from personaut.facts import SituationalContext

        memory_no_ctx = Memory(description="Test")
        assert memory_no_ctx.has_context() is False

        empty_ctx = SituationalContext()
        memory_empty = Memory(description="Test", context=empty_ctx)
        assert memory_empty.has_context() is False

        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        memory_with = Memory(description="Test", context=ctx)
        assert memory_with.has_context() is True

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        memory = Memory(
            description="Test memory",
            metadata={"key": "value"},
        )

        data = memory.to_dict()

        assert data["id"] == memory.id
        assert data["description"] == "Test memory"
        assert data["memory_type"] == "individual"
        assert data["metadata"] == {"key": "value"}
        assert "created_at" in data

    def test_to_dict_with_emotional_state(self) -> None:
        """Should include emotional state in dict."""
        from personaut.emotions.state import EmotionalState

        state = EmotionalState()
        state.change_emotion("cheerful", 0.7)

        memory = Memory(description="Test", emotional_state=state)
        data = memory.to_dict()

        assert "emotional_state" in data
        assert data["emotional_state"]["cheerful"] == 0.7

    def test_to_dict_with_context(self) -> None:
        """Should include context in dict."""
        from personaut.facts import SituationalContext

        ctx = SituationalContext()
        ctx.add_location("city", "Miami")

        memory = Memory(description="Test", context=ctx)
        data = memory.to_dict()

        assert "context" in data

    def test_from_dict(self) -> None:
        """Should deserialize from dictionary."""
        data = {
            "id": "mem_test123",
            "description": "Restored memory",
            "memory_type": "individual",
            "created_at": "2024-01-15T10:30:00",
            "metadata": {"restored": True},
        }

        memory = Memory.from_dict(data)

        assert memory.id == "mem_test123"
        assert memory.description == "Restored memory"
        assert memory.memory_type == MemoryType.INDIVIDUAL
        assert memory.metadata == {"restored": True}

    def test_from_dict_with_emotional_state(self) -> None:
        """Should restore emotional state from dict."""
        data = {
            "description": "Test",
            "emotional_state": {"cheerful": 0.8, "excited": 0.6},
        }

        memory = Memory.from_dict(data)

        assert memory.emotional_state is not None
        assert memory.emotional_state.get_emotion("cheerful") == 0.8

    def test_from_dict_with_context(self) -> None:
        """Should restore context from dict."""
        data = {
            "description": "Test",
            "context": {
                "facts": [
                    {"category": "location", "key": "city", "value": "Miami"},
                ],
            },
        }

        memory = Memory.from_dict(data)

        assert memory.context is not None
        assert memory.get_context_value("city") == "Miami"

    def test_memory_repr(self) -> None:
        """Should have readable string representation."""
        memory = Memory(description="A short memory")
        repr_str = repr(memory)

        assert "Memory" in repr_str
        assert memory.id in repr_str
        assert "A short memory" in repr_str

    def test_memory_repr_truncates_long_description(self) -> None:
        """Should truncate long descriptions in repr."""
        long_desc = "A" * 100
        memory = Memory(description=long_desc)

        repr_str = repr(memory)

        assert "..." in repr_str
        assert len(repr_str) < 150


class TestCreateMemory:
    """Tests for create_memory factory function."""

    def test_create_basic(self) -> None:
        """Should create memory with defaults."""
        memory = create_memory(description="Test")

        assert memory.description == "Test"
        assert memory.memory_type == MemoryType.INDIVIDUAL

    def test_create_with_emotional_state(self) -> None:
        """Should create with emotional state."""
        from personaut.emotions.state import EmotionalState

        state = EmotionalState()
        state.change_emotion("cheerful", 0.8)

        memory = create_memory(
            description="Happy day",
            emotional_state=state,
        )

        assert memory.emotional_state is state

    def test_create_with_context(self) -> None:
        """Should create with situational context."""
        from personaut.facts import SituationalContext

        ctx = SituationalContext()
        ctx.add_location("city", "Miami")

        memory = create_memory(
            description="Miami trip",
            context=ctx,
        )

        assert memory.context is ctx

    def test_create_with_memory_type(self) -> None:
        """Should create with specified memory type."""
        memory = create_memory(
            description="Private thought",
            memory_type=MemoryType.PRIVATE,
        )

        assert memory.memory_type == MemoryType.PRIVATE

    def test_create_with_metadata(self) -> None:
        """Should create with metadata."""
        memory = create_memory(
            description="Tagged memory",
            metadata={"tags": ["important", "work"]},
        )

        assert memory.metadata == {"tags": ["important", "work"]}


class TestValueToIntensity:
    """Tests for value to intensity mapping."""

    def test_intensity_levels(self) -> None:
        """Should map values to correct intensity levels."""
        memory = Memory(description="Test")

        assert memory._value_to_intensity(0.9) == "very high"
        assert memory._value_to_intensity(0.8) == "very high"
        assert memory._value_to_intensity(0.7) == "high"
        assert memory._value_to_intensity(0.5) == "moderate"
        assert memory._value_to_intensity(0.3) == "mild"
        assert memory._value_to_intensity(0.1) == "minimal"
