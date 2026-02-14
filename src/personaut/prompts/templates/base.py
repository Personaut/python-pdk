"""Base template for prompt generation.

This module provides the BaseTemplate abstract class that defines
the interface for all prompt templates.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from personaut.prompts.components.emotional_state import EmotionalStateComponent
from personaut.prompts.components.personality import PersonalityComponent


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.traits.profile import TraitProfile


@dataclass
class BaseTemplate(ABC):
    """Abstract base class for prompt templates.

    Templates define the overall structure and tone of prompts for
    different simulation types. They use components to render
    individual sections and combine them into a complete prompt.

    Subclasses must implement the `render` method.

    Attributes:
        emotional_component: Component for emotional state formatting.
        personality_component: Component for personality formatting.

    Example:
        >>> class MyTemplate(BaseTemplate):
        ...     def render(self, **kwargs) -> str:
        ...         return "My custom prompt"
    """

    emotional_component: EmotionalStateComponent = field(default_factory=EmotionalStateComponent)
    personality_component: PersonalityComponent = field(default_factory=PersonalityComponent)

    @abstractmethod
    def render(self, individual: Any, **kwargs: Any) -> str:
        """Render the template into a complete prompt.

        Subclasses must implement this method to assemble components
        into a final prompt string.

        Args:
            individual: The individual to generate a prompt for.
            **kwargs: Template-specific arguments.

        Returns:
            Complete prompt string.
        """
        ...

    def _render_identity(
        self,
        individual: Any,
    ) -> str:
        """Render the identity section.

        Args:
            individual: The individual to describe.

        Returns:
            Identity section text.
        """
        name = self._get_name(individual)
        return f"You are roleplaying as {name}."

    def _render_personality(
        self,
        traits: TraitProfile | None,
        *,
        name: str = "They",
        style: str = "narrative",
    ) -> str:
        """Render the personality section.

        Args:
            traits: Trait profile to describe.
            name: Name for the description.
            style: Formatting style.

        Returns:
            Personality section text.
        """
        if traits is None:
            return ""

        text = self.personality_component.format(traits, name=name, style=style)
        return f"## Personality\n{text}"

    def _render_emotional_state(
        self,
        emotional_state: EmotionalState | None,
        *,
        name: str = "They",
        highlight_dominant: bool = False,
    ) -> str:
        """Render the emotional state section.

        Args:
            emotional_state: Emotional state to describe.
            name: Name for the description.
            highlight_dominant: Whether to highlight dominant emotion.

        Returns:
            Emotional state section text.
        """
        if emotional_state is None:
            return ""

        text = self.emotional_component.format(
            emotional_state,
            name=name,
            highlight_dominant=highlight_dominant,
        )
        return f"## Current Emotional State\n{text}"

    def _render_guidelines(
        self,
        guidelines: list[str] | None = None,
    ) -> str:
        """Render behavioral guidelines section.

        Args:
            guidelines: List of behavioral guidelines.

        Returns:
            Guidelines section text.
        """
        if not guidelines:
            return ""

        lines = ["## Behavioral Guidelines"]
        for guideline in guidelines:
            lines.append(f"- {guideline}")

        return "\n".join(lines)

    def _render_response_instruction(
        self,
        name: str,
        instruction: str = "Respond as {name} would in this situation.",
    ) -> str:
        """Render the final response instruction.

        Args:
            name: Name of the individual.
            instruction: Instruction template.

        Returns:
            Response instruction text.
        """
        return instruction.format(name=name)

    def _get_name(self, individual: Any) -> str:
        """Get name from individual object."""
        if hasattr(individual, "name"):
            return str(individual.name)
        if isinstance(individual, dict):
            return str(individual.get("name", "Unknown"))
        return "Unknown"

    def _get_emotional_state(self, individual: Any) -> Any | None:
        """Get emotional state from individual object."""
        if hasattr(individual, "emotional_state"):
            return individual.emotional_state
        if isinstance(individual, dict):
            return individual.get("emotional_state")
        return None

    def _get_traits(self, individual: Any) -> Any | None:
        """Get trait profile from individual object."""
        if hasattr(individual, "traits"):
            return individual.traits
        if isinstance(individual, dict):
            return individual.get("traits")
        return None

    def _join_sections(self, sections: list[str]) -> str:
        """Join sections with double newlines, filtering empty ones."""
        non_empty = [s for s in sections if s.strip()]
        return "\n\n".join(non_empty)


__all__ = ["BaseTemplate"]
