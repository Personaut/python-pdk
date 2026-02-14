"""Modality definitions for Personaut PDK.

This module defines the different communication modalities available for
simulations and live interactions. Each modality represents a distinct
communication channel with specific characteristics and UI representations.

Example:
    >>> from personaut.types.modality import Modality
    >>> modality = Modality.TEXT_MESSAGE
    >>> print(modality.description)
    'Asynchronous text-based messaging (SMS, chat apps)'
"""

from __future__ import annotations

from enum import Enum


class Modality(str, Enum):
    """Communication modality for interactions.

    Modalities define the channel through which individuals communicate
    in a simulation. Each modality has distinct characteristics that
    affect how prompts are generated and how the UI is rendered.

    Attributes:
        IN_PERSON: Face-to-face conversation.
        TEXT_MESSAGE: Asynchronous text messaging (SMS, chat).
        EMAIL: Email correspondence.
        PHONE_CALL: Voice-only phone conversation.
        VIDEO_CALL: Video conference call.
        SURVEY: Questionnaire or survey format.

    Example:
        >>> situation = create_situation(
        ...     type=Modality.TEXT_MESSAGE, description="Catching up with a friend"
        ... )
    """

    IN_PERSON = "in_person"
    TEXT_MESSAGE = "text_message"
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    VIDEO_CALL = "video_call"
    SURVEY = "survey"

    @property
    def description(self) -> str:
        """Get a human-readable description of the modality.

        Returns:
            Description of the modality's characteristics.
        """
        descriptions = {
            Modality.IN_PERSON: "Face-to-face conversation with full non-verbal cues",
            Modality.TEXT_MESSAGE: "Asynchronous text-based messaging (SMS, chat apps)",
            Modality.EMAIL: "Formal or semi-formal email correspondence",
            Modality.PHONE_CALL: "Voice-only phone conversation",
            Modality.VIDEO_CALL: "Video conference with visual and audio communication",
            Modality.SURVEY: "Structured questionnaire or survey format",
        }
        return descriptions[self]

    @property
    def is_synchronous(self) -> bool:
        """Check if the modality is synchronous (real-time).

        Synchronous modalities expect immediate responses, while
        asynchronous modalities allow for delays.

        Returns:
            True if the modality is synchronous.
        """
        synchronous = {Modality.IN_PERSON, Modality.PHONE_CALL, Modality.VIDEO_CALL}
        return self in synchronous

    @property
    def has_visual_cues(self) -> bool:
        """Check if the modality includes visual communication.

        Visual modalities allow for facial expressions and body language.

        Returns:
            True if the modality includes visual cues.
        """
        visual = {Modality.IN_PERSON, Modality.VIDEO_CALL}
        return self in visual

    @property
    def has_audio_cues(self) -> bool:
        """Check if the modality includes audio communication.

        Audio modalities allow for tone of voice and verbal nuances.

        Returns:
            True if the modality includes audio cues.
        """
        audio = {Modality.IN_PERSON, Modality.PHONE_CALL, Modality.VIDEO_CALL}
        return self in audio

    @property
    def ui_template(self) -> str:
        """Get the UI template name for rendering this modality.

        Returns:
            Template name for the modality's UI representation.
        """
        templates = {
            Modality.IN_PERSON: "chat/in_person.html",
            Modality.TEXT_MESSAGE: "chat/text_message.html",
            Modality.EMAIL: "chat/email.html",
            Modality.PHONE_CALL: "chat/phone_call.html",
            Modality.VIDEO_CALL: "chat/video_call.html",
            Modality.SURVEY: "survey/questionnaire.html",
        }
        return templates[self]

    @property
    def formality_level(self) -> str:
        """Get the typical formality level for this modality.

        Returns:
            Formality level: 'casual', 'semi-formal', or 'formal'.
        """
        formality = {
            Modality.IN_PERSON: "casual",
            Modality.TEXT_MESSAGE: "casual",
            Modality.EMAIL: "semi-formal",
            Modality.PHONE_CALL: "semi-formal",
            Modality.VIDEO_CALL: "semi-formal",
            Modality.SURVEY: "formal",
        }
        return formality[self]


# String constants for backward compatibility and convenience
IN_PERSON = Modality.IN_PERSON.value
TEXT_MESSAGE = Modality.TEXT_MESSAGE.value
EMAIL = Modality.EMAIL.value
PHONE_CALL = Modality.PHONE_CALL.value
VIDEO_CALL = Modality.VIDEO_CALL.value
SURVEY = Modality.SURVEY.value


def parse_modality(value: str | Modality) -> Modality:
    """Parse a string or Modality value into a Modality enum.

    This function provides flexible parsing of modality values, accepting
    both string values and Modality enum instances.

    Args:
        value: String value or Modality enum to parse.

    Returns:
        The corresponding Modality enum value.

    Raises:
        ValueError: If the value is not a valid modality.

    Example:
        >>> parse_modality("text_message")
        <Modality.TEXT_MESSAGE: 'text_message'>
        >>> parse_modality(Modality.EMAIL)
        <Modality.EMAIL: 'email'>
    """
    if isinstance(value, Modality):
        return value

    try:
        return Modality(value)
    except ValueError:
        valid = [m.value for m in Modality]
        msg = f"Invalid modality '{value}'. Valid options: {valid}"
        raise ValueError(msg) from None


__all__ = [
    # Constants
    "EMAIL",
    "IN_PERSON",
    "PHONE_CALL",
    "SURVEY",
    "TEXT_MESSAGE",
    "VIDEO_CALL",
    # Enum
    "Modality",
    # Functions
    "parse_modality",
]
