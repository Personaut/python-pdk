"""Prompt generation system for Personaut PDK.

This module provides dynamic prompt generation that incorporates emotional
state, personality traits, memories, relationships, and situational context.

Components:
- PromptManager: Orchestrates prompt generation
- PromptBuilder: Fluent interface for building prompts
- Templates: Pre-built templates for different simulation types
- Components: Reusable prompt sections

Example:
    >>> from personaut.prompts import PromptManager
    >>> manager = PromptManager()
    >>> prompt = manager.generate(individual, situation)

    >>> # Or use the builder for fine-grained control
    >>> from personaut.prompts import PromptBuilder
    >>> prompt = (PromptBuilder()
    ...     .with_individual(individual)
    ...     .with_situation(situation)
    ...     .using_template("conversation")
    ...     .build()
    ... )
"""

from personaut.prompts.builder import PromptBuilder
from personaut.prompts.manager import PromptManager, ValidationResult


# Lazy import for templates and components to avoid circular imports
__all__ = [
    # Main classes
    "PromptBuilder",
    "PromptManager",
    "ValidationResult",
    # Templates (lazy loaded)
    "BaseTemplate",
    "ConversationTemplate",
    "SurveyTemplate",
    "OutcomeTemplate",
    # Components (lazy loaded)
    "EmotionalStateComponent",
    "PersonalityComponent",
    "MemoryComponent",
    "RelationshipComponent",
    "SituationComponent",
]


def __getattr__(name: str) -> object:
    """Lazy load templates and components."""
    if name in (
        "BaseTemplate",
        "ConversationTemplate",
        "SurveyTemplate",
        "OutcomeTemplate",
    ):
        from personaut.prompts import templates

        return getattr(templates, name)

    if name in (
        "EmotionalStateComponent",
        "PersonalityComponent",
        "MemoryComponent",
        "RelationshipComponent",
        "SituationComponent",
    ):
        from personaut.prompts import components

        return getattr(components, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
