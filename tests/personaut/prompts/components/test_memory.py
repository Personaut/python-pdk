"""Tests for MemoryComponent."""

import pytest

from personaut.prompts.components.memory import MemoryComponent


class MockMemory:
    """Mock memory for testing."""

    def __init__(
        self,
        description: str,
        memory_type: str = "individual",
        trust_threshold: float | None = None,
    ) -> None:
        self.description = description
        self.memory_type = memory_type
        self.trust_threshold = trust_threshold

    def get_trust_threshold(self) -> float | None:
        return self.trust_threshold


class TestMemoryComponent:
    """Tests for MemoryComponent class."""

    @pytest.fixture
    def component(self) -> MemoryComponent:
        """Create a component for testing."""
        return MemoryComponent()

    @pytest.fixture
    def memories(self) -> list[MockMemory]:
        """Create test memories."""
        return [
            MockMemory("First day at new job", "individual"),
            MockMemory("Successful project", "shared"),
            MockMemory("Private struggle", "private", trust_threshold=0.7),
        ]

    def test_format_empty_memories(
        self,
        component: MemoryComponent,
    ) -> None:
        """Test formatting with no memories."""
        text = component.format([])
        assert text == ""

    def test_format_memories(
        self,
        component: MemoryComponent,
        memories: list[MockMemory],
    ) -> None:
        """Test formatting memories."""
        text = component.format(memories, trust_level=1.0)
        assert "First day" in text
        assert "Successful project" in text
        assert "Private struggle" in text

    def test_trust_filtering(
        self,
        component: MemoryComponent,
        memories: list[MockMemory],
    ) -> None:
        """Test that private memories are filtered by trust."""
        # Low trust should exclude private memory
        text = component.format(memories, trust_level=0.5)
        assert "Private struggle" not in text
        assert "First day" in text

    def test_high_trust_includes_private(
        self,
        component: MemoryComponent,
        memories: list[MockMemory],
    ) -> None:
        """Test that high trust includes private memories."""
        text = component.format(memories, trust_level=0.8)
        assert "Private struggle" in text

    def test_custom_name(
        self,
        component: MemoryComponent,
        memories: list[MockMemory],
    ) -> None:
        """Test custom name in formatting."""
        text = component.format(memories, name="Sarah")
        assert "Sarah" in text

    def test_include_type(self, memories: list[MockMemory]) -> None:
        """Test including memory type in output."""
        component = MemoryComponent(include_type=True)
        text = component.format(memories, trust_level=1.0)
        assert "[individual]" in text or "[shared]" in text

    def test_max_memories(self, memories: list[MockMemory]) -> None:
        """Test limiting number of memories."""
        component = MemoryComponent(max_memories=2)
        text = component.format(memories, trust_level=1.0)
        # Should only include first 2
        lines = [l for l in text.split("\n") if l.startswith("-")]
        assert len(lines) <= 2

    def test_format_brief(
        self,
        component: MemoryComponent,
        memories: list[MockMemory],
    ) -> None:
        """Test brief format."""
        text = component.format_brief(memories)
        assert "3" in text or "relevant" in text

    def test_format_brief_empty(self, component: MemoryComponent) -> None:
        """Test brief format with no memories."""
        text = component.format_brief([])
        assert "no relevant" in text

    def test_dict_memory_format(self, component: MemoryComponent) -> None:
        """Test formatting dict-based memories."""
        memories = [
            {"description": "Dict memory", "memory_type": "individual"},
        ]
        text = component.format(memories)
        assert "Dict memory" in text
