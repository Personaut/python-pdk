"""Tests for OutcomeTemplate."""

import pytest

from personaut.emotions.state import EmotionalState
from personaut.prompts.templates.outcome import OutcomeTemplate
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


class TestOutcomeTemplate:
    """Tests for OutcomeTemplate class."""

    @pytest.fixture
    def template(self) -> OutcomeTemplate:
        """Create a template for testing."""
        return OutcomeTemplate()

    @pytest.fixture
    def customer(self) -> MockIndividual:
        """Create a customer individual."""
        state = EmotionalState()
        state.change_emotion("insecure", 0.6)

        traits = TraitProfile()
        traits.set_trait("vigilance", 0.8)

        return MockIndividual("Customer", state, traits)

    @pytest.fixture
    def situation(self):
        """Create a sales situation."""
        return create_situation(
            modality=Modality.PHONE_CALL,
            description="Sales call for product upgrade",
        )

    def test_render_basic(
        self,
        template: OutcomeTemplate,
        customer: MockIndividual,
    ) -> None:
        """Test basic outcome prompt rendering."""
        prompt = template.render(customer)
        assert "Customer" in prompt
        assert "analyze" in prompt.lower()

    def test_render_with_outcome(
        self,
        template: OutcomeTemplate,
        customer: MockIndividual,
    ) -> None:
        """Test rendering with target outcome."""
        prompt = template.render(
            customer,
            target_outcome="Customer agrees to upgrade",
        )
        assert "upgrade" in prompt.lower()

    def test_render_with_situation(
        self,
        template: OutcomeTemplate,
        customer: MockIndividual,
        situation,
    ) -> None:
        """Test rendering with situation."""
        prompt = template.render(customer, situation=situation)
        assert "phone" in prompt.lower() or "call" in prompt.lower()

    def test_likelihood_analysis(
        self,
        template: OutcomeTemplate,
        customer: MockIndividual,
    ) -> None:
        """Test likelihood analysis type."""
        prompt = template.render(
            customer,
            analysis_type="likelihood",
            target_outcome="Accept offer",
        )
        assert "likelihood" in prompt.lower()

    def test_barriers_analysis(
        self,
        template: OutcomeTemplate,
        customer: MockIndividual,
    ) -> None:
        """Test barriers analysis type."""
        prompt = template.render(
            customer,
            analysis_type="barriers",
            target_outcome="Accept offer",
        )
        assert "barrier" in prompt.lower()

    def test_approach_analysis(
        self,
        template: OutcomeTemplate,
        customer: MockIndividual,
    ) -> None:
        """Test approach analysis type."""
        prompt = template.render(
            customer,
            analysis_type="approach",
            target_outcome="Accept offer",
        )
        assert "approach" in prompt.lower() or "recommend" in prompt.lower()

    def test_includes_personality(
        self,
        template: OutcomeTemplate,
        customer: MockIndividual,
    ) -> None:
        """Test that personality is included."""
        prompt = template.render(customer)
        # Should include list-style personality
        assert "vigilance" in prompt.lower() or "-" in prompt

    def test_includes_emotional_state(
        self,
        template: OutcomeTemplate,
        customer: MockIndividual,
    ) -> None:
        """Test that emotional state is included."""
        prompt = template.render(customer)
        assert "emotional" in prompt.lower()
