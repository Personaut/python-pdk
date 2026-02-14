"""Physical features for Personaut PDK individuals.

This module defines the PhysicalFeatures class that describes
an individual's physical appearance. These features are injected
into the system prompt so the LLM can reference them in stage
directions (e.g., "[pushes dark hair out of eyes]").

Example:
    >>> from personaut.individuals.physical import PhysicalFeatures
    >>>
    >>> features = PhysicalFeatures(
    ...     height="5'10\"",
    ...     build="athletic",
    ...     hair="short dark curly hair",
    ...     eyes="brown",
    ...     skin_tone="warm olive",
    ...     distinguishing_features=["scar above left eyebrow", "always wears a watch"],
    ... )
    >>> print(features.to_prompt())
    Height: 5'10", Build: athletic, Hair: short dark curly hair, Eyes: brown, ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================================
# Standard descriptors — used for UI dropdowns / validation hints
# ============================================================================

BUILDS = [
    "slim",
    "lean",
    "athletic",
    "average",
    "stocky",
    "muscular",
    "curvy",
    "heavyset",
    "petite",
    "tall and thin",
]
"""Common build descriptors shown in the UI."""

EYE_COLORS = [
    "brown",
    "dark brown",
    "hazel",
    "green",
    "blue",
    "gray",
    "amber",
    "black",
]
"""Common eye color options."""

HAIR_TYPES = [
    "straight",
    "wavy",
    "curly",
    "coily",
    "bald",
]
"""Common hair texture descriptors."""

HAIR_COLORS = [
    "black",
    "dark brown",
    "brown",
    "auburn",
    "red",
    "strawberry blonde",
    "blonde",
    "platinum blonde",
    "gray",
    "white",
    "silver",
]
"""Common hair color options."""

SKIN_TONES = [
    "pale",
    "fair",
    "light",
    "light olive",
    "olive",
    "warm olive",
    "tan",
    "medium brown",
    "brown",
    "dark brown",
    "deep brown",
    "ebony",
]
"""Common skin tone descriptors."""

# Remember what Uncle Ben said: "With great power comes great
# responsibility." Don't be a creep!
AGE_GROUPS = [
    "young adult",
    "adult",
    "middle-aged",
    "senior",
    "elderly",
]
"""Age descriptor groups (adults only — all individuals must be 18+)."""


# ============================================================================
# PhysicalFeatures dataclass
# ============================================================================


@dataclass
class PhysicalFeatures:
    """Physical appearance description for an individual.

    All fields are optional — only populated fields are included in
    prompts and serialization.  This keeps the model lightweight while
    still enabling rich physical descriptions when desired.

    Attributes:
        height: Height description (e.g. "5'10\"", "tall", "175cm").
        build: Body type / build (e.g. "athletic", "slim", "stocky").
        hair: Free-text hair description (color, length, style).
        eyes: Eye color or description.
        skin_tone: Skin tone description.
        age_appearance: How old the person looks (e.g. "mid-30s", "young adult").
        facial_features: Free-text facial description (e.g. "sharp jawline, dimples").
        distinguishing_features: Scars, tattoos, piercings, birthmarks, etc.
        clothing_style: Typical clothing / fashion sense.
        accessories: Glasses, watch, jewelry, etc.
        other: Any other appearance notes.

    Example:
        >>> pf = PhysicalFeatures(hair="long red hair", eyes="green")
        >>> pf.to_dict()
        {'hair': 'long red hair', 'eyes': 'green'}
    """

    height: str | None = None
    build: str | None = None
    hair: str | None = None
    eyes: str | None = None
    skin_tone: str | None = None
    age_appearance: str | None = None
    facial_features: str | None = None
    distinguishing_features: list[str] = field(default_factory=list)
    clothing_style: str | None = None
    accessories: list[str] = field(default_factory=list)
    other: str | None = None

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Return True if no physical features have been set."""
        return not any(
            [
                self.height,
                self.build,
                self.hair,
                self.eyes,
                self.skin_tone,
                self.age_appearance,
                self.facial_features,
                self.distinguishing_features,
                self.clothing_style,
                self.accessories,
                self.other,
            ]
        )

    # ------------------------------------------------------------------
    # Prompt rendering
    # ------------------------------------------------------------------

    def to_prompt(self) -> str:
        """Render a concise, natural-language description for LLM prompting.

        Only populated fields are included.  The output is designed to be
        injected into the system prompt so the LLM can reference these
        details in stage directions and dialogue.

        Returns:
            Formatted string, or empty string if no features set.

        Example:
            >>> pf = PhysicalFeatures(height="tall", build="lean", eyes="blue")
            >>> pf.to_prompt()
            'Height: tall. Build: lean. Eyes: blue.'
        """
        if self.is_empty():
            return ""

        parts: list[str] = []
        if self.age_appearance:
            parts.append(f"Appears {self.age_appearance}")
        if self.height:
            parts.append(f"Height: {self.height}")
        if self.build:
            parts.append(f"Build: {self.build}")
        if self.hair:
            parts.append(f"Hair: {self.hair}")
        if self.eyes:
            parts.append(f"Eyes: {self.eyes}")
        if self.skin_tone:
            parts.append(f"Skin tone: {self.skin_tone}")
        if self.facial_features:
            parts.append(f"Face: {self.facial_features}")
        if self.distinguishing_features:
            parts.append(f"Distinguishing features: {', '.join(self.distinguishing_features)}")
        if self.clothing_style:
            parts.append(f"Usually wears: {self.clothing_style}")
        if self.accessories:
            parts.append(f"Accessories: {', '.join(self.accessories)}")
        if self.other:
            parts.append(self.other)

        return ". ".join(parts) + "."

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary, omitting empty/None fields.

        Returns:
            Dict with only populated fields.
        """
        d: dict[str, Any] = {}
        if self.height:
            d["height"] = self.height
        if self.build:
            d["build"] = self.build
        if self.hair:
            d["hair"] = self.hair
        if self.eyes:
            d["eyes"] = self.eyes
        if self.skin_tone:
            d["skin_tone"] = self.skin_tone
        if self.age_appearance:
            d["age_appearance"] = self.age_appearance
        if self.facial_features:
            d["facial_features"] = self.facial_features
        if self.distinguishing_features:
            d["distinguishing_features"] = self.distinguishing_features
        if self.clothing_style:
            d["clothing_style"] = self.clothing_style
        if self.accessories:
            d["accessories"] = self.accessories
        if self.other:
            d["other"] = self.other
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PhysicalFeatures:
        """Create from a dictionary.

        Args:
            data: Dictionary of physical features, or None.

        Returns:
            PhysicalFeatures instance (empty if data is None).
        """
        if not data:
            return cls()
        return cls(
            height=data.get("height"),
            build=data.get("build"),
            hair=data.get("hair"),
            eyes=data.get("eyes"),
            skin_tone=data.get("skin_tone"),
            age_appearance=data.get("age_appearance"),
            facial_features=data.get("facial_features"),
            distinguishing_features=data.get("distinguishing_features", []),
            clothing_style=data.get("clothing_style"),
            accessories=data.get("accessories", []),
            other=data.get("other"),
        )

    def __str__(self) -> str:
        return self.to_prompt() or "(no physical features set)"


__all__ = [
    "AGE_GROUPS",
    "BUILDS",
    "EYE_COLORS",
    "HAIR_COLORS",
    "HAIR_TYPES",
    "SKIN_TONES",
    "PhysicalFeatures",
]
