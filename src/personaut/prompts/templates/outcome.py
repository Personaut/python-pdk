"""Outcome template for outcome analysis simulations.

This module provides the OutcomeTemplate class for generating prompts
that analyze potential outcomes given an individual's state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from personaut.prompts.templates.base import BaseTemplate


@dataclass
class OutcomeTemplate(BaseTemplate):
    """Template for outcome analysis prompts.

    Generates prompts that analyze how an individual would likely
    respond to or achieve a target outcome given their current state.

    Example:
        >>> template = OutcomeTemplate()
        >>> prompt = template.render(
        ...     individual=customer,
        ...     situation=sales_call,
        ...     target_outcome="Customer agrees to upgrade",
        ... )
    """

    def render(
        self,
        individual: Any,
        *,
        situation: Any | None = None,
        target_outcome: str | None = None,
        analysis_type: str = "likelihood",
        guidelines: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Render an outcome analysis prompt.

        Args:
            individual: The individual to analyze.
            situation: The situational context.
            target_outcome: The desired outcome to analyze.
            analysis_type: Type of analysis
                ("likelihood", "barriers", "approach").
            guidelines: Additional analysis guidelines.
            **kwargs: Additional template-specific options.

        Returns:
            Complete outcome analysis prompt.
        """
        name = self._get_name(individual)
        emotional_state = self._get_emotional_state(individual)
        traits = self._get_traits(individual)

        # Build sections
        sections = []

        # Analysis task
        sections.append(self._render_analysis_task(name, target_outcome))

        # Individual profile
        sections.append(f"## Individual: {name}")

        # Personality
        if traits:
            sections.append(self._render_personality(traits, name=name, style="list"))

        # Emotional state
        if emotional_state:
            sections.append(
                self._render_emotional_state(
                    emotional_state,
                    name=name,
                    highlight_dominant=True,
                )
            )

        # Situation
        if situation:
            from personaut.prompts.components.situation import SituationComponent

            sit_component = SituationComponent()
            sections.append(sit_component.format(situation, name=name))

        # Target outcome
        if target_outcome:
            sections.append(f"## Target Outcome\n{target_outcome}")

        # Analysis type instructions
        sections.append(self._render_analysis_instructions(analysis_type, name))

        # Guidelines
        if guidelines:
            sections.append(self._render_guidelines(guidelines))

        return self._join_sections(sections)

    def _render_analysis_task(
        self,
        name: str,
        target_outcome: str | None,
    ) -> str:
        """Render the analysis task description."""
        if target_outcome:
            return (
                f"Analyze how {name} would respond in this situation "
                f"and assess the likelihood of achieving the target outcome."
            )
        return (
            f"Analyze how {name} would likely respond in this situation based on their personality and emotional state."
        )

    def _render_analysis_instructions(
        self,
        analysis_type: str,
        name: str,
    ) -> str:
        """Render analysis-type-specific instructions."""
        instructions = {
            "likelihood": (
                "## Analysis Instructions\n"
                f"Assess the likelihood that {name} will achieve the target outcome.\n"
                "Consider:\n"
                "- How their personality traits influence their approach\n"
                "- How their emotional state affects their receptiveness\n"
                "- What barriers might prevent success\n"
                "- What factors favor success\n\n"
                "Provide a likelihood rating (Low/Medium/High) with explanation."
            ),
            "barriers": (
                "## Analysis Instructions\n"
                f"Identify potential barriers to {name} achieving the outcome.\n"
                "Consider:\n"
                "- Personality-based resistance\n"
                "- Emotional blockers\n"
                "- Situational challenges\n"
                "- Trust and relationship factors\n\n"
                "List barriers in order of significance."
            ),
            "approach": (
                "## Analysis Instructions\n"
                f"Recommend the best approach to help {name} achieve the outcome.\n"
                "Consider:\n"
                "- What communication style works best for their personality\n"
                "- How to address their current emotional state\n"
                "- What arguments or framings would resonate\n"
                "- What to avoid based on their traits\n\n"
                "Provide specific, actionable recommendations."
            ),
        }

        return instructions.get(
            analysis_type,
            f"## Analysis Instructions\nAnalyze {name}'s likely response.",
        )


__all__ = ["OutcomeTemplate"]
