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
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from personaut.simulations.simulation import Simulation
from personaut.simulations.styles import SimulationStyle


logger = logging.getLogger(__name__)


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

        if self.llm is None:
            logger.warning(
                "No LLM configured for survey simulation. "
                "Pass llm=, provider=, or model= to create_simulation() "
                "for content-aware survey responses. Falling back to placeholders."
            )

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

        # If an LLM is available, use it for content-aware responses
        if self.llm is not None:
            response_data = self._generate_llm_response(
                respondent=respondent,
                question=question,
                emotional_state=emotional_state,
            )
        elif question_type.startswith("likert"):
            # Fallback: generate based on emotional positivity
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

    _llm_warned: bool = False

    def _generate_llm_response(
        self,
        respondent: Any,
        question: dict[str, Any],
        emotional_state: Any,
    ) -> dict[str, Any]:
        """Generate a survey response using the LLM.

        Uses PromptManager to build a rich persona prompt, then appends
        question-specific format instructions so the LLM returns a
        correctly typed answer.

        Args:
            respondent: The individual responding.
            question: Question definition with id, text, type, etc.
            emotional_state: Respondent's emotional state.

        Returns:
            Response dictionary matching the question type.
        """
        from personaut.prompts.manager import PromptManager

        question_text = question.get("text", "")
        question_type = question.get("type", "open_ended")

        # Build rich persona prompt via PromptManager
        pm = PromptManager(default_template="survey")
        persona_prompt = pm.generate(
            individual=respondent,
            situation=self.situation,
            questions=[question_text],
            template="survey",
        )

        # Append question-type specific instructions
        if question_type.startswith("likert"):
            config = QUESTION_TYPES.get(question_type) or QUESTION_TYPES["likert_5"]
            min_val = config.get("min", 1)
            max_val = config.get("max", 5)
            instruction = (
                f"\n\nQuestion: {question_text}\n"
                f"Respond with a single integer from {min_val} to {max_val}. "
                f"Consider the question content and the persona's personality/emotional state. "
                f"Reply with ONLY the number, nothing else."
            )
        elif question_type == "yes_no":
            instruction = (
                f"\n\nQuestion: {question_text}\n"
                "Respond with ONLY 'Yes' or 'No' based on the persona's "
                "personality, emotional state, and the question content."
            )
        elif question_type == "multiple_choice":
            options = question.get("options", [])
            options_str = "\n".join(f"  {i + 1}. {opt}" for i, opt in enumerate(options))
            instruction = (
                f"\n\nQuestion: {question_text}\n"
                f"Options:\n{options_str}\n\n"
                "Respond with ONLY the exact text of the chosen option. "
                "Consider the persona's personality and emotional state."
            )
        else:
            # open_ended
            instruction = (
                f"\n\nQuestion: {question_text}\n"
                "Respond in character with 1-3 sentences. "
                "Your answer should reflect the persona's personality traits, "
                "emotional state, and relevant experiences. "
                "Reply with ONLY the answer, no preamble."
            )

        prompt = persona_prompt + instruction

        try:
            assert self.llm is not None
            result = self.llm.generate(prompt, temperature=0.7, max_tokens=256)
            raw = result.text.strip()
        except Exception as exc:
            logger.warning(
                "LLM generation failed for survey response, falling back to placeholder: %s",
                exc,
            )
            return self._generate_fallback_response(question, emotional_state)

        # Parse the raw LLM response into the correct format
        if question_type.startswith("likert"):
            return self._parse_likert_response(raw, question_type)
        elif question_type == "yes_no":
            return self._parse_yes_no_response(raw)
        elif question_type == "multiple_choice":
            options = question.get("options", [])
            return self._parse_multiple_choice_response(raw, options)
        else:
            return {"response": raw}

    def _parse_likert_response(self, raw: str, question_type: str) -> dict[str, Any]:
        """Parse an LLM response into a Likert value."""
        config = QUESTION_TYPES.get(question_type) or QUESTION_TYPES["likert_5"]
        min_val: int = int(config.get("min", 1))
        max_val: int = int(config.get("max", 5))
        labels: dict[int, str] = dict(config.get("labels", {}))

        # Extract the first integer from the response
        match = re.search(r"\d+", raw)
        if match:
            value = int(match.group())
            value = max(min_val, min(max_val, value))
        else:
            # If parsing fails, use midpoint
            value = round((max_val + min_val) / 2)

        return {
            "response": value,
            "response_label": labels.get(value, str(value)),
        }

    def _parse_yes_no_response(self, raw: str) -> dict[str, Any]:
        """Parse an LLM response into Yes/No."""
        lowered = raw.lower().strip()
        if lowered.startswith("yes"):
            return {"response": "Yes"}
        elif lowered.startswith("no"):
            return {"response": "No"}
        # Fallback: look for either word
        if "yes" in lowered:
            return {"response": "Yes"}
        return {"response": "No"}

    def _parse_multiple_choice_response(self, raw: str, options: list[str]) -> dict[str, Any]:
        """Parse an LLM response into one of the given options."""
        raw_lower = raw.lower().strip()
        # Exact match first
        for opt in options:
            if opt.lower() == raw_lower:
                return {"response": opt}
        # Substring match
        for opt in options:
            if opt.lower() in raw_lower:
                return {"response": opt}
        # Number match (e.g. "1" or "2")
        match = re.search(r"\d+", raw)
        if match:
            idx = int(match.group()) - 1
            if 0 <= idx < len(options):
                return {"response": options[idx]}
        # Default to first option
        return {"response": options[0] if options else None}

    def _generate_fallback_response(
        self,
        question: dict[str, Any],
        emotional_state: Any,
    ) -> dict[str, Any]:
        """Generate a fallback response when LLM fails."""
        question_type = question.get("type", "open_ended")
        if question_type.startswith("likert"):
            return self._generate_likert_response(question_type, emotional_state)
        elif question_type == "yes_no":
            return self._generate_yes_no_response(emotional_state)
        elif question_type == "multiple_choice":
            return self._generate_multiple_choice_response(question.get("options", []), emotional_state)
        return self._generate_open_response(question.get("text", ""), emotional_state)

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
        if dominant in ("anxious", "insecure", "helpless"):
            response = (
                "I'm not entirely sure, but I think things could be improved "
                "with more support and clearer communication."
            )
        elif dominant in ("content", "satisfied", "cheerful"):
            response = (
                "Overall, I'm quite satisfied with how things are going. "
                "There's always room for improvement, but I'm pleased with the progress."
            )
        elif dominant in ("angry", "hostile", "critical"):
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
            "content",
            "satisfied",
            "excited",
            "hopeful",
            "proud",
            "trusting",
            "appreciated",
            "respected",
            "cheerful",
            "energetic",
            "creative",
            "loving",
            "nurturing",
            "faithful",
        }
        negative_emotions = {
            "anxious",
            "angry",
            "depressed",
            "lonely",
            "guilty",
            "ashamed",
            "hurt",
            "hostile",
            "hateful",
            "insecure",
            "helpless",
            "rejected",
            "bored",
            "apathetic",
            "critical",
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
            "angry": "Anger may result in more critical feedback",
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
