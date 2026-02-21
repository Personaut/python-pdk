"""Individual implementation for Personaut PDK.

This module provides the Individual class, which represents a persona
with traits, emotions, memories, masks, and triggers.

Example:
    >>> from personaut.individuals import create_individual
    >>> from personaut.emotions import EmotionalState
    >>> from personaut.traits import TraitProfile, WARMTH, DOMINANCE
    >>>
    >>> # Create trait profile
    >>> traits = TraitProfile()
    >>> traits.set_trait(WARMTH, 0.8)
    >>> traits.set_trait(DOMINANCE, 0.4)
    >>>
    >>> # Create individual with traits
    >>> individual = create_individual(
    ...     name="Sarah",
    ...     traits=traits,
    ...     emotional_state=EmotionalState({"cheerful": 0.6}),
    ... )
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar

from personaut.emotions.state import EmotionalState
from personaut.individuals.physical import PhysicalFeatures
from personaut.masks.mask import Mask
from personaut.traits.profile import TraitProfile
from personaut.triggers.trigger import Trigger
from personaut.types.exceptions import MINIMUM_SIMULATION_AGE, AgeRestrictionError


if TYPE_CHECKING:
    from personaut.memory.memory import Memory
    from personaut.situations.situation import Situation

logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """A simulated individual with personality, emotions, and memories.

    An Individual represents a complete persona that can participate in
    simulations. It combines:
    - Emotional state (current feelings)
    - Trait profile (personality characteristics)
    - Physical features (appearance description)
    - Memories (experiences and knowledge)
    - Masks (contextual personas)
    - Triggers (automatic responses)

    Attributes:
        id: Unique identifier for this individual.
        name: Human-readable name.
        emotional_state: Current emotional state.
        traits: Personality trait profile.
        physical_features: Physical appearance description.
        memories: List of memories belonging to this individual.
        masks: Available contextual personas.
        triggers: Automatic response triggers.
        active_mask: Currently active mask (if any).
        metadata: Additional metadata about the individual.
        created_at: When this individual was created.
        updated_at: When this individual was last updated.

    Example:
        >>> individual = Individual(
        ...     name="Sarah Chen",
        ...     emotional_state=EmotionalState({"cheerful": 0.6}),
        ...     traits=TraitProfile({"warmth": 0.8}),
        ... )
        >>> individual.get_dominant_emotion()
        ('cheerful', 0.6)
    """

    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Remember what Uncle Ben said: "With great power comes great
    # responsibility." Don't be a creep!
    age: int | None = None
    emotional_state: EmotionalState = field(default_factory=EmotionalState)
    traits: TraitProfile = field(default_factory=TraitProfile)
    physical_features: PhysicalFeatures = field(default_factory=PhysicalFeatures)
    memories: list[Memory] = field(default_factory=list)
    masks: list[Mask] = field(default_factory=list)
    triggers: list[Trigger] = field(default_factory=list)
    active_mask: Mask | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    MAX_NAME_LENGTH: ClassVar[int] = 255

    def __post_init__(self) -> None:
        """Validate individual constraints after dataclass construction."""
        from personaut.types.exceptions import ValidationError as _ValidationError

        # Validate name
        if not self.name or not self.name.strip():
            raise _ValidationError(
                "Individual name must not be empty",
                field="name",
                value=self.name,
            )
        if len(self.name) > self.MAX_NAME_LENGTH:
            raise _ValidationError(
                f"Individual name exceeds maximum length of {self.MAX_NAME_LENGTH} characters",
                field="name",
                value=self.name,
            )

        # Remember what Uncle Ben said: "With great power comes great
        # responsibility." Don't be a creep!
        if self.age is not None and self.age < MINIMUM_SIMULATION_AGE:
            raise AgeRestrictionError(self.age, name=self.name)

    # -- Emotional State Methods --

    def get_emotional_state(self) -> EmotionalState:
        """Get the current emotional state, modified by active mask.

        Returns:
            The emotional state, possibly modified by the active mask.
        """
        if self.active_mask is not None:
            return self.active_mask.apply(self.emotional_state)
        return self.emotional_state

    def get_raw_emotional_state(self) -> EmotionalState:
        """Get the raw emotional state without mask modifications.

        Returns:
            The unmodified emotional state.
        """
        return self.emotional_state

    def change_emotion(self, emotion: str, delta: float) -> None:
        """Change an emotion's intensity.

        Args:
            emotion: The emotion name.
            delta: Amount to change (positive or negative).
        """
        self.emotional_state.change_emotion(emotion, delta)
        self._update_timestamp()

    def set_emotion(self, emotion: str, value: float) -> None:
        """Set an emotion to a specific value.

        Args:
            emotion: The emotion name.
            value: The new intensity (0.0-1.0).
        """
        # change_emotion sets the absolute value
        self.emotional_state.change_emotion(emotion, value)
        self._update_timestamp()

    def get_dominant_emotion(self) -> tuple[str, float] | None:
        """Get the dominant emotion from the effective state.

        Returns:
            Tuple of (emotion_name, intensity) or None if no emotions.
        """
        state = self.get_emotional_state()
        return state.get_dominant()

    # -- Trait Methods --

    def get_trait(self, trait: str) -> float:
        """Get a trait's value.

        Args:
            trait: The trait name.

        Returns:
            The trait value (0.0-1.0).
        """
        return self.traits.get_trait(trait)

    def set_trait(self, trait: str, value: float) -> None:
        """Set a trait's value.

        Args:
            trait: The trait name.
            value: The trait value (0.0-1.0).
        """
        self.traits.set_trait(trait, value)
        self._update_timestamp()

    def get_high_traits(self, threshold: float = 0.7) -> list[tuple[str, float]]:
        """Get traits above a threshold.

        Args:
            threshold: Minimum value to include.

        Returns:
            List of (trait_name, value) tuples.
        """
        return self.traits.get_high_traits(threshold)

    def get_low_traits(self, threshold: float = 0.3) -> list[tuple[str, float]]:
        """Get traits below a threshold.

        Args:
            threshold: Maximum value to include.

        Returns:
            List of (trait_name, value) tuples.
        """
        return self.traits.get_low_traits(threshold)

    # -- Memory Methods --

    def add_memory(self, memory: Memory) -> None:
        """Add a memory to this individual.

        If a memory with the same ID already exists, it is replaced.

        Args:
            memory: The memory to add.
        """
        # Deduplicate by ID — replace existing if same ID
        for i, existing in enumerate(self.memories):
            if existing.id == memory.id:
                self.memories[i] = memory
                self._update_timestamp()
                return
        self.memories.append(memory)
        self._update_timestamp()

    def remove_memory(self, memory_id: str) -> bool:
        """Remove a memory by ID.

        Args:
            memory_id: The ID of the memory to remove.

        Returns:
            True if removed, False if not found.
        """
        for i, mem in enumerate(self.memories):
            if mem.id == memory_id:
                self.memories.pop(i)
                self._update_timestamp()
                return True
        return False

    def get_memories(
        self,
        limit: int | None = None,
        tags: list[str] | None = None,
    ) -> list[Memory]:
        """Get memories, optionally filtered.

        Args:
            limit: Maximum number of memories to return.
            tags: Filter by tags (checks memory.metadata.get('tags')).

        Returns:
            List of matching memories.
        """
        result = list(self.memories)

        # Filter by tags if specified (using metadata)
        if tags:
            filtered: list[Memory] = []
            for m in result:
                mem_tags = m.metadata.get("tags", []) if hasattr(m, "metadata") else []
                if any(t in mem_tags for t in tags):
                    filtered.append(m)
            result = filtered

        # Apply limit
        if limit is not None:
            result = result[:limit]

        return result

    def memory_count(self) -> int:
        """Get the number of memories."""
        return len(self.memories)

    # -- Mask Methods --

    def add_mask(self, mask: Mask) -> None:
        """Add a mask to this individual.

        Args:
            mask: The mask to add.
        """
        self.masks.append(mask)
        self._update_timestamp()

    def remove_mask(self, mask_name: str) -> bool:
        """Remove a mask by name.

        Args:
            mask_name: The name of the mask to remove.

        Returns:
            True if removed, False if not found.
        """
        for i, m in enumerate(self.masks):
            if m.name == mask_name:
                # Deactivate if this is the active mask
                if self.active_mask and self.active_mask.name == mask_name:
                    self.active_mask = None
                self.masks.pop(i)
                self._update_timestamp()
                return True
        return False

    def get_mask(self, mask_name: str) -> Mask | None:
        """Get a mask by name.

        Args:
            mask_name: The name of the mask.

        Returns:
            The mask or None if not found.
        """
        for m in self.masks:
            if m.name == mask_name:
                return m
        return None

    def activate_mask(self, mask_name: str) -> bool:
        """Activate a mask by name.

        Args:
            mask_name: The name of the mask to activate.

        Returns:
            True if activated, False if not found.
        """
        mask = self.get_mask(mask_name)
        if mask is not None:
            self.active_mask = mask
            self._update_timestamp()
            return True
        return False

    def deactivate_mask(self) -> None:
        """Deactivate the current mask."""
        self.active_mask = None
        self._update_timestamp()

    def has_mask(self, mask_name: str) -> bool:
        """Check if this individual has a mask.

        Args:
            mask_name: The name to check.

        Returns:
            True if the mask exists.
        """
        return self.get_mask(mask_name) is not None

    # -- Trigger Methods --

    def add_trigger(self, trigger: Trigger) -> None:
        """Add a trigger to this individual.

        Args:
            trigger: The trigger to add.
        """
        self.triggers.append(trigger)
        self._update_timestamp()

    def remove_trigger(self, trigger: Trigger) -> bool:
        """Remove a trigger.

        Args:
            trigger: The trigger to remove.

        Returns:
            True if removed, False if not found.
        """
        try:
            self.triggers.remove(trigger)
            self._update_timestamp()
            return True
        except ValueError:
            return False

    def remove_trigger_by_description(self, description: str) -> bool:
        """Remove a trigger by description.

        Args:
            description: The description of the trigger to remove.

        Returns:
            True if removed, False if not found.
        """
        for i, t in enumerate(self.triggers):
            if t.description == description:
                self.triggers.pop(i)
                self._update_timestamp()
                return True
        return False

    def check_triggers(
        self,
        situation: Situation | None = None,
    ) -> list[Trigger]:
        """Check which triggers would fire.

        For emotional triggers, the emotional state is used as context.
        For situational triggers, the situation is used as context.

        Args:
            situation: Optional situation context for situational triggers.

        Returns:
            List of triggers that would fire.
        """
        from personaut.triggers.emotional import EmotionalTrigger
        from personaut.triggers.situational import SituationalTrigger

        fired: list[Trigger] = []
        for trigger in self.triggers:
            # Use different check calls based on trigger type
            should_fire = False
            if isinstance(trigger, EmotionalTrigger):
                should_fire = trigger.check(self.emotional_state)
            elif isinstance(trigger, SituationalTrigger):
                should_fire = trigger.check(situation)
            else:
                # Default to checking with emotional state for unknown types
                should_fire = trigger.check(self.emotional_state)

            if should_fire:
                fired.append(trigger)
        return fired

    def fire_triggers(
        self,
        situation: Situation | None = None,
    ) -> list[Trigger]:
        """Check and fire all matching triggers.

        This applies the effects of any triggered responses to the
        individual's emotional state or activates masks.

        Args:
            situation: Optional situation context.

        Returns:
            List of triggers that fired.
        """
        fired = self.check_triggers(situation)
        for trigger in fired:
            response = trigger.fire(self.emotional_state)
            if isinstance(response, EmotionalState):
                self.emotional_state = response
            elif isinstance(response, Mask):
                self.active_mask = response
        return fired

    # -- Metadata Methods --

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value.

        Args:
            key: The metadata key.
            value: The value to set.
        """
        self.metadata[key] = value
        self._update_timestamp()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value.

        Args:
            key: The metadata key.
            default: Default if not found.

        Returns:
            The metadata value or default.
        """
        return self.metadata.get(key, default)

    def has_metadata(self, key: str) -> bool:
        """Check if a metadata key exists."""
        return key in self.metadata

    # -- Serialization --

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "emotional_state": self.emotional_state.to_dict(),
            "traits": self.traits.to_dict(),
            "physical_features": self.physical_features.to_dict(),
            "memories": [m.to_dict() for m in self.memories],
            "masks": [m.to_dict() for m in self.masks],
            "triggers": [t.to_dict() for t in self.triggers],
            "active_mask": self.active_mask.name if self.active_mask else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Individual:
        """Create from dictionary.

        Performs a full restoration including memories, masks, triggers,
        and active mask state.
        """
        from personaut.memory.memory import Memory
        from personaut.triggers.emotional import EmotionalTrigger
        from personaut.triggers.situational import SituationalTrigger

        # Create emotional state from dict
        emotional_state = EmotionalState()
        if "emotional_state" in data:
            emotional_state.change_state(data["emotional_state"])

        # Create trait profile from dict
        traits = TraitProfile()
        if "traits" in data:
            for trait, value in data["traits"].items():
                try:
                    traits.set_trait(trait, value)
                except Exception:
                    logger.warning("Skipping invalid trait %r=%r during deserialization", trait, value)

        physical_features = PhysicalFeatures.from_dict(data.get("physical_features"))

        # Restore memories
        memories: list[Memory] = []
        for mem_data in data.get("memories") or []:
            try:
                memories.append(Memory.from_dict(mem_data))
            except Exception:
                logger.warning("Skipping malformed memory during deserialization", exc_info=True)

        # Restore masks
        masks: list[Mask] = []
        for mask_data in data.get("masks") or []:
            try:
                masks.append(Mask.from_dict(mask_data))
            except Exception:
                logger.warning("Skipping malformed mask during deserialization", exc_info=True)

        # Restore triggers (dispatch by type)
        triggers: list[Trigger] = []
        for trigger_data in data.get("triggers") or []:
            try:
                trigger_type = trigger_data.get("type", "emotional")
                if trigger_type == "situational":
                    triggers.append(SituationalTrigger.from_dict(trigger_data))
                else:
                    triggers.append(EmotionalTrigger.from_dict(trigger_data))
            except Exception:
                logger.warning("Skipping malformed trigger during deserialization", exc_info=True)

        # Restore active mask reference
        active_mask: Mask | None = None
        active_mask_name = data.get("active_mask")
        if active_mask_name:
            for m in masks:
                if m.name == active_mask_name:
                    active_mask = m
                    break

        return cls(
            id=data["id"],
            name=data["name"],
            age=data.get("age"),
            emotional_state=emotional_state,
            traits=traits,
            physical_features=physical_features,
            memories=memories,
            masks=masks,
            triggers=triggers,
            active_mask=active_mask,
            metadata=data.get("metadata") or {},
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data.get("updated_at", data["created_at"])),
        )

    # -- Private Methods --

    def _update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()

    def __str__(self) -> str:
        """Human-readable representation."""
        dominant = self.get_dominant_emotion()
        emotion_str = f"{dominant[0]}={dominant[1]:.1f}" if dominant else "neutral"
        mask_str = f" [{self.active_mask.name}]" if self.active_mask else ""
        return f"Individual({self.name}, {emotion_str}{mask_str})"

    def __repr__(self) -> str:
        return f"Individual(id={self.id!r}, name={self.name!r})"


def create_individual(
    name: str,
    age: int | None = None,
    traits: TraitProfile | dict[str, float] | None = None,
    emotional_state: EmotionalState | dict[str, float] | None = None,
    physical_features: PhysicalFeatures | dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Individual:
    """Create a new individual.

    Factory function for creating Individual instances with convenient
    argument handling.

    Args:
        name: The individual's name.
        age: Age in years (must be 18+, or None if unspecified).
        traits: Trait profile or dict of trait values.
        emotional_state: Emotional state or dict of emotion values.
        physical_features: Physical appearance or dict of features.
        metadata: Optional metadata dictionary.

    Returns:
        A new Individual instance.

    Raises:
        AgeRestrictionError: If *age* is below 18.

    Example:
        >>> individual = create_individual(
        ...     name="Sarah",
        ...     age=28,
        ...     traits={"warmth": 0.8, "dominance": 0.4},
        ...     emotional_state={"cheerful": 0.6},
        ...     physical_features={"hair": "long red hair", "eyes": "green"},
        ... )
    """
    # Handle traits
    if traits is None:
        trait_profile = TraitProfile()
    elif isinstance(traits, dict):
        trait_profile = TraitProfile()
        for trait, value in traits.items():
            try:
                trait_profile.set_trait(trait, value)
            except Exception:
                logger.warning("Skipping invalid trait %r during creation", trait, exc_info=True)
    else:
        trait_profile = traits

    # Handle emotional state
    if emotional_state is None:
        emotion_state = EmotionalState()
    elif isinstance(emotional_state, dict):
        emotion_state = EmotionalState()
        emotion_state.change_state(emotional_state)
    else:
        emotion_state = emotional_state

    # Handle physical features
    if physical_features is None:
        phys = PhysicalFeatures()
    elif isinstance(physical_features, dict):
        phys = PhysicalFeatures.from_dict(physical_features)
    else:
        phys = physical_features

    return Individual(
        name=name,
        age=age,
        traits=trait_profile,
        emotional_state=emotion_state,
        physical_features=phys,
        metadata=metadata or {},
    )


def create_human(
    name: str,
    context: str | None = None,
    role: str | None = None,
) -> Individual:
    """Create an individual representing a human in a simulation.

    This creates a tracked individual that represents a real human
    participating in a simulation (e.g., the user).

    Args:
        name: The human's name or identifier.
        context: Optional context about the human.
        role: Optional role in the simulation.

    Returns:
        A new Individual with human metadata.

    Example:
        >>> human = create_human("User", role="interviewer")
    """
    metadata: dict[str, Any] = {
        "is_human": True,
        "tracked": True,
    }
    if context:
        metadata["context"] = context
    if role:
        metadata["role"] = role

    return Individual(
        name=name,
        metadata=metadata,
    )


def create_nontracked_individual(
    role: str,
    name: str | None = None,
) -> Individual:
    """Create a non-tracked individual for background purposes.

    Non-tracked individuals are used for background characters or
    anonymous participants that don't need full state management.

    Args:
        role: The role this individual plays.
        name: Optional name (defaults to role).

    Returns:
        A new non-tracked Individual.

    Example:
        >>> barista = create_nontracked_individual("barista")
        >>> crowd = create_nontracked_individual("crowd_member")
    """
    return Individual(
        name=name or role.replace("_", " ").title(),
        metadata={
            "is_human": False,
            "tracked": False,
            "role": role,
        },
    )


__all__ = [
    "Individual",
    "create_human",
    "create_individual",
    "create_nontracked_individual",
]
