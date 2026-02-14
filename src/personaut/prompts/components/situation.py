"""Situation component for prompt generation.

This module provides the SituationComponent class that formats
situational context including modality, location, and environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from personaut.types.modality import Modality


if TYPE_CHECKING:
    from personaut.situations.situation import Situation


# Modality-specific descriptions
MODALITY_DESCRIPTIONS: dict[Modality, dict[str, str]] = {
    Modality.IN_PERSON: {
        "setting": "physically present",
        "cues": "can observe body language and environmental cues",
        "timing": "responses are immediate and spontaneous",
    },
    Modality.VIDEO_CALL: {
        "setting": "on a video call",
        "cues": "can see facial expressions but environmental cues are limited",
        "timing": "responses are immediate but may have slight delays",
    },
    Modality.PHONE_CALL: {
        "setting": "on a phone call",
        "cues": "can only hear vocal tones and cannot see visual cues",
        "timing": "responses are immediate and conversational",
    },
    Modality.TEXT_MESSAGE: {
        "setting": "communicating via text message",
        "cues": "has time to consider responses and cannot see immediate reactions",
        "timing": "can think before responding, asynchronous",
    },
    Modality.EMAIL: {
        "setting": "communicating via email",
        "cues": "has significant time to compose thoughtful responses",
        "timing": "formal and asynchronous",
    },
    Modality.SURVEY: {
        "setting": "responding to a survey",
        "cues": "answering structured questions",
        "timing": "considered and reflective",
    },
}


@dataclass
class SituationComponent:
    """Component for formatting situational context into prompt text.

    This component converts a Situation into natural language that
    provides context about where, when, and how individuals are interacting.

    Attributes:
        include_modality_traits: Whether to include modality characteristics.
        include_environment: Whether to include environmental details.

    Example:
        >>> component = SituationComponent()
        >>> text = component.format(situation)
    """

    include_modality_traits: bool = True
    include_environment: bool = True

    def format(
        self,
        situation: Situation | Any,
        *,
        name: str = "They",
    ) -> str:
        """Format a situation into natural language.

        Args:
            situation: The situation to format.
            name: Name to use in the description.

        Returns:
            Natural language description of the situation.
        """
        lines = ["## Situation"]

        # Get modality
        modality = self._get_modality(situation)
        modality_info = MODALITY_DESCRIPTIONS.get(modality, {})

        # Description line
        description = self._get_description(situation)
        location = self._get_location(situation)

        setting = modality_info.get("setting", "interacting")

        if location:
            lines.append(f"{name} is {setting} at {location}.")
        else:
            lines.append(f"{name} is {setting}.")

        if description:
            lines.append(f"Context: {description}")

        # Modality traits
        if self.include_modality_traits and modality_info:
            cues = modality_info.get("cues", "")
            if cues:
                lines.append(f"{name} {cues}.")

        # Environmental context
        if self.include_environment:
            context = self._get_context(situation)
            if context:
                for key, value in context.items():
                    if isinstance(value, str):
                        lines.append(f"- {key.title()}: {value}")

        return "\n".join(lines)

    def _get_modality(self, situation: Any) -> Modality:
        """Get modality from situation object."""
        if hasattr(situation, "modality"):
            modality = situation.modality
            if isinstance(modality, Modality):
                return modality
            if isinstance(modality, str):
                try:
                    return Modality(modality)
                except ValueError:
                    return Modality.TEXT_MESSAGE
        if isinstance(situation, dict):
            modality = situation.get("modality", "text_message")
            try:
                return Modality(modality)
            except ValueError:
                return Modality.TEXT_MESSAGE
        return Modality.TEXT_MESSAGE

    def _get_description(self, situation: Any) -> str | None:
        """Get description from situation object."""
        if hasattr(situation, "description"):
            return str(situation.description) if situation.description else None
        if isinstance(situation, dict):
            desc = situation.get("description")
            return str(desc) if desc else None
        return None

    def _get_location(self, situation: Any) -> str | None:
        """Get location from situation object."""
        if hasattr(situation, "location"):
            return str(situation.location) if situation.location else None
        if isinstance(situation, dict):
            loc = situation.get("location")
            return str(loc) if loc else None
        return None

    def _get_context(self, situation: Any) -> dict[str, Any]:
        """Get additional context from situation object."""
        if hasattr(situation, "context"):
            ctx = situation.context
            return dict(ctx) if ctx else {}
        if isinstance(situation, dict):
            return dict(situation.get("context", {}))
        return {}

    def format_brief(
        self,
        situation: Situation | Any,
    ) -> str:
        """Generate a brief one-line situation summary.

        Args:
            situation: The situation to summarize.

        Returns:
            Brief summary suitable for inline use.
        """
        modality = self._get_modality(situation)
        location = self._get_location(situation)

        modality_info = MODALITY_DESCRIPTIONS.get(modality, {})
        setting = modality_info.get("setting", "interacting")

        if location:
            return f"{setting} at {location}"
        return setting

    def format_modality_context(
        self,
        modality: Modality,
        *,
        name: str = "They",
    ) -> str:
        """Format modality-specific communication context.

        Args:
            modality: The communication modality.
            name: Name to use in description.

        Returns:
            Description of modality characteristics.
        """
        info = MODALITY_DESCRIPTIONS.get(modality, {})

        parts = []
        if info.get("cues"):
            parts.append(f"{name} {info['cues']}.")
        if info.get("timing"):
            parts.append(f"Communication is {info['timing']}.")

        return " ".join(parts)


__all__ = [
    "MODALITY_DESCRIPTIONS",
    "SituationComponent",
]
