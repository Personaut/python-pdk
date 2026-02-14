"""Tests for PromptBuilder."""

import pytest

from personaut.emotions.state import EmotionalState
from personaut.prompts.builder import TEMPLATES, PromptBuilder
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


class TestPromptBuilder:
    """Tests for PromptBuilder class."""

    @pytest.fixture
    def builder(self) -> PromptBuilder:
        """Create a builder for testing."""
        return PromptBuilder()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        """Create Sarah individual."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.6)

        traits = TraitProfile()
        traits.set_trait("warmth", 0.8)

        return MockIndividual("Sarah", state, traits)

    @pytest.fixture
    def situation(self):
        """Create a test situation."""
        return create_situation(
            modality=Modality.IN_PERSON,
            description="Meeting",
        )

    def test_build_requires_individual(self, builder: PromptBuilder) -> None:
        """Test that build requires an individual."""
        with pytest.raises(ValueError, match="Individual must be set"):
            builder.build()

    def test_basic_build(
        self,
        builder: PromptBuilder,
        sarah: MockIndividual,
    ) -> None:
        """Test basic prompt building."""
        prompt = builder.with_individual(sarah).build()
        assert "Sarah" in prompt

    def test_fluent_interface(
        self,
        builder: PromptBuilder,
        sarah: MockIndividual,
        situation,
    ) -> None:
        """Test fluent interface chaining."""
        prompt = builder.with_individual(sarah).with_situation(situation).build()
        assert "Sarah" in prompt
        assert "Situation" in prompt

    def test_with_emotional_state(
        self,
        builder: PromptBuilder,
        sarah: MockIndividual,
    ) -> None:
        """Test setting emotional state explicitly."""
        custom_state = EmotionalState()
        custom_state.change_emotion("proud", 0.9)

        # The builder stores the override
        builder.with_individual(sarah).with_emotional_state(custom_state)

        # Verify the override is stored
        assert builder._emotional_state is custom_state
        assert builder._emotional_state is not sarah.emotional_state

    def test_with_traits(
        self,
        builder: PromptBuilder,
        sarah: MockIndividual,
    ) -> None:
        """Test setting traits explicitly."""
        custom_traits = TraitProfile()
        custom_traits.set_trait("dominance", 0.9)

        prompt = builder.with_individual(sarah).with_traits(custom_traits).build()
        # Should use custom traits
        assert "personality" in prompt.lower()

    def test_with_guidelines(
        self,
        builder: PromptBuilder,
        sarah: MockIndividual,
    ) -> None:
        """Test setting guidelines."""
        prompt = builder.with_individual(sarah).with_guidelines(["Be extra helpful"]).build()
        assert "extra helpful" in prompt.lower()

    def test_using_template(
        self,
        builder: PromptBuilder,
        sarah: MockIndividual,
    ) -> None:
        """Test template selection."""
        prompt = builder.with_individual(sarah).using_template("survey").build()
        assert "survey" in prompt.lower()

    def test_invalid_template_raises(
        self,
        builder: PromptBuilder,
        sarah: MockIndividual,
    ) -> None:
        """Test that invalid template raises error."""
        with pytest.raises(ValueError, match="Unknown template"):
            builder.with_individual(sarah).using_template("invalid")

    def test_reset(
        self,
        builder: PromptBuilder,
        sarah: MockIndividual,
    ) -> None:
        """Test reset functionality."""
        builder.with_individual(sarah)
        builder.reset()

        with pytest.raises(ValueError, match="Individual must be set"):
            builder.build()

    def test_templates_registry(self) -> None:
        """Test that templates registry has expected templates."""
        assert "conversation" in TEMPLATES
        assert "survey" in TEMPLATES
        assert "outcome" in TEMPLATES
