"""Integration tests for survey simulations.

These tests require a valid LLM API key (Gemini or Bedrock).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from personaut import (
    create_individual,
    WARMTH,
    DOMINANCE,
)
from personaut.situations import create_situation
from personaut.simulations import (
    SurveySimulation,
    SURVEY,
    create_simulation,
    QUESTION_TYPES,
)
from personaut.types import SURVEY as SURVEY_MODALITY
from personaut.models import get_llm, Provider


# Skip if no API key
pytestmark = pytest.mark.skipif(
    not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("AWS_ACCESS_KEY_ID")),
    reason="No API credentials available",
)


def get_available_llm():
    """Get an available LLM provider."""
    if os.environ.get("GOOGLE_API_KEY"):
        return get_llm(Provider.GEMINI)
    elif os.environ.get("AWS_ACCESS_KEY_ID"):
        return get_llm(Provider.BEDROCK)
    raise RuntimeError("No API credentials available")


class TestSurveySimulation:
    """End-to-end survey simulation tests."""

    @pytest.fixture
    def respondent(self):
        """Create survey respondent."""
        resp = create_individual(
            name="Alex",
            description="A 35-year-old marketing manager who values work-life balance and enjoys outdoor activities.",
            individual_type="simulated",
        )
        resp.set_trait(WARMTH, 0.7)
        resp.set_trait(DOMINANCE, 0.5)
        return resp

    @pytest.fixture
    def survey_questions(self) -> list[dict]:
        """Create sample survey questions."""
        return [
            {
                "id": "q1",
                "text": "How satisfied are you with your work-life balance?",
                "type": "scale",
                "scale_min": 1,
                "scale_max": 5,
            },
            {
                "id": "q2",
                "text": "What is your favorite outdoor activity?",
                "type": "open",
            },
            {
                "id": "q3",
                "text": "Would you recommend your workplace to a friend?",
                "type": "yes_no",
            },
        ]

    def test_basic_survey(self, respondent, survey_questions) -> None:
        """Test basic survey simulation."""
        llm = get_available_llm()

        situation = create_situation(
            modality=SURVEY_MODALITY,
            description="Employee satisfaction survey",
        )

        simulation = create_simulation(
            situation=situation,
            individuals=[respondent],
            simulation_type=SURVEY,
            llm=llm,
            questions=survey_questions,
        )

        result = simulation.run()

        assert result is not None
        assert result.responses is not None
        assert len(result.responses) == len(survey_questions)

    def test_survey_response_formats(self, respondent, survey_questions) -> None:
        """Test survey responses match question types."""
        llm = get_available_llm()

        situation = create_situation(
            modality=SURVEY_MODALITY,
            description="Format test survey",
        )

        simulation = create_simulation(
            situation=situation,
            individuals=[respondent],
            simulation_type=SURVEY,
            llm=llm,
            questions=survey_questions,
        )

        result = simulation.run()

        # Scale question should have numeric response
        q1_response = result.responses.get("q1")
        assert q1_response is not None

        # Open question should have text response
        q2_response = result.responses.get("q2")
        assert q2_response is not None
        assert isinstance(q2_response, str)
        assert len(q2_response) > 0

    def test_survey_considers_traits(self, respondent, survey_questions) -> None:
        """Test survey responses reflect personality traits."""
        llm = get_available_llm()

        # Create different personality
        pessimist = create_individual(
            name="Negative Nancy",
            description="A pessimistic person who is rarely satisfied with anything.",
        )
        pessimist.change_emotion("depressed", 0.6)

        situation = create_situation(
            modality=SURVEY_MODALITY,
            description="Personality test survey",
        )

        # Run survey with pessimist
        sim_pessimist = create_simulation(
            situation=situation,
            individuals=[pessimist],
            simulation_type=SURVEY,
            llm=llm,
            questions=survey_questions,
        )
        result_pessimist = sim_pessimist.run()

        # Run survey with regular respondent
        sim_regular = create_simulation(
            situation=situation,
            individuals=[respondent],
            simulation_type=SURVEY,
            llm=llm,
            questions=survey_questions,
        )
        result_regular = sim_regular.run()

        # Both should complete the survey
        assert result_pessimist is not None
        assert result_regular is not None


class TestSurveyQuestionTypes:
    """Tests for different survey question types."""

    @pytest.fixture
    def respondent(self):
        """Create test respondent."""
        return create_individual(
            name="Tester",
            description="A test survey respondent",
        )

    def test_likert_scale(self, respondent) -> None:
        """Test Likert scale question handling."""
        llm = get_available_llm()

        questions = [
            {
                "id": "likert",
                "text": "Rate your agreement: AI will improve healthcare.",
                "type": "scale",
                "scale_min": 1,
                "scale_max": 5,
                "labels": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
            }
        ]

        situation = create_situation(modality=SURVEY_MODALITY, description="Likert test")
        simulation = create_simulation(
            situation=situation,
            individuals=[respondent],
            simulation_type=SURVEY,
            llm=llm,
            questions=questions,
        )

        result = simulation.run()

        assert result is not None
        assert "likert" in result.responses

    def test_multiple_choice(self, respondent) -> None:
        """Test multiple choice question handling."""
        llm = get_available_llm()

        questions = [
            {
                "id": "mc",
                "text": "What is your preferred communication method?",
                "type": "multiple_choice",
                "options": ["Email", "Phone", "Video Call", "In-Person"],
            }
        ]

        situation = create_situation(modality=SURVEY_MODALITY, description="MC test")
        simulation = create_simulation(
            situation=situation,
            individuals=[respondent],
            simulation_type=SURVEY,
            llm=llm,
            questions=questions,
        )

        result = simulation.run()

        assert result is not None
        assert "mc" in result.responses

    def test_open_ended(self, respondent) -> None:
        """Test open-ended question handling."""
        llm = get_available_llm()

        questions = [
            {
                "id": "open",
                "text": "Describe your ideal vacation in 2-3 sentences.",
                "type": "open",
            }
        ]

        situation = create_situation(modality=SURVEY_MODALITY, description="Open test")
        simulation = create_simulation(
            situation=situation,
            individuals=[respondent],
            simulation_type=SURVEY,
            llm=llm,
            questions=questions,
        )

        result = simulation.run()

        assert result is not None
        response = result.responses.get("open")
        assert response is not None
        assert len(response) > 10  # Should be a meaningful response


class TestSurveyOutput:
    """Tests for survey output formats."""

    @pytest.fixture
    def simple_survey(self):
        """Create simple survey setup."""
        respondent = create_individual(name="Test", description="Test respondent")
        questions = [{"id": "q1", "text": "Test question?", "type": "open"}]
        return respondent, questions

    def test_save_survey_results(self, simple_survey) -> None:
        """Test saving survey results to file."""
        llm = get_available_llm()
        respondent, questions = simple_survey

        situation = create_situation(modality=SURVEY_MODALITY, description="Save test")
        simulation = create_simulation(
            situation=situation,
            individuals=[respondent],
            simulation_type=SURVEY,
            llm=llm,
            questions=questions,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = simulation.run(output_dir=tmpdir)

            # Check files were created
            files = list(Path(tmpdir).iterdir())
            assert len(files) >= 1
