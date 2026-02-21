"""Mask implementation for Personaut PDK.

Masks are contextual personas that modify emotional expression based on
situational context. They allow individuals to adapt their behavior to
different social contexts while maintaining their underlying emotional state.

Example:
    >>> from personaut.masks import create_mask, PROFESSIONAL_MASK
    >>> from personaut.emotions.state import EmotionalState
    >>>
    >>> # Create a custom mask
    >>> mask = create_mask(
    ...     name="interview",
    ...     emotional_modifications={"anxious": -0.3, "proud": 0.4},
    ...     trigger_situations=["interview", "formal meeting"],
    ... )
    >>>
    >>> # Apply mask to emotional state
    >>> state = EmotionalState()
    >>> state.change_emotion("anxious", 0.7)
    >>> modified = mask.apply(state)
    >>> modified.get_emotion("anxious")  # 0.4 (reduced by 0.3)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState


@dataclass
class Mask:
    """Contextual persona that modifies emotional expression.

    Masks represent social personas that individuals adopt in specific
    situations. They modify emotional expression without changing the
    underlying emotional state.

    Attributes:
        name: Human-readable name for the mask.
        emotional_modifications: Changes to apply to emotions.
            Positive values increase, negative values decrease.
        trigger_situations: Keywords that trigger this mask.
        active_by_default: Whether mask is active without triggers.
        description: Optional description of the mask's purpose.

    Example:
        >>> mask = Mask(
        ...     name="professional",
        ...     emotional_modifications={"angry": -0.5, "content": 0.2},
        ...     trigger_situations=["office", "meeting"],
        ... )
        >>> mask.should_trigger("office meeting")
        True
    """

    name: str
    emotional_modifications: dict[str, float] = field(default_factory=dict)
    trigger_situations: list[str] = field(default_factory=list)
    active_by_default: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        """Validate mask configuration."""
        # Validate emotional modifications are within bounds
        for emotion, value in self.emotional_modifications.items():
            if not -1.0 <= value <= 1.0:
                msg = f"Modification for '{emotion}' must be between -1.0 and 1.0, got {value}"
                raise ValueError(msg)

    def apply(self, emotional_state: EmotionalState) -> EmotionalState:
        """Apply this mask to an emotional state.

        Creates a new EmotionalState with modified values. The original
        state is not changed.

        Args:
            emotional_state: The emotional state to modify.

        Returns:
            A new EmotionalState with modifications applied.

        Example:
            >>> state = EmotionalState()
            >>> state.change_emotion("angry", 0.8)
            >>> modified = professional_mask.apply(state)
            >>> modified.get_emotion("angry")  # Reduced
        """
        from personaut.emotions.state import EmotionalState

        # Get all current emotion values
        current_values = emotional_state.to_dict()

        # Apply modifications
        new_values = {}
        for emotion, value in current_values.items():
            modification = self.emotional_modifications.get(emotion, 0.0)
            new_value = max(0.0, min(1.0, value + modification))
            new_values[emotion] = new_value

        # Create new state with modified values
        new_state = EmotionalState(
            emotions=list(new_values.keys()),
            baseline=0.0,
        )
        new_state.change_state(new_values)

        return new_state

    def should_trigger(self, situation_text: str) -> bool:
        """Check if this mask should trigger for a situation.

        Args:
            situation_text: Description of the situation.

        Returns:
            True if any trigger keyword is found in the situation.

        Example:
            >>> mask = Mask(name="work", trigger_situations=["office", "meeting"])
            >>> mask.should_trigger("Attending an office meeting")
            True
        """
        if self.active_by_default:
            return True

        situation_lower = situation_text.lower()
        return any(trigger.lower() in situation_lower for trigger in self.trigger_situations)

    def get_modification(self, emotion: str) -> float:
        """Get the modification value for a specific emotion.

        Args:
            emotion: Name of the emotion.

        Returns:
            The modification value, or 0.0 if not specified.
        """
        return self.emotional_modifications.get(emotion, 0.0)

    def to_dict(self) -> dict[str, Any]:
        """Convert mask to dictionary for serialization."""
        return {
            "name": self.name,
            "emotional_modifications": self.emotional_modifications,
            "trigger_situations": self.trigger_situations,
            "active_by_default": self.active_by_default,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Mask:
        """Create a Mask from a dictionary."""
        return cls(
            name=data["name"],
            emotional_modifications=data.get("emotional_modifications", {}),
            trigger_situations=data.get("trigger_situations", []),
            active_by_default=data.get("active_by_default", False),
            description=data.get("description", ""),
        )


def create_mask(
    name: str,
    emotional_modifications: dict[str, float] | None = None,
    trigger_situations: list[str] | None = None,
    active_by_default: bool = False,
    description: str = "",
) -> Mask:
    """Create a new mask.

    Factory function for creating Mask instances with sensible defaults.

    Args:
        name: Human-readable name for the mask.
        emotional_modifications: Changes to apply to emotions.
        trigger_situations: Keywords that trigger this mask.
        active_by_default: Whether mask is active without triggers.
        description: Optional description of the mask's purpose.

    Returns:
        A new Mask instance.

    Example:
        >>> mask = create_mask(
        ...     name="stoic",
        ...     emotional_modifications={
        ...         "excited": -0.4,
        ...         "anxious": -0.3,
        ...         "content": 0.2,
        ...     },
        ...     trigger_situations=["crisis", "emergency"],
        ... )
    """
    return Mask(
        name=name,
        emotional_modifications=emotional_modifications or {},
        trigger_situations=trigger_situations or [],
        active_by_default=active_by_default,
        description=description,
    )


__all__ = [
    "Mask",
    "create_mask",
]
