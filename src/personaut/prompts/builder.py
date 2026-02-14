"""PromptBuilder for fluent prompt construction.

This module provides the PromptBuilder class that offers a fluent
interface for constructing prompts with fine-grained control.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from personaut.prompts.components.emotional_state import EmotionalStateComponent
from personaut.prompts.components.memory import MemoryComponent
from personaut.prompts.components.personality import PersonalityComponent
from personaut.prompts.components.relationship import RelationshipComponent
from personaut.prompts.components.situation import SituationComponent
from personaut.prompts.templates.base import BaseTemplate
from personaut.prompts.templates.conversation import ConversationTemplate
from personaut.prompts.templates.outcome import OutcomeTemplate
from personaut.prompts.templates.survey import SurveyTemplate


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.situations.situation import Situation
    from personaut.traits.profile import TraitProfile


# Default section order
DEFAULT_SECTION_ORDER = [
    "identity",
    "personality",
    "emotional_state",
    "relationships",
    "memories",
    "situation",
    "guidelines",
    "instruction",
]


# Template registry
TEMPLATES: dict[str, type[BaseTemplate]] = {
    "conversation": ConversationTemplate,
    "survey": SurveyTemplate,
    "outcome": OutcomeTemplate,
}


@dataclass
class PromptBuilder:
    """Fluent builder for constructing prompts.

    Provides fine-grained control over prompt assembly with a
    fluent interface for chaining configuration calls.

    Example:
        >>> builder = PromptBuilder()
        >>> prompt = (builder
        ...     .with_individual(sarah)
        ...     .with_emotional_state(sarah.emotional_state)
        ...     .with_traits(sarah.traits)
        ...     .with_situation(meeting)
        ...     .using_template("conversation")
        ...     .build()
        ... )
    """

    # Components
    _emotional_component: EmotionalStateComponent = field(default_factory=EmotionalStateComponent)
    _personality_component: PersonalityComponent = field(default_factory=PersonalityComponent)
    _memory_component: MemoryComponent = field(default_factory=MemoryComponent)
    _relationship_component: RelationshipComponent = field(default_factory=RelationshipComponent)
    _situation_component: SituationComponent = field(default_factory=SituationComponent)

    # Configuration (using post_init to set mutable defaults)
    _individual: Any = field(default=None, repr=False)
    _emotional_state: Any = field(default=None, repr=False)
    _traits: Any = field(default=None, repr=False)
    _situation: Any = field(default=None, repr=False)
    _memories: list[Any] = field(default_factory=list, repr=False)
    _relationships: list[Any] = field(default_factory=list, repr=False)
    _other_individuals: list[Any] = field(default_factory=list, repr=False)
    _guidelines: list[str] = field(default_factory=list, repr=False)
    _template_name: str = field(default="conversation")
    _section_ordering: list[str] = field(default_factory=list)
    _trust_level: float = field(default=1.0)

    def __post_init__(self) -> None:
        """Initialize section ordering."""
        if not self._section_ordering:
            self._section_ordering = list(DEFAULT_SECTION_ORDER)

    def with_individual(self, individual: Any) -> PromptBuilder:
        """Set the main individual for the prompt.

        Args:
            individual: The individual to roleplay as.

        Returns:
            Self for chaining.
        """
        self._individual = individual
        return self

    def with_emotional_state(
        self,
        emotional_state: EmotionalState,
    ) -> PromptBuilder:
        """Set the emotional state.

        Args:
            emotional_state: The emotional state to use.

        Returns:
            Self for chaining.
        """
        self._emotional_state = emotional_state
        return self

    def with_traits(self, traits: TraitProfile) -> PromptBuilder:
        """Set the personality traits.

        Args:
            traits: The trait profile to use.

        Returns:
            Self for chaining.
        """
        self._traits = traits
        return self

    def with_situation(self, situation: Situation | Any) -> PromptBuilder:
        """Set the situational context.

        Args:
            situation: The situation to describe.

        Returns:
            Self for chaining.
        """
        self._situation = situation
        return self

    def with_memories(
        self,
        memories: list[Any],
        *,
        trust_level: float = 1.0,
    ) -> PromptBuilder:
        """Set relevant memories.

        Args:
            memories: List of memory objects.
            trust_level: Trust level for filtering private memories.

        Returns:
            Self for chaining.
        """
        self._memories = list(memories)
        self._trust_level = trust_level
        return self

    def with_relationships(
        self,
        relationships: list[Any],
    ) -> PromptBuilder:
        """Set relationship context.

        Args:
            relationships: List of relationship objects.

        Returns:
            Self for chaining.
        """
        self._relationships = list(relationships)
        return self

    def with_others(self, others: list[Any]) -> PromptBuilder:
        """Set other individuals in the interaction.

        Args:
            others: List of other individuals.

        Returns:
            Self for chaining.
        """
        self._other_individuals = list(others)
        return self

    def with_guidelines(self, guidelines: list[str]) -> PromptBuilder:
        """Set behavioral guidelines.

        Args:
            guidelines: List of guideline strings.

        Returns:
            Self for chaining.
        """
        self._guidelines = list(guidelines)
        return self

    def using_template(self, template_name: str) -> PromptBuilder:
        """Set the template to use.

        Args:
            template_name: Name of template ("conversation", "survey", "outcome").

        Returns:
            Self for chaining.

        Raises:
            ValueError: If template name is not recognized.
        """
        if template_name not in TEMPLATES:
            valid = ", ".join(TEMPLATES.keys())
            msg = f"Unknown template: {template_name}. Valid: {valid}"
            raise ValueError(msg)

        self._template_name = template_name
        return self

    def section_order(self, order: list[str]) -> PromptBuilder:
        """Set custom section ordering.

        Args:
            order: List of section names in desired order.

        Returns:
            Self for chaining.
        """
        self._section_ordering = list(order)
        return self

    def build(self) -> str:
        """Build the final prompt string.

        Returns:
            Complete prompt string.

        Raises:
            ValueError: If no individual has been set.
        """
        if self._individual is None:
            msg = "Individual must be set. Call with_individual() first."
            raise ValueError(msg)

        # Get or create emotional state and traits from individual
        emotional_state = self._emotional_state
        if emotional_state is None and hasattr(self._individual, "emotional_state"):
            emotional_state = self._individual.emotional_state

        traits = self._traits
        if traits is None and hasattr(self._individual, "traits"):
            traits = self._individual.traits

        # Build using template
        template_cls = TEMPLATES[self._template_name]
        template = template_cls()

        # Use template's render method
        if isinstance(template, ConversationTemplate):
            return template.render(
                self._individual,
                other_participants=self._other_individuals or None,
                relationships=self._relationships or None,
                situation=self._situation,
                memories=self._memories or None,
                trust_level=self._trust_level,
                guidelines=self._guidelines or None,
            )
        elif isinstance(template, SurveyTemplate):
            return template.render(
                self._individual,
                guidelines=self._guidelines or None,
            )
        elif isinstance(template, OutcomeTemplate):
            return template.render(
                self._individual,
                situation=self._situation,
                guidelines=self._guidelines or None,
            )
        else:
            # Generic fallback
            return self._build_generic(emotional_state, traits)

    def _build_generic(
        self,
        emotional_state: Any,
        traits: Any,
    ) -> str:
        """Build prompt using ordered sections (fallback method)."""
        name = self._get_name(self._individual)
        sections = []

        for section in self._section_ordering:
            section_text = self._render_section(section, name, emotional_state, traits)
            if section_text:
                sections.append(section_text)

        return "\n\n".join(sections)

    def _render_section(
        self,
        section: str,
        name: str,
        emotional_state: Any,
        traits: Any,
    ) -> str:
        """Render a single section by name."""
        if section == "identity":
            return f"You are roleplaying as {name}."

        elif section == "personality" and traits:
            text = self._personality_component.format(traits, name=name)
            return f"## Personality\n{text}"

        elif section == "emotional_state" and emotional_state:
            text = self._emotional_component.format(emotional_state, name=name, highlight_dominant=True)
            return f"## Current Emotional State\n{text}"

        elif section == "relationships" and self._other_individuals:
            return self._relationship_component.format(
                self._individual,
                self._other_individuals,
                self._relationships,
            )

        elif section == "memories" and self._memories:
            return self._memory_component.format(
                self._memories,
                trust_level=self._trust_level,
                name=name,
            )

        elif section == "situation" and self._situation:
            return self._situation_component.format(self._situation, name=name)

        elif section == "guidelines" and self._guidelines:
            lines = ["## Behavioral Guidelines"]
            for g in self._guidelines:
                lines.append(f"- {g}")
            return "\n".join(lines)

        elif section == "instruction":
            return f"Respond as {name} would in this situation."

        return ""

    def _get_name(self, individual: Any) -> str:
        """Get name from individual object."""
        if hasattr(individual, "name"):
            return str(individual.name)
        if isinstance(individual, dict):
            return str(individual.get("name", "Unknown"))
        return "Unknown"

    def reset(self) -> PromptBuilder:
        """Reset all configuration to defaults.

        Returns:
            Self for chaining.
        """
        self._individual = None
        self._emotional_state = None
        self._traits = None
        self._situation = None
        self._memories = []
        self._relationships = []
        self._other_individuals = []
        self._guidelines = []
        self._template_name = "conversation"
        self._section_ordering = list(DEFAULT_SECTION_ORDER)
        self._trust_level = 1.0
        return self


__all__ = [
    "DEFAULT_SECTION_ORDER",
    "TEMPLATES",
    "PromptBuilder",
]
