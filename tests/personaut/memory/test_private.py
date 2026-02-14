"""Tests for PrivateMemory class."""

from __future__ import annotations

import pytest

from personaut.memory import MemoryType, PrivateMemory, create_private_memory


class TestPrivateMemory:
    """Tests for PrivateMemory class."""

    def test_create_private_memory(self) -> None:
        """Should create a private memory."""
        memory = PrivateMemory(
            owner_id="sarah_123",
            description="My secret",
            trust_threshold=0.7,
        )

        assert memory.owner_id == "sarah_123"
        assert memory.description == "My secret"
        assert memory.trust_threshold == 0.7
        assert memory.memory_type == MemoryType.PRIVATE

    def test_memory_type_forced_to_private(self) -> None:
        """Memory type should always be PRIVATE."""
        memory = PrivateMemory(description="Test", owner_id="test")

        assert memory.memory_type == MemoryType.PRIVATE

    def test_trust_threshold_validation(self) -> None:
        """Trust threshold must be between 0 and 1."""
        with pytest.raises(ValueError, match="Trust threshold must be between"):
            PrivateMemory(
                owner_id="test",
                description="Test",
                trust_threshold=1.5,
            )

        with pytest.raises(ValueError, match="Trust threshold must be between"):
            PrivateMemory(
                owner_id="test",
                description="Test",
                trust_threshold=-0.1,
            )

    def test_valid_trust_thresholds(self) -> None:
        """Valid threshold values should work."""
        low = PrivateMemory(owner_id="a", description="Low", trust_threshold=0.0)
        high = PrivateMemory(owner_id="b", description="High", trust_threshold=1.0)
        mid = PrivateMemory(owner_id="c", description="Mid", trust_threshold=0.5)

        assert low.trust_threshold == 0.0
        assert high.trust_threshold == 1.0
        assert mid.trust_threshold == 0.5

    def test_can_access_granted(self) -> None:
        """Should grant access when trust level sufficient."""
        memory = PrivateMemory(
            owner_id="sarah",
            description="Secret",
            trust_threshold=0.6,
        )

        assert memory.can_access(0.6) is True
        assert memory.can_access(0.7) is True
        assert memory.can_access(1.0) is True

    def test_can_access_denied(self) -> None:
        """Should deny access when trust level insufficient."""
        memory = PrivateMemory(
            owner_id="sarah",
            description="Secret",
            trust_threshold=0.6,
        )

        assert memory.can_access(0.5) is False
        assert memory.can_access(0.3) is False
        assert memory.can_access(0.0) is False

    def test_record_disclosure(self) -> None:
        """Should track disclosure count."""
        memory = PrivateMemory(
            owner_id="sarah",
            description="Secret",
        )

        assert memory.disclosure_count == 0

        memory.record_disclosure()
        assert memory.disclosure_count == 1

        memory.record_disclosure()
        memory.record_disclosure()
        assert memory.disclosure_count == 3

    def test_get_sensitivity_level(self) -> None:
        """Should return appropriate sensitivity descriptions."""
        extreme = PrivateMemory(owner_id="a", description="A", trust_threshold=0.95)
        high = PrivateMemory(owner_id="b", description="B", trust_threshold=0.7)
        moderate = PrivateMemory(owner_id="c", description="C", trust_threshold=0.5)
        mild = PrivateMemory(owner_id="d", description="D", trust_threshold=0.3)
        minimal = PrivateMemory(owner_id="e", description="E", trust_threshold=0.1)

        assert extreme.get_sensitivity_level() == "extremely sensitive"
        assert high.get_sensitivity_level() == "highly sensitive"
        assert moderate.get_sensitivity_level() == "moderately sensitive"
        assert mild.get_sensitivity_level() == "mildly sensitive"
        assert minimal.get_sensitivity_level() == "minimally sensitive"

    def test_belongs_to(self) -> None:
        """Should check ownership."""
        memory = PrivateMemory(
            owner_id="sarah_123",
            description="Personal",
        )

        assert memory.belongs_to("sarah_123") is True
        assert memory.belongs_to("mike_456") is False

    def test_add_tag(self) -> None:
        """Should add tags."""
        memory = PrivateMemory(
            owner_id="sarah",
            description="Secret",
        )

        memory.add_tag("childhood")
        memory.add_tag("trauma")
        memory.add_tag("childhood")  # Duplicate

        assert "childhood" in memory.tags
        assert "trauma" in memory.tags
        assert memory.tags.count("childhood") == 1  # No duplicate

    def test_has_tag(self) -> None:
        """Should check for tags."""
        memory = PrivateMemory(
            owner_id="sarah",
            description="Secret",
            tags=["childhood", "family"],
        )

        assert memory.has_tag("childhood") is True
        assert memory.has_tag("work") is False

    def test_to_dict(self) -> None:
        """Should include private-specific fields."""
        memory = PrivateMemory(
            owner_id="sarah_123",
            description="Secret",
            trust_threshold=0.8,
            tags=["personal"],
        )
        memory.record_disclosure()

        data = memory.to_dict()

        assert data["memory_type"] == "private"
        assert data["owner_id"] == "sarah_123"
        assert data["trust_threshold"] == 0.8
        assert data["disclosure_count"] == 1
        assert data["tags"] == ["personal"]

    def test_from_dict(self) -> None:
        """Should restore from dictionary."""
        data = {
            "id": "mem_private",
            "description": "Restored secret",
            "owner_id": "sarah_123",
            "trust_threshold": 0.85,
            "disclosure_count": 3,
            "tags": ["childhood", "trauma"],
        }

        memory = PrivateMemory.from_dict(data)

        assert memory.id == "mem_private"
        assert memory.owner_id == "sarah_123"
        assert memory.trust_threshold == 0.85
        assert memory.disclosure_count == 3
        assert memory.tags == ["childhood", "trauma"]


class TestCreatePrivateMemory:
    """Tests for create_private_memory factory."""

    def test_create_basic(self) -> None:
        """Should create with required fields."""
        memory = create_private_memory(
            owner_id="sarah_123",
            description="My secret",
        )

        assert memory.owner_id == "sarah_123"
        assert memory.description == "My secret"
        assert memory.trust_threshold == 0.5  # Default

    def test_create_with_trust_threshold(self) -> None:
        """Should create with specified threshold."""
        memory = create_private_memory(
            owner_id="sarah_123",
            description="Very private",
            trust_threshold=0.9,
        )

        assert memory.trust_threshold == 0.9

    def test_create_with_emotional_state(self) -> None:
        """Should create with emotional state."""
        from personaut.emotions.state import EmotionalState

        state = EmotionalState()
        state.change_emotion("anxious", 0.8)

        memory = create_private_memory(
            owner_id="sarah_123",
            description="Anxiety trigger",
            emotional_state=state,
        )

        assert memory.emotional_state is state

    def test_create_with_context(self) -> None:
        """Should create with situational context."""
        from personaut.facts import SituationalContext

        ctx = SituationalContext()
        ctx.add_location("venue_type", "hospital")

        memory = create_private_memory(
            owner_id="sarah_123",
            description="The diagnosis",
            context=ctx,
        )

        assert memory.context is ctx

    def test_create_with_tags(self) -> None:
        """Should create with tags."""
        memory = create_private_memory(
            owner_id="sarah_123",
            description="Childhood memory",
            tags=["childhood", "family", "trauma"],
        )

        assert memory.tags == ["childhood", "family", "trauma"]

    def test_create_with_metadata(self) -> None:
        """Should create with metadata."""
        memory = create_private_memory(
            owner_id="sarah_123",
            description="Secret",
            metadata={"source": "therapy"},
        )

        assert memory.metadata == {"source": "therapy"}
