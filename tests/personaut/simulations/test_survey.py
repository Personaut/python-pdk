"""Tests for survey simulation."""

from __future__ import annotations

import json

from personaut.simulations.styles import SimulationStyle
from personaut.simulations.survey import (
    QUESTION_TYPES,
    SurveySimulation,
)
from personaut.simulations.types import SimulationType
from tests.personaut.simulations.conftest import MockIndividual, MockSituation


class TestQuestionTypes:
    """Tests for QUESTION_TYPES configuration."""

    def test_likert_5_exists(self) -> None:
        """Test likert_5 configuration exists."""
        assert "likert_5" in QUESTION_TYPES
        assert QUESTION_TYPES["likert_5"]["min"] == 1
        assert QUESTION_TYPES["likert_5"]["max"] == 5

    def test_likert_7_exists(self) -> None:
        """Test likert_7 configuration exists."""
        assert "likert_7" in QUESTION_TYPES
        assert QUESTION_TYPES["likert_7"]["min"] == 1
        assert QUESTION_TYPES["likert_7"]["max"] == 7

    def test_likert_10_exists(self) -> None:
        """Test likert_10 configuration exists."""
        assert "likert_10" in QUESTION_TYPES
        assert QUESTION_TYPES["likert_10"]["min"] == 1
        assert QUESTION_TYPES["likert_10"]["max"] == 10

    def test_yes_no_exists(self) -> None:
        """Test yes_no configuration exists."""
        assert "yes_no" in QUESTION_TYPES
        assert QUESTION_TYPES["yes_no"]["options"] == ["Yes", "No"]

    def test_open_ended_exists(self) -> None:
        """Test open_ended configuration exists."""
        assert "open_ended" in QUESTION_TYPES


class TestSurveySimulation:
    """Tests for SurveySimulation class."""

    def test_create_survey_simulation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test creating a survey simulation."""
        questions = [
            {"id": "q1", "text": "How satisfied are you?", "type": "likert_5"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
            questions=questions,
        )
        assert simulation.simulation_type == SimulationType.SURVEY

    def test_default_style_is_questionnaire(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test default style is questionnaire."""
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
        )
        assert simulation.style == SimulationStyle.QUESTIONNAIRE

    def test_generate_likert_response(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test generating Likert scale response."""
        questions = [
            {"id": "q1", "text": "How satisfied are you?", "type": "likert_5"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
            questions=questions,
        )
        content = simulation._generate()

        # Should contain question and answer
        assert "Q1:" in content
        assert "A1:" in content

    def test_generate_yes_no_response(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test generating yes/no response."""
        questions = [
            {"id": "q1", "text": "Would you recommend?", "type": "yes_no"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
            questions=questions,
        )
        content = simulation._generate()

        # Should contain Yes or No
        assert "Yes" in content or "No" in content

    def test_generate_open_response(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test generating open-ended response."""
        questions = [
            {"id": "q1", "text": "Any comments?", "type": "open_ended"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
            questions=questions,
        )
        content = simulation._generate()

        assert "Q1:" in content

    def test_json_format(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test JSON format output."""
        questions = [
            {"id": "q1", "text": "Rate your experience", "type": "likert_5"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
            style=SimulationStyle.JSON,
            questions=questions,
        )
        content = simulation._generate()

        data = json.loads(content)
        assert "respondent" in data
        assert "responses" in data
        assert len(data["responses"]) == 1

    def test_include_reasoning(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test include_reasoning option."""
        questions = [
            {"id": "q1", "text": "How satisfied?", "type": "likert_5"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
            questions=questions,
            include_reasoning=True,
        )
        content = simulation._generate()

        # Should contain emotional influence note
        assert "[Note:" in content

    def test_multiple_questions(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test handling multiple questions."""
        questions = [
            {"id": "q1", "text": "Rate satisfaction", "type": "likert_5"},
            {"id": "q2", "text": "Would recommend?", "type": "yes_no"},
            {"id": "q3", "text": "Comments?", "type": "open_ended"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
            questions=questions,
        )
        content = simulation._generate()

        assert "Q1:" in content
        assert "Q2:" in content
        assert "Q3:" in content


class TestEmotionalPositivity:
    """Tests for emotional positivity calculations."""

    def test_positive_emotions_influence_responses(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test positive emotions lead to higher Likert scores."""
        questions = [
            {"id": "q1", "text": "Satisfaction?", "type": "likert_5"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.SURVEY,
            style=SimulationStyle.JSON,
            questions=questions,
        )
        content = simulation._generate()
        data = json.loads(content)

        # Sarah has positive emotions, should have higher-than-neutral score
        response = data["responses"][0]["response"]
        assert response >= 3  # Neutral or above

    def test_anxious_emotions_influence_responses(
        self,
        mock_situation: MockSituation,
        mock_individual_anxious: MockIndividual,
    ) -> None:
        """Test anxious emotions lead to lower Likert scores."""
        questions = [
            {"id": "q1", "text": "Satisfaction?", "type": "likert_5"},
        ]
        simulation = SurveySimulation(
            situation=mock_situation,
            individuals=[mock_individual_anxious],
            simulation_type=SimulationType.SURVEY,
            style=SimulationStyle.JSON,
            questions=questions,
        )
        content = simulation._generate()
        data = json.loads(content)

        # Anxious individual should have lower-than-neutral score
        response = data["responses"][0]["response"]
        assert response <= 3  # Neutral or below
