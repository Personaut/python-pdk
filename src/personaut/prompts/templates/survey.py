"""Survey template for questionnaire simulations.

This module provides the SurveyTemplate class for generating prompts
that instruct individuals to respond to survey questions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from personaut.prompts.templates.base import BaseTemplate


@dataclass
class SurveyTemplate(BaseTemplate):
    """Template for survey response prompts.

    Generates prompts that instruct the LLM to respond to survey
    questions as an individual, considering their emotional state
    and personality traits.

    Attributes:
        response_format: Format for responses
            ("likert_scale", "open_ended", "multiple_choice").

    Example:
        >>> template = SurveyTemplate()
        >>> prompt = template.render(
        ...     individual=respondent,
        ...     questions=["How satisfied are you?"],
        ...     response_format="likert_scale",
        ... )
    """

    response_format: str = "likert_scale"

    def render(
        self,
        individual: Any,
        *,
        questions: list[str] | None = None,
        response_format: str | None = None,
        context: str | None = None,
        guidelines: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Render a survey prompt.

        Args:
            individual: The individual responding to the survey.
            questions: List of survey questions.
            response_format: Format for responses (overrides default).
            context: Additional context about the survey.
            guidelines: Additional behavioral guidelines.
            **kwargs: Additional template-specific options.

        Returns:
            Complete survey prompt.
        """
        name = self._get_name(individual)
        emotional_state = self._get_emotional_state(individual)
        traits = self._get_traits(individual)

        fmt = response_format or self.response_format

        # Build sections
        sections = []

        # Identity with survey context
        sections.append(self._render_survey_identity(individual))

        # Personality
        if traits:
            sections.append(self._render_personality(traits, name=name))

        # Emotional state
        if emotional_state:
            sections.append(self._render_emotional_state(emotional_state, name=name))
            # Add emotional influence note
            sections.append(self._render_emotional_influence(emotional_state, name))

        # Survey context
        if context:
            sections.append(f"## Survey Context\n{context}")

        # Response format instructions
        sections.append(self._render_format_instructions(fmt))

        # Questions
        if questions:
            sections.append(self._render_questions(questions))

        # Guidelines
        all_guidelines = self._generate_survey_guidelines(emotional_state, traits, guidelines)
        if all_guidelines:
            sections.append(self._render_guidelines(all_guidelines))

        # Response instruction
        sections.append(self._render_survey_instruction(name, fmt))

        return self._join_sections(sections)

    def _render_survey_identity(self, individual: Any) -> str:
        """Render identity section for survey context."""
        name = self._get_name(individual)
        return (
            f"You are roleplaying as {name} responding to a survey.\n"
            f"Answer the questions as {name} would, based on their "
            f"personality and current emotional state."
        )

    def _render_emotional_influence(
        self,
        emotional_state: Any,
        name: str,
    ) -> str:
        """Render note about emotional influence on responses."""
        if not emotional_state:
            return ""

        dominant = emotional_state.get_dominant()
        emotion, intensity = dominant

        if intensity < 0.3:
            return ""

        influence_map = {
            "anxious": "may lead to more cautious or uncertain responses",
            "confident": "may lead to more decisive, assured responses",
            "sad": "may lead to more negative or pessimistic responses",
            "cheerful": "may lead to more positive, optimistic responses",
            "frustrated": "may lead to more critical responses",
            "hopeful": "may lead to more optimistic responses",
        }

        influence = influence_map.get(
            emotion,
            f"the {emotion} feeling may influence response patterns",
        )

        return (
            f"Note: {name}'s current emotional state {influence}. "
            f"This should naturally affect how they answer questions."
        )

    def _render_format_instructions(self, response_format: str) -> str:
        """Render format-specific instructions."""
        format_instructions = {
            "likert_scale": (
                "## Response Format\n"
                "Respond to each question using a 5-point scale:\n"
                "1 = Strongly Disagree\n"
                "2 = Disagree\n"
                "3 = Neutral\n"
                "4 = Agree\n"
                "5 = Strongly Agree\n\n"
                "Provide your rating and a brief explanation for each."
            ),
            "open_ended": (
                "## Response Format\n"
                "Respond to each question with a thoughtful, open-ended answer.\n"
                "Be genuine and express thoughts as the individual would."
            ),
            "multiple_choice": (
                "## Response Format\n"
                "Select the best answer from the options provided.\n"
                "Briefly explain your reasoning for each choice."
            ),
        }

        return format_instructions.get(
            response_format,
            "## Response Format\nAnswer each question thoughtfully.",
        )

    def _render_questions(self, questions: list[str]) -> str:
        """Render the questions section."""
        lines = ["## Questions"]
        for i, question in enumerate(questions, 1):
            lines.append(f"{i}. {question}")
        return "\n".join(lines)

    def _generate_survey_guidelines(
        self,
        emotional_state: Any,
        traits: Any,
        custom_guidelines: list[str] | None,
    ) -> list[str]:
        """Generate survey-specific guidelines."""
        guidelines = [
            "Be consistent across related questions",
            "Let personality traits naturally influence response patterns",
        ]

        if emotional_state:
            dominant = emotional_state.get_dominant()
            if dominant[1] >= 0.5:
                guidelines.append(f"Let the {dominant[0]} feeling subtly influence responses")

        if custom_guidelines:
            guidelines.extend(custom_guidelines)

        return guidelines

    def _render_survey_instruction(
        self,
        name: str,
        response_format: str,
    ) -> str:
        """Render the survey-specific instruction."""
        if response_format == "likert_scale":
            return f"Answer each question as {name} would. Format: [Rating] - [Brief explanation]"
        elif response_format == "multiple_choice":
            return f"Select the answer that {name} would most likely choose and explain why."
        else:
            return f"Respond to each question as {name} would."


__all__ = ["SurveyTemplate"]
