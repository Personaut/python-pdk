"""Extended tests for PromptBuilder — targeting uncovered branches and methods."""

from __future__ import annotations

import pytest

from personaut.emotions.state import EmotionalState
from personaut.prompts.builder import DEFAULT_SECTION_ORDER, PromptBuilder
from personaut.situations.situation import create_situation
from personaut.traits.profile import TraitProfile
from personaut.types.modality import Modality


class MockIndividual:
    """Mock individual for testing."""

    def __init__(
        self,
        name: str,
        emotional_state: EmotionalState | None = None,
        traits: TraitProfile | None = None,
    ) -> None:
        self.id = f"{name.lower()}-1"
        self.name = name
        self.emotional_state = emotional_state or EmotionalState()
        self.traits = traits or TraitProfile()


class MockMemory:
    """Mock memory for testing."""

    def __init__(self, description: str = "Test memory") -> None:
        self.description = description
        self.memory_type = "individual"
        self.emotional_state = None


class MockRelationship:
    """Mock relationship for testing."""

    def __init__(self, trust: float = 0.5) -> None:
        self.trust_level = trust
        self.members = ["person_a", "person_b"]


class TestPromptBuilderWithMemories:
    """Tests for with_memories method."""

    @pytest.fixture
    def builder(self) -> PromptBuilder:
        return PromptBuilder()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        state = EmotionalState()
        state.change_emotion("anxious", 0.6)
        traits = TraitProfile()
        traits.set_trait("warmth", 0.8)
        return MockIndividual("Sarah", state, traits)

    def test_with_memories_sets_memories(self, builder: PromptBuilder, sarah: MockIndividual) -> None:
        """with_memories should store the memory list."""
        memories = [MockMemory("Memory 1"), MockMemory("Memory 2")]
        builder.with_individual(sarah).with_memories(memories)
        assert len(builder._memories) == 2

    def test_with_memories_sets_trust_level(self, builder: PromptBuilder, sarah: MockIndividual) -> None:
        """with_memories should store trust level."""
        memories = [MockMemory()]
        builder.with_individual(sarah).with_memories(memories, trust_level=0.7)
        assert builder._trust_level == 0.7

    def test_with_memories_returns_self(self, builder: PromptBuilder, sarah: MockIndividual) -> None:
        """with_memories should return self for chaining."""
        result = builder.with_individual(sarah).with_memories([])
        assert result is builder


class TestPromptBuilderWithRelationships:
    """Tests for with_relationships method."""

    @pytest.fixture
    def builder(self) -> PromptBuilder:
        return PromptBuilder()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        return MockIndividual("Sarah")

    def test_with_relationships_sets_list(self, builder: PromptBuilder, sarah: MockIndividual) -> None:
        """with_relationships should store the relationship list."""
        rels = [MockRelationship(), MockRelationship(0.9)]
        builder.with_individual(sarah).with_relationships(rels)
        assert len(builder._relationships) == 2

    def test_with_relationships_returns_self(self, builder: PromptBuilder, sarah: MockIndividual) -> None:
        """with_relationships should return self for chaining."""
        result = builder.with_individual(sarah).with_relationships([])
        assert result is builder


class TestPromptBuilderWithOthers:
    """Tests for with_others method."""

    @pytest.fixture
    def builder(self) -> PromptBuilder:
        return PromptBuilder()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        return MockIndividual("Sarah")

    def test_with_others_sets_list(self, builder: PromptBuilder, sarah: MockIndividual) -> None:
        """with_others should store the other individuals list."""
        mike = MockIndividual("Mike")
        builder.with_individual(sarah).with_others([mike])
        assert len(builder._other_individuals) == 1

    def test_with_others_returns_self(self, builder: PromptBuilder, sarah: MockIndividual) -> None:
        """with_others should return self for chaining."""
        result = builder.with_individual(sarah).with_others([])
        assert result is builder


class TestPromptBuilderSectionOrder:
    """Tests for section_order method."""

    @pytest.fixture
    def builder(self) -> PromptBuilder:
        return PromptBuilder()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        return MockIndividual("Sarah")

    def test_default_section_order(self, builder: PromptBuilder) -> None:
        """Default builder should have DEFAULT_SECTION_ORDER."""
        assert builder._section_ordering == list(DEFAULT_SECTION_ORDER)

    def test_custom_section_order(self, builder: PromptBuilder) -> None:
        """section_order should override ordering."""
        custom = ["situation", "identity"]
        builder.section_order(custom)
        assert builder._section_ordering == custom

    def test_section_order_returns_self(self, builder: PromptBuilder) -> None:
        """section_order should return self for chaining."""
        result = builder.section_order([])
        assert result is builder


class TestPromptBuilderBuildBranches:
    """Tests for build method template branching."""

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        state = EmotionalState()
        state.change_emotion("proud", 0.8)
        traits = TraitProfile()
        traits.set_trait("warmth", 0.8)
        return MockIndividual("Sarah", state, traits)

    def test_build_survey_template(self, sarah: MockIndividual) -> None:
        """Build with survey template should produce survey-type prompt."""
        builder = PromptBuilder()
        prompt = builder.with_individual(sarah).using_template("survey").build()
        assert "survey" in prompt.lower()

    def test_build_outcome_template(self, sarah: MockIndividual) -> None:
        """Build with outcome template should produce outcome-type prompt."""
        builder = PromptBuilder()
        situation = create_situation(
            modality=Modality.IN_PERSON,
            description="Job interview",
        )
        prompt = builder.with_individual(sarah).with_situation(situation).using_template("outcome").build()
        assert "analyze" in prompt.lower() or "outcome" in prompt.lower()

    def test_build_conversation_with_others(self, sarah: MockIndividual) -> None:
        """Build conversation with other participants."""
        mike = MockIndividual("Mike")
        builder = PromptBuilder()
        prompt = builder.with_individual(sarah).with_others([mike]).using_template("conversation").build()
        assert "Sarah" in prompt

    def test_build_uses_individual_emotional_state_if_none_set(self, sarah: MockIndividual) -> None:
        """Build should use individual's emotional_state if none explicitly set."""
        builder = PromptBuilder()
        prompt = builder.with_individual(sarah).build()
        # Should not crash, and should include identity
        assert "Sarah" in prompt


class TestPromptBuilderGetName:
    """Tests for _get_name method."""

    @pytest.fixture
    def builder(self) -> PromptBuilder:
        return PromptBuilder()

    def test_get_name_from_object(self, builder: PromptBuilder) -> None:
        """Should get name from object with name attribute."""
        individual = MockIndividual("Alice")
        assert builder._get_name(individual) == "Alice"

    def test_get_name_from_dict(self, builder: PromptBuilder) -> None:
        """Should get name from dict."""
        assert builder._get_name({"name": "Bob"}) == "Bob"

    def test_get_name_from_dict_missing(self, builder: PromptBuilder) -> None:
        """Should return 'Unknown' for dict without name."""
        assert builder._get_name({}) == "Unknown"

    def test_get_name_from_unknown_type(self, builder: PromptBuilder) -> None:
        """Should return 'Unknown' for unsupported type."""
        assert builder._get_name(42) == "Unknown"


class TestPromptBuilderFull:
    """Tests for full prompt building with all components."""

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        state = EmotionalState()
        state.change_emotion("proud", 0.8)
        traits = TraitProfile()
        traits.set_trait("warmth", 0.8)
        return MockIndividual("Sarah", state, traits)

    def test_full_chain(self, sarah: MockIndividual) -> None:
        """Full fluent chain should produce complete prompt."""
        situation = create_situation(
            modality=Modality.IN_PERSON,
            description="Office meeting",
        )
        mike = MockIndividual("Mike")
        builder = PromptBuilder()
        prompt = (
            builder.with_individual(sarah)
            .with_emotional_state(sarah.emotional_state)
            .with_traits(sarah.traits)
            .with_situation(situation)
            .with_others([mike])
            .with_guidelines(["Be professional", "Stay on topic"])
            .using_template("conversation")
            .build()
        )
        assert "Sarah" in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_reset_clears_everything(self) -> None:
        """Reset should clear all configuration."""
        builder = PromptBuilder()
        sarah = MockIndividual("Sarah")
        builder.with_individual(sarah).with_guidelines(["Test"])
        builder.reset()

        assert builder._individual is None
        assert builder._emotional_state is None
        assert builder._traits is None
        assert builder._situation is None
        assert builder._memories == []
        assert builder._relationships == []
        assert builder._other_individuals == []
        assert builder._guidelines == []
        assert builder._template_name == "conversation"
        assert builder._trust_level == 1.0
