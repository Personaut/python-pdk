"""PromptManager for orchestrating prompt generation.

This module provides the PromptManager class that orchestrates
prompt generation for simulations with sensible defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from personaut.prompts.builder import PromptBuilder
from personaut.prompts.templates.conversation import ConversationTemplate
from personaut.prompts.templates.outcome import OutcomeTemplate
from personaut.prompts.templates.survey import SurveyTemplate


if TYPE_CHECKING:
    from personaut.situations.situation import Situation


@dataclass
class ValidationResult:
    """Result of prompt validation.

    Attributes:
        is_valid: Whether the prompt passed validation.
        errors: List of validation errors.
        warnings: List of validation warnings.
    """

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PromptManager:
    """Manager for orchestrating prompt generation.

    The PromptManager provides a high-level interface for generating
    prompts with sensible defaults, coordinating between templates
    and components.

    Attributes:
        intensity_threshold: Minimum emotion intensity to include.
        max_memories: Maximum memories to include in prompts.
        include_private_memories: Whether to include private memories.
        default_template: Default template name to use.
        include_guidelines: Whether to include behavioral guidelines.
        max_tokens: Approximate maximum prompt length.
        verbose: Whether to include debug information.

    Example:
        >>> manager = PromptManager()
        >>> prompt = manager.generate(individual, situation)
    """

    # Component settings
    intensity_threshold: float = 0.3
    max_memories: int = 5
    include_private_memories: bool = True

    # Template settings
    default_template: str = "conversation"
    include_guidelines: bool = True

    # Output settings
    max_tokens: int = 2000
    verbose: bool = False

    def generate(
        self,
        individual: Any,
        situation: Situation | Any | None = None,
        *,
        other_participants: list[Any] | None = None,
        relationships: list[Any] | None = None,
        memories: list[Any] | None = None,
        template: str | None = None,
        questions: list[str] | None = None,
        target_outcome: str | None = None,
        preview: bool = False,
        **overrides: Any,
    ) -> str:
        """Generate a prompt for the given individual and context.

        Args:
            individual: The individual to generate a prompt for.
            situation: The situational context.
            other_participants: Other individuals in the interaction.
            relationships: Relationships between participants.
            memories: Relevant memories to include.
            template: Template to use (overrides default).
            questions: Survey questions (for survey template).
            target_outcome: Target outcome (for outcome template).
            preview: If True, returns prompt without sending to model.
            **overrides: Override default settings for this generation.

        Returns:
            Complete prompt string.
        """
        template_name = template or self.default_template

        # Apply overrides
        overrides.get("intensity_threshold", self.intensity_threshold)
        max_mem = overrides.get("max_memories", self.max_memories)

        # Get trust level from relationships
        trust_level = self._calculate_trust_level(individual, other_participants, relationships)

        # Filter memories if needed
        filtered_memories = None
        if memories:
            filtered_memories = memories[:max_mem]

        # Generate using appropriate template
        if template_name == "conversation":
            prompt = self._generate_conversation(
                individual,
                situation=situation,
                other_participants=other_participants,
                relationships=relationships,
                memories=filtered_memories,
                trust_level=trust_level,
            )
        elif template_name == "survey":
            prompt = self._generate_survey(
                individual,
                questions=questions,
            )
        elif template_name == "outcome":
            prompt = self._generate_outcome(
                individual,
                situation=situation,
                target_outcome=target_outcome,
            )
        else:
            # Use builder for custom templates
            builder = PromptBuilder()
            builder.with_individual(individual)

            if situation:
                builder.with_situation(situation)
            if other_participants:
                builder.with_others(other_participants)
            if relationships:
                builder.with_relationships(relationships)
            if filtered_memories:
                builder.with_memories(filtered_memories, trust_level=trust_level)

            prompt = builder.using_template(template_name).build()

        # Validate and potentially truncate
        if not preview:
            validation = self.validate(prompt)
            if validation.warnings and self.verbose:
                for warning in validation.warnings:
                    print(f"Warning: {warning}")

        return prompt

    def _generate_conversation(
        self,
        individual: Any,
        *,
        situation: Any | None,
        other_participants: list[Any] | None,
        relationships: list[Any] | None,
        memories: list[Any] | None,
        trust_level: float,
    ) -> str:
        """Generate a conversation prompt."""
        template = ConversationTemplate()
        return template.render(
            individual,
            other_participants=other_participants,
            relationships=relationships,
            situation=situation,
            memories=memories,
            trust_level=trust_level,
        )

    def _generate_survey(
        self,
        individual: Any,
        *,
        questions: list[str] | None,
    ) -> str:
        """Generate a survey prompt."""
        template = SurveyTemplate()
        return template.render(
            individual,
            questions=questions,
        )

    def _generate_outcome(
        self,
        individual: Any,
        *,
        situation: Any | None,
        target_outcome: str | None,
    ) -> str:
        """Generate an outcome analysis prompt."""
        template = OutcomeTemplate()
        return template.render(
            individual,
            situation=situation,
            target_outcome=target_outcome,
        )

    def _calculate_trust_level(
        self,
        individual: Any,
        others: list[Any] | None,
        relationships: list[Any] | None,
    ) -> float:
        """Calculate average trust level with other participants."""
        if not others or not relationships:
            return 0.5  # Default neutral trust

        individual_id = self._get_id(individual)
        trust_levels = []

        for other in others:
            other_id = self._get_id(other)
            for rel in relationships:
                members = self._get_members(rel)
                if individual_id in members and other_id in members:
                    trust = self._get_trust(rel, individual_id)
                    trust_levels.append(trust)
                    break

        if not trust_levels:
            return 0.5

        return sum(trust_levels) / len(trust_levels)

    def _get_id(self, individual: Any) -> str:
        """Get ID from individual object."""
        if hasattr(individual, "id"):
            return str(individual.id)
        if isinstance(individual, dict):
            return str(individual.get("id", str(individual)))
        return str(individual)

    def _get_members(self, relationship: Any) -> list[str]:
        """Get member IDs from relationship object."""
        if hasattr(relationship, "members"):
            return [str(m) for m in relationship.members]
        if isinstance(relationship, dict):
            return [str(m) for m in relationship.get("members", [])]
        return []

    def _get_trust(self, relationship: Any, individual_id: str) -> float:
        """Get trust level from relationship."""
        if hasattr(relationship, "get_trust"):
            return float(relationship.get_trust(individual_id))
        if hasattr(relationship, "trust"):
            trust = relationship.trust
            if isinstance(trust, dict):
                return float(trust.get(individual_id, 0.5))
            return float(trust)
        if isinstance(relationship, dict):
            trust = relationship.get("trust", 0.5)
            if isinstance(trust, dict):
                return float(trust.get(individual_id, 0.5))
            return float(trust)
        return 0.5

    def validate(self, prompt: str) -> ValidationResult:
        """Validate a generated prompt.

        Args:
            prompt: The prompt to validate.

        Returns:
            ValidationResult with any errors or warnings.
        """
        result = ValidationResult()

        # Check for empty prompt
        if not prompt.strip():
            result.is_valid = False
            result.errors.append("Prompt is empty")
            return result

        # Check approximate token length (rough estimate: 4 chars per token)
        estimated_tokens = len(prompt) // 4
        if estimated_tokens > self.max_tokens:
            result.warnings.append(f"Prompt may be too long: ~{estimated_tokens} tokens (max: {self.max_tokens})")

        # Check for required sections
        if "roleplaying as" not in prompt.lower():
            result.warnings.append("Missing identity section")

        return result

    def get_builder(self) -> PromptBuilder:
        """Get a new PromptBuilder with this manager's settings.

        Returns:
            Configured PromptBuilder instance.
        """
        return PromptBuilder()


__all__ = [
    "PromptManager",
    "ValidationResult",
]
