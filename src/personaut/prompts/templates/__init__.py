"""Prompt templates for different simulation types."""

from personaut.prompts.templates.base import BaseTemplate
from personaut.prompts.templates.conversation import ConversationTemplate
from personaut.prompts.templates.outcome import OutcomeTemplate
from personaut.prompts.templates.survey import SurveyTemplate


__all__ = [
    "BaseTemplate",
    "ConversationTemplate",
    "OutcomeTemplate",
    "SurveyTemplate",
]
