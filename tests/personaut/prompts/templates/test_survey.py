"""Tests for SurveyTemplate."""

import pytest

from personaut.emotions.state import EmotionalState
from personaut.prompts.templates.survey import SurveyTemplate
from personaut.traits.profile import TraitProfile


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


class TestSurveyTemplate:
    """Tests for SurveyTemplate class."""

    @pytest.fixture
    def template(self) -> SurveyTemplate:
        """Create a template for testing."""
        return SurveyTemplate()

    @pytest.fixture
    def respondent(self) -> MockIndividual:
        """Create a respondent individual."""
        state = EmotionalState()
        state.change_emotion("proud", 0.6)

        traits = TraitProfile()
        traits.set_trait("perfectionism", 0.8)

        return MockIndividual("Respondent", state, traits)

    @pytest.fixture
    def questions(self) -> list[str]:
        """Create test questions."""
        return [
            "How satisfied are you with your work?",
            "Do you feel valued by your team?",
        ]

    def test_render_basic(
        self,
        template: SurveyTemplate,
        respondent: MockIndividual,
    ) -> None:
        """Test basic survey prompt rendering."""
        prompt = template.render(respondent)
        assert "Respondent" in prompt
        assert "survey" in prompt.lower()

    def test_render_with_questions(
        self,
        template: SurveyTemplate,
        respondent: MockIndividual,
        questions: list[str],
    ) -> None:
        """Test rendering with questions."""
        prompt = template.render(respondent, questions=questions)
        assert "satisfied" in prompt.lower()
        assert "valued" in prompt.lower()

    def test_likert_format(
        self,
        template: SurveyTemplate,
        respondent: MockIndividual,
    ) -> None:
        """Test likert scale format instructions."""
        prompt = template.render(respondent, response_format="likert_scale")
        assert "1" in prompt or "scale" in prompt.lower()

    def test_open_ended_format(
        self,
        respondent: MockIndividual,
    ) -> None:
        """Test open-ended format instructions."""
        template = SurveyTemplate(response_format="open_ended")
        prompt = template.render(respondent)
        assert "open" in prompt.lower() or "thoughtful" in prompt.lower()

    def test_multiple_choice_format(
        self,
        respondent: MockIndividual,
    ) -> None:
        """Test multiple choice format instructions."""
        template = SurveyTemplate(response_format="multiple_choice")
        prompt = template.render(respondent)
        assert "select" in prompt.lower() or "choice" in prompt.lower()

    def test_includes_emotional_influence(
        self,
        template: SurveyTemplate,
        respondent: MockIndividual,
    ) -> None:
        """Test that emotional influence is noted."""
        # Make emotion stronger for it to appear
        respondent.emotional_state.change_emotion("proud", 0.8)
        prompt = template.render(respondent)
        # Should mention how emotions affect responses
        assert "proud" in prompt.lower() or "emotional" in prompt.lower()

    def test_includes_guidelines(
        self,
        template: SurveyTemplate,
        respondent: MockIndividual,
    ) -> None:
        """Test that guidelines are included."""
        prompt = template.render(respondent)
        assert "consistent" in prompt.lower() or "guideline" in prompt.lower()

    def test_custom_context(
        self,
        template: SurveyTemplate,
        respondent: MockIndividual,
    ) -> None:
        """Test custom survey context."""
        prompt = template.render(
            respondent,
            context="Annual employee satisfaction survey",
        )
        assert "Annual" in prompt or "satisfaction" in prompt.lower()
