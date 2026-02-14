"""Survey simulation for Personaut PDK.

This module provides the SurveySimulation class for generating
questionnaire responses from individuals.

Example:
    >>> from personaut.simulations.survey import SurveySimulation
    >>> simulation = SurveySimulation(
    ...     situation=survey_situation,
    ...     individuals=[respondent],
    ...     simulation_type=SimulationType.SURVEY,
    ...     questions=survey_questions,
    ... )
    >>> results = simulation.run(num=5, dir="./")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from personaut.simulations.simulation import Simulation
from personaut.simulations.styles import SimulationStyle


# Question type configurations
QUESTION_TYPES: dict[str, dict[str, Any]] = {
    "likert_5": {
        "min": 1,
        "max": 5,
        "labels": {
            1: "Strongly Disagree",
            2: "Disagree",
            3: "Neutral",
            4: "Agree",
            5: "Strongly Agree",
        },
    },
    "likert_7": {
        "min": 1,
        "max": 7,
        "labels": {
            1: "Strongly Disagree",
            2: "Disagree",
            3: "Somewhat Disagree",
            4: "Neutral",
            5: "Somewhat Agree",
            6: "Agree",
            7: "Strongly Agree",
        },
    },
    "likert_10": {
        "min": 1,
        "max": 10,
        "labels": {},  # No labels for 10-point scale
    },
    "yes_no": {
        "options": ["Yes", "No"],
    },
    "multiple_choice": {
        "options": [],  # Defined per question
    },
    "open_ended": {
        "max_length": 1000,
    },
}


@dataclass
class SurveySimulation(Simulation):
    """Simulation for questionnaire/survey responses.

    Generates realistic survey responses based on the respondent's
    emotional state and personality traits.

    Attributes:
        questions: List of question definitions.
        response_style: How to format responses ('verbose', 'concise').
        include_reasoning: Whether to include reasoning for responses.

    Example:
        >>> simulation = SurveySimulation(
        ...     situation=situation,
        ...     individuals=[respondent],
        ...     simulation_type=SimulationType.SURVEY,
        ...     questions=questions,
        ... )
    """

    questions: list[dict[str, Any]] = field(default_factory=list)
    response_style: str = "concise"
    include_reasoning: bool = True

    def _generate(self, run_index: int = 0, **options: Any) -> str:
        """Generate survey responses.

        Args:
            run_index: Index of this run (0-based).
            **options: Additional options.

        Returns:
            Formatted survey responses.
        """
        # Use first individual as respondent
        respondent = self.individuals[0] if self.individuals else None
        if respondent is None:
            return "Error: No respondent provided"

        questions = options.get("questions", self.questions)
        include_reasoning = options.get("include_reasoning", self.include_reasoning)

        # Generate responses for each question
        responses = []
        for question in questions:
            response = self._generate_response(
                respondent=respondent,
                question=question,
                include_reasoning=include_reasoning,
            )
            responses.append(response)

        # Format output
        return self._format_responses(respondent, responses)

    def _generate_response(
        self,
        respondent: Any,
        question: dict[str, Any],
        include_reasoning: bool = True,
    ) -> dict[str, Any]:
        """Generate a response for a single question.

        Args:
            respondent: The individual responding.
            question: Question definition.
            include_reasoning: Whether to include reasoning.

        Returns:
            Response dictionary.
        """
        question_id = question.get("id", "q")
        question_text = question.get("text", "")
        question_type = question.get("type", "open_ended")

        # Get emotional influence
        emotional_state = self._get_emotional_state(respondent)
        dominant_emotion = self._get_dominant_emotion(emotional_state)
        emotional_influence = self._get_emotional_influence(dominant_emotion)

        # Generate response based on type
        if question_type.startswith("likert"):
            response_data = self._generate_likert_response(
                question_type=question_type,
                emotional_state=emotional_state,
            )
        elif question_type == "yes_no":
            response_data = self._generate_yes_no_response(
                emotional_state=emotional_state,
            )
        elif question_type == "multiple_choice":
            response_data = self._generate_multiple_choice_response(
                options=question.get("options", []),
                emotional_state=emotional_state,
            )
        else:
            response_data = self._generate_open_response(
                question_text=question_text,
                emotional_state=emotional_state,
            )

        result = {
            "question_id": question_id,
            "question": question_text,
            **response_data,
        }

        if include_reasoning:
            result["emotional_influence"] = emotional_influence

        return result

    def _generate_likert_response(
        self,
        question_type: str,
        emotional_state: Any,
    ) -> dict[str, Any]:
        """Generate a Likert scale response.

        Args:
            question_type: Type of Likert scale.
            emotional_state: Respondent's emotional state.

        Returns:
            Response dictionary with value and label.
        """
        config = QUESTION_TYPES.get(question_type) or QUESTION_TYPES["likert_5"]
        min_val: int = int(config.get("min", 1))
        max_val: int = int(config.get("max", 5))
        labels: dict[int, str] = dict(config.get("labels", {}))

        # Generate value based on emotional state
        # More positive emotions lead to more positive responses
        positivity = self._get_emotional_positivity(emotional_state)
        midpoint = (max_val + min_val) / 2

        # Adjust based on positivity (-1 to 1)
        adjustment = positivity * (max_val - midpoint) * 0.5
        value = round(midpoint + adjustment)
        value = max(min_val, min(max_val, value))  # Clamp to range

        return {
            "response": value,
            "response_label": labels.get(value, str(value)),
        }

    def _generate_yes_no_response(
        self,
        emotional_state: Any,
    ) -> dict[str, Any]:
        """Generate a yes/no response.

        Args:
            emotional_state: Respondent's emotional state.

        Returns:
            Response dictionary.
        """
        positivity = self._get_emotional_positivity(emotional_state)
        response = "Yes" if positivity > 0 else "No"
        return {"response": response}

    def _generate_multiple_choice_response(
        self,
        options: list[str],
        emotional_state: Any,
    ) -> dict[str, Any]:
        """Generate a multiple choice response.

        Args:
            options: Available options.
            emotional_state: Respondent's emotional state.

        Returns:
            Response dictionary.
        """
        if not options:
            return {"response": None}

        # For now, select based on emotional positivity
        positivity = self._get_emotional_positivity(emotional_state)
        # Higher positivity tends toward later options (often more positive)
        index = int((positivity + 1) / 2 * (len(options) - 1))
        index = max(0, min(len(options) - 1, index))

        return {"response": options[index]}

    def _generate_open_response(
        self,
        question_text: str,
        emotional_state: Any,
    ) -> dict[str, Any]:
        """Generate an open-ended response.

        Args:
            question_text: The question being answered.
            emotional_state: Respondent's emotional state.

        Returns:
            Response dictionary.
        """
        dominant = self._get_dominant_emotion(emotional_state)

        # Generate a contextual placeholder response
        # In a real implementation, this would use the LLM
        if dominant in ("anxious", "insecure", "nervous"):
            response = (
                "I'm not entirely sure, but I think things could be improved "
                "with more support and clearer communication."
            )
        elif dominant in ("content", "satisfied", "happy"):
            response = (
                "Overall, I'm quite satisfied with how things are going. "
                "There's always room for improvement, but I'm pleased with the progress."
            )
        elif dominant in ("frustrated", "angry", "annoyed"):
            response = (
                "Honestly, there are several areas that need significant improvement. "
                "I'd like to see more attention to these issues."
            )
        else:
            response = (
                "I have mixed feelings about this. Some aspects are working well, while others could use attention."
            )

        return {"response": response}

    def _get_dominant_emotion(self, emotional_state: Any) -> str:
        """Get the dominant emotion from an emotional state.

        Args:
            emotional_state: Emotional state object.

        Returns:
            Name of the dominant emotion.
        """
        if emotional_state is None:
            return "neutral"

        if hasattr(emotional_state, "get_dominant"):
            dominant = emotional_state.get_dominant()
            return dominant[0] if dominant else "neutral"

        if isinstance(emotional_state, dict):
            if not emotional_state:
                return "neutral"
            result = max(emotional_state.items(), key=lambda x: x[1])[0]
            return str(result)

        return "neutral"

    def _get_emotional_positivity(self, emotional_state: Any) -> float:
        """Calculate overall emotional positivity.

        Args:
            emotional_state: Emotional state object.

        Returns:
            Value from -1 (very negative) to 1 (very positive).
        """
        if emotional_state is None:
            return 0.0

        positive_emotions = {
            "happy",
            "content",
            "satisfied",
            "excited",
            "hopeful",
            "proud",
            "trusting",
            "confident",
            "loved",
            "grateful",
            "cheerful",
            "energetic",
            "creative",
            "peaceful",
            "relaxed",
        }
        negative_emotions = {
            "sad",
            "anxious",
            "angry",
            "frustrated",
            "depressed",
            "fearful",
            "lonely",
            "guilty",
            "ashamed",
            "hurt",
            "hostile",
            "hateful",
            "insecure",
            "helpless",
            "rejected",
        }

        emotions = {}
        if hasattr(emotional_state, "to_dict"):
            emotions = emotional_state.to_dict()
        elif isinstance(emotional_state, dict):
            emotions = emotional_state

        positive_sum = sum(v for k, v in emotions.items() if k in positive_emotions)
        negative_sum = sum(v for k, v in emotions.items() if k in negative_emotions)

        total = positive_sum + negative_sum
        if total == 0:
            return 0.0

        return float((positive_sum - negative_sum) / total)

    def _get_emotional_influence(self, dominant_emotion: str) -> str:
        """Get a description of how emotion influences response.

        Args:
            dominant_emotion: The dominant emotion.

        Returns:
            Description of emotional influence.
        """
        influences = {
            "anxious": "Elevated anxiety may lead to more cautious responses",
            "content": "Contentment leads to more positive, balanced responses",
            "frustrated": "Frustration may result in more critical feedback",
            "hopeful": "Hopefulness promotes optimistic, forward-looking responses",
            "insecure": "Insecurity may lead to hedged or uncertain responses",
            "satisfied": "Satisfaction leads to affirming, stable responses",
            "neutral": "Neutral state leads to balanced, measured responses",
        }
        return influences.get(
            dominant_emotion,
            "Current emotional state may subtly influence responses",
        )

    def _format_responses(
        self,
        respondent: Any,
        responses: list[dict[str, Any]],
    ) -> str:
        """Format survey responses for output.

        Args:
            respondent: The respondent.
            responses: List of response dictionaries.

        Returns:
            Formatted output string.
        """
        if self.style == SimulationStyle.JSON:
            return self._format_json(respondent, responses)
        else:
            return self._format_questionnaire(respondent, responses)

    def _format_json(
        self,
        respondent: Any,
        responses: list[dict[str, Any]],
    ) -> str:
        """Format as JSON.

        Args:
            respondent: The respondent.
            responses: List of response dictionaries.

        Returns:
            JSON-formatted string.
        """
        emotional_state = self._get_emotional_state(respondent)
        emotions_dict: dict[str, Any] = {}
        if emotional_state is not None and hasattr(emotional_state, "to_dict"):
            emotions_dict = emotional_state.to_dict()
        elif isinstance(emotional_state, dict):
            emotions_dict = emotional_state

        output = {
            "simulation_id": f"survey_{id(self)}",
            "respondent": {
                "name": self._get_individual_name(respondent),
                "emotional_state": emotions_dict,
            },
            "responses": responses,
        }
        return json.dumps(output, indent=2)

    def _format_questionnaire(
        self,
        respondent: Any,
        responses: list[dict[str, Any]],
    ) -> str:
        """Format as questionnaire style.

        Args:
            respondent: The respondent.
            responses: List of response dictionaries.

        Returns:
            Questionnaire-formatted string.
        """
        lines = [
            "=== Survey Responses ===",
            f"Respondent: {self._get_individual_name(respondent)}",
            f"Situation: {getattr(self.situation, 'description', 'Survey')}",
            "",
            "---",
            "",
        ]

        for i, response in enumerate(responses, 1):
            question = response.get("question", "Unknown question")
            answer = response.get("response", "No response")
            label = response.get("response_label", "")

            lines.append(f"Q{i}: {question}")

            if label:
                lines.append(f"A{i}: {answer} ({label})")
            else:
                lines.append(f"A{i}: {answer}")

            if "emotional_influence" in response:
                lines.append(f"    [Note: {response['emotional_influence']}]")

            lines.append("")

        return "\n".join(lines)


__all__ = ["QUESTION_TYPES", "SurveySimulation"]
