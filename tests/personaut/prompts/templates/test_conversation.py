"""Tests for ConversationTemplate."""

import pytest

from personaut.emotions.state import EmotionalState
from personaut.prompts.templates.conversation import ConversationTemplate
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


class TestConversationTemplate:
    """Tests for ConversationTemplate class."""

    @pytest.fixture
    def template(self) -> ConversationTemplate:
        """Create a template for testing."""
        return ConversationTemplate()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        """Create Sarah individual with emotions."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.6)
        state.change_emotion("hopeful", 0.4)

        traits = TraitProfile()
        traits.set_trait("warmth", 0.8)

        return MockIndividual("Sarah", state, traits)

    @pytest.fixture
    def mike(self) -> MockIndividual:
        """Create Mike individual."""
        return MockIndividual("Mike")

    @pytest.fixture
    def situation(self):
        """Create a test situation."""
        return create_situation(
            modality=Modality.IN_PERSON,
            description="Job interview",
            location="Corporate Office",
        )

    def test_render_basic(
        self,
        template: ConversationTemplate,
        sarah: MockIndividual,
    ) -> None:
        """Test basic prompt rendering."""
        prompt = template.render(sarah)
        assert "Sarah" in prompt
        assert "roleplaying" in prompt.lower()

    def test_render_includes_emotional_state(
        self,
        template: ConversationTemplate,
        sarah: MockIndividual,
    ) -> None:
        """Test that emotional state is included."""
        prompt = template.render(sarah)
        assert "anxious" in prompt.lower()

    def test_render_includes_personality(
        self,
        template: ConversationTemplate,
        sarah: MockIndividual,
    ) -> None:
        """Test that personality is included."""
        prompt = template.render(sarah)
        assert "personality" in prompt.lower() or "warm" in prompt.lower()

    def test_render_with_situation(
        self,
        template: ConversationTemplate,
        sarah: MockIndividual,
        situation,
    ) -> None:
        """Test rendering with situation."""
        prompt = template.render(sarah, situation=situation)
        assert "Corporate Office" in prompt

    def test_render_with_others(
        self,
        template: ConversationTemplate,
        sarah: MockIndividual,
        mike: MockIndividual,
    ) -> None:
        """Test rendering with other participants."""
        prompt = template.render(sarah, other_participants=[mike])
        assert "Mike" in prompt

    def test_render_includes_guidelines(
        self,
        template: ConversationTemplate,
        sarah: MockIndividual,
    ) -> None:
        """Test that guidelines are included."""
        prompt = template.render(sarah)
        assert "guideline" in prompt.lower() or "-" in prompt

    def test_custom_guidelines(
        self,
        template: ConversationTemplate,
        sarah: MockIndividual,
    ) -> None:
        """Test custom guidelines."""
        prompt = template.render(
            sarah,
            guidelines=["Be extra cautious"],
        )
        assert "cautious" in prompt.lower()

    def test_style_formal(self, sarah: MockIndividual) -> None:
        """Test formal style template."""
        template = ConversationTemplate(style="formal")
        prompt = template.render(sarah)
        assert "formal" in prompt.lower() or "professional" in prompt.lower()

    def test_style_casual(self, sarah: MockIndividual) -> None:
        """Test casual style template."""
        template = ConversationTemplate(style="casual")
        prompt = template.render(sarah)
        assert "casual" in prompt.lower() or "relaxed" in prompt.lower()

    def test_response_instruction(
        self,
        template: ConversationTemplate,
        sarah: MockIndividual,
    ) -> None:
        """Test that response instruction is included."""
        prompt = template.render(sarah)
        assert "respond as" in prompt.lower()
