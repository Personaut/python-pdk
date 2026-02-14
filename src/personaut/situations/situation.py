"""Situation implementation for Personaut PDK.

This module provides the Situation class for defining the context
of simulations, including modality, time, location, and additional context.

Example:
    >>> from personaut.situations import create_situation
    >>> from personaut.types.modality import Modality
    >>> from datetime import datetime
    >>>
    >>> situation = create_situation(
    ...     modality=Modality.IN_PERSON,
    ...     description="Meeting at a coffee shop to discuss a project",
    ...     time=datetime.now(),
    ...     location="Miami, FL",
    ... )
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from personaut.types.modality import Modality, parse_modality


@dataclass
class Situation:
    """A situation providing context for a simulation.

    Defines the circumstances under which individuals are interacting,
    including the modality (how they're communicating), time, place,
    and additional contextual information.

    Attributes:
        id: Unique identifier for the situation.
        modality: How individuals are interacting (IN_PERSON, TEXT, etc.).
        description: Human-readable description of the situation.
        time: When the situation is occurring.
        location: Where the situation is occurring (if applicable).
        context: Additional contextual information.
        participants: IDs of individuals involved.
        tags: Labels for categorizing the situation.

    Example:
        >>> situation = Situation(
        ...     modality=Modality.IN_PERSON,
        ...     description="Team meeting in the conference room",
        ...     location="Conference Room A",
        ... )
    """

    modality: Modality
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    time: datetime | None = None
    location: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    participants: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the context dictionary.

        Args:
            key: The key to look up. Supports dot notation for nested access.
            default: Value to return if key not found.

        Returns:
            The value at the key, or default if not found.

        Example:
            >>> situation.get_context_value("environment.lighting")
            "bright"
        """
        if "." not in key:
            return self.context.get(key, default)

        # Handle nested key access
        parts = key.split(".")
        current: Any = self.context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default
        return current

    def set_context_value(self, key: str, value: Any) -> None:
        """Set a value in the context dictionary.

        Args:
            key: The key to set. Supports dot notation for nested access.
            value: The value to set.

        Example:
            >>> situation.set_context_value("environment.lighting", "dim")
        """
        if "." not in key:
            self.context[key] = value
            return

        # Handle nested key access
        parts = key.split(".")
        current = self.context
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def has_context(self, key: str) -> bool:
        """Check if a context key exists.

        Args:
            key: The key to check.

        Returns:
            True if the key exists in context.
        """
        return self.get_context_value(key) is not None

    def add_participant(self, participant_id: str) -> None:
        """Add a participant to the situation.

        Args:
            participant_id: ID of the participant to add.
        """
        if participant_id not in self.participants:
            self.participants.append(participant_id)

    def remove_participant(self, participant_id: str) -> None:
        """Remove a participant from the situation.

        Args:
            participant_id: ID of the participant to remove.
        """
        if participant_id in self.participants:
            self.participants.remove(participant_id)

    def has_participant(self, participant_id: str) -> bool:
        """Check if an individual is a participant.

        Args:
            participant_id: ID to check.

        Returns:
            True if the individual is a participant.
        """
        return participant_id in self.participants

    def add_tag(self, tag: str) -> None:
        """Add a tag to the situation.

        Args:
            tag: Tag to add.
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if the situation has a specific tag.

        Args:
            tag: Tag to check.

        Returns:
            True if the situation has the tag.
        """
        return tag in self.tags

    def is_in_person(self) -> bool:
        """Check if this is an in-person situation."""
        return self.modality == Modality.IN_PERSON

    def is_remote(self) -> bool:
        """Check if this is a remote/mediated situation."""
        return self.modality in {
            Modality.VIDEO_CALL,
            Modality.PHONE_CALL,
            Modality.TEXT_MESSAGE,
            Modality.EMAIL,
        }

    def is_synchronous(self) -> bool:
        """Check if this is a synchronous communication modality."""
        return self.modality in {
            Modality.IN_PERSON,
            Modality.VIDEO_CALL,
            Modality.PHONE_CALL,
        }

    def is_asynchronous(self) -> bool:
        """Check if this is an asynchronous communication modality."""
        return self.modality in {
            Modality.TEXT_MESSAGE,
            Modality.EMAIL,
        }

    def get_modality_traits(self) -> dict[str, Any]:
        """Get communication traits for the current modality.

        Returns:
            Dict with modality characteristics.
        """
        traits: dict[Modality, dict[str, Any]] = {
            Modality.IN_PERSON: {
                "visual_cues": True,
                "audio_cues": True,
                "physical_presence": True,
                "real_time": True,
                "formality": "varies",
            },
            Modality.VIDEO_CALL: {
                "visual_cues": True,
                "audio_cues": True,
                "physical_presence": False,
                "real_time": True,
                "formality": "moderate",
            },
            Modality.PHONE_CALL: {
                "visual_cues": False,
                "audio_cues": True,
                "physical_presence": False,
                "real_time": True,
                "formality": "moderate",
            },
            Modality.TEXT_MESSAGE: {
                "visual_cues": False,
                "audio_cues": False,
                "physical_presence": False,
                "real_time": False,
                "formality": "informal",
            },
            Modality.EMAIL: {
                "visual_cues": False,
                "audio_cues": False,
                "physical_presence": False,
                "real_time": False,
                "formality": "formal",
            },
        }
        result: dict[str, Any] = traits.get(self.modality, {})
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "modality": self.modality.value,
            "description": self.description,
            "time": self.time.isoformat() if self.time else None,
            "location": self.location,
            "context": self.context,
            "participants": self.participants,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Situation:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            modality=parse_modality(data["modality"]),
            description=data["description"],
            time=datetime.fromisoformat(data["time"]) if data.get("time") else None,
            location=data.get("location"),
            context=data.get("context", {}),
            participants=data.get("participants", []),
            tags=data.get("tags", []),
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        parts = [f"[{self.modality.value}] {self.description}"]
        if self.location:
            parts.append(f"at {self.location}")
        if self.time:
            parts.append(f"({self.time.strftime('%Y-%m-%d %H:%M')})")
        return " ".join(parts)


def create_situation(
    modality: Modality | str,
    description: str,
    time: datetime | None = None,
    location: str | None = None,
    context: dict[str, Any] | None = None,
    participants: list[str] | None = None,
    tags: list[str] | None = None,
) -> Situation:
    """Create a new situation.

    Factory function for creating Situation instances.

    Args:
        modality: How individuals are interacting.
        description: Human-readable description.
        time: When the situation is occurring.
        location: Where the situation is occurring.
        context: Additional contextual information.
        participants: IDs of individuals involved.
        tags: Labels for categorization.

    Returns:
        A new Situation instance.

    Example:
        >>> situation = create_situation(
        ...     modality=Modality.IN_PERSON,
        ...     description="Coffee shop meeting",
        ...     location="Downtown Cafe",
        ...     context={"atmosphere": "relaxed"},
        ... )
    """
    # Handle string modality
    if isinstance(modality, str):
        modality = parse_modality(modality)

    return Situation(
        modality=modality,
        description=description,
        time=time,
        location=location,
        context=context or {},
        participants=participants or [],
        tags=tags or [],
    )


__all__ = [
    "Situation",
    "create_situation",
]
