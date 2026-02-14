"""TraitProfile class for Personaut PDK.

This module provides the TraitProfile class, which represents the
personality trait configuration of an individual with values for each
trait ranging from 0.0 to 1.0.

Example:
    >>> from personaut.traits.profile import TraitProfile
    >>> profile = TraitProfile()
    >>> profile.set_trait("warmth", 0.8)
    >>> profile.set_trait("dominance", 0.3)
    >>> print(profile.get_trait("warmth"))
    0.8
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from personaut.traits.trait import ALL_TRAITS, is_valid_trait
from personaut.types.exceptions import TraitNotFoundError, TraitValueError


if TYPE_CHECKING:
    from collections.abc import Iterator

    from personaut.types.common import TraitDict


class TraitProfile:
    """Represents the personality trait profile of an individual.

    TraitProfile tracks the value of various traits, each ranging
    from 0.0 (low end of trait) to 1.0 (high end of trait). The midpoint
    (0.5) represents the population average.

    Attributes:
        traits: Dictionary mapping trait names to their current values.

    Example:
        >>> profile = TraitProfile(baseline=0.5)
        >>> profile.set_trait("warmth", 0.9)
        >>> profile.get_trait("warmth")
        0.9
    """

    __slots__ = ("_traits",)

    def __init__(
        self,
        traits: list[str] | None = None,
        baseline: float = 0.5,
    ) -> None:
        """Initialize a TraitProfile.

        Args:
            traits: Optional list of traits to track. If None, tracks
                all 17 standard traits.
            baseline: Initial value for all traits (0.0 to 1.0).
                Default is 0.5 (population average).

        Raises:
            TraitValueError: If baseline is outside [0.0, 1.0].
            TraitNotFoundError: If any trait in the list is unknown.

        Example:
            >>> profile = TraitProfile()  # All 17 traits at 0.5
            >>> profile = TraitProfile(baseline=0.7)  # All at 0.7
            >>> profile = TraitProfile(["warmth", "dominance"])  # Only these two
        """
        if not 0.0 <= baseline <= 1.0:
            raise TraitValueError("baseline", baseline)

        trait_list = traits if traits is not None else ALL_TRAITS

        # Validate all traits
        for trait in trait_list:
            if not is_valid_trait(trait):
                raise TraitNotFoundError(trait)

        self._traits: TraitDict = dict.fromkeys(trait_list, baseline)

    def set_trait(self, trait: str, value: float) -> None:
        """Set the value of a single trait.

        Args:
            trait: Name of the trait to set.
            value: New value for the trait (0.0 to 1.0).

        Raises:
            TraitNotFoundError: If the trait is not tracked.
            TraitValueError: If value is outside [0.0, 1.0].

        Example:
            >>> profile = TraitProfile()
            >>> profile.set_trait("warmth", 0.8)
            >>> profile.get_trait("warmth")
            0.8
        """
        if trait not in self._traits:
            raise TraitNotFoundError(trait)

        if not 0.0 <= value <= 1.0:
            raise TraitValueError(trait, value)

        self._traits[trait] = value

    def set_traits(self, traits: TraitDict) -> None:
        """Set multiple traits at once.

        Args:
            traits: Dictionary mapping trait names to new values.

        Raises:
            TraitNotFoundError: If any trait is not tracked.
            TraitValueError: If any value is outside [0.0, 1.0].

        Example:
            >>> profile = TraitProfile()
            >>> profile.set_traits({"warmth": 0.8, "dominance": 0.3})
        """
        # Validate all traits and values first
        for trait, value in traits.items():
            if trait not in self._traits:
                raise TraitNotFoundError(trait)
            if not 0.0 <= value <= 1.0:
                raise TraitValueError(trait, value)

        # Apply all traits
        for trait, value in traits.items():
            self._traits[trait] = value

    def get_trait(self, trait: str) -> float:
        """Get the current value of a trait.

        Args:
            trait: Name of the trait to query.

        Returns:
            Current value of the trait (0.0 to 1.0).

        Raises:
            TraitNotFoundError: If the trait is not tracked.

        Example:
            >>> profile = TraitProfile()
            >>> profile.get_trait("warmth")
            0.5
        """
        if trait not in self._traits:
            raise TraitNotFoundError(trait)
        return self._traits[trait]

    def to_dict(self) -> TraitDict:
        """Convert trait profile to a dictionary.

        Returns:
            A copy of the internal trait dictionary.

        Example:
            >>> profile = TraitProfile(["warmth", "dominance"])
            >>> profile.set_trait("warmth", 0.8)
            >>> profile.to_dict()
            {'warmth': 0.8, 'dominance': 0.5}
        """
        return dict(self._traits)

    def get_high_traits(self, threshold: float = 0.7) -> list[tuple[str, float]]:
        """Get traits that are above average.

        Args:
            threshold: Minimum value to be considered high.

        Returns:
            List of (trait_name, value) tuples for traits above threshold,
            sorted by value descending.

        Example:
            >>> profile = TraitProfile()
            >>> profile.set_trait("warmth", 0.9)
            >>> profile.set_trait("dominance", 0.8)
            >>> profile.get_high_traits()
            [('warmth', 0.9), ('dominance', 0.8)]
        """
        high = [(t, v) for t, v in self._traits.items() if v >= threshold]
        return sorted(high, key=lambda x: -x[1])

    def get_low_traits(self, threshold: float = 0.3) -> list[tuple[str, float]]:
        """Get traits that are below average.

        Args:
            threshold: Maximum value to be considered low.

        Returns:
            List of (trait_name, value) tuples for traits below threshold,
            sorted by value ascending.

        Example:
            >>> profile = TraitProfile()
            >>> profile.set_trait("warmth", 0.2)
            >>> profile.set_trait("dominance", 0.1)
            >>> profile.get_low_traits()
            [('dominance', 0.1), ('warmth', 0.2)]
        """
        low = [(t, v) for t, v in self._traits.items() if v <= threshold]
        return sorted(low, key=lambda x: x[1])

    def get_extreme_traits(
        self,
        low_threshold: float = 0.3,
        high_threshold: float = 0.7,
    ) -> dict[str, list[tuple[str, float]]]:
        """Get traits at both extremes.

        Args:
            low_threshold: Maximum value to be considered low.
            high_threshold: Minimum value to be considered high.

        Returns:
            Dictionary with 'high' and 'low' keys containing sorted
            trait lists.

        Example:
            >>> profile = TraitProfile()
            >>> profile.set_trait("warmth", 0.9)
            >>> profile.set_trait("dominance", 0.1)
            >>> extremes = profile.get_extreme_traits()
            >>> extremes["high"]
            [('warmth', 0.9)]
        """
        return {
            "high": self.get_high_traits(high_threshold),
            "low": self.get_low_traits(low_threshold),
        }

    def get_deviation_from_average(self) -> float:
        """Calculate how much this profile deviates from average (0.5).

        Returns:
            Average absolute deviation from 0.5 across all traits.

        Example:
            >>> profile = TraitProfile()  # All at 0.5
            >>> profile.get_deviation_from_average()
            0.0
        """
        if not self._traits:
            return 0.0
        deviations = [abs(v - 0.5) for v in self._traits.values()]
        return sum(deviations) / len(deviations)

    def is_similar_to(self, other: TraitProfile, threshold: float = 0.2) -> bool:
        """Check if this profile is similar to another.

        Args:
            other: Another TraitProfile to compare with.
            threshold: Maximum average difference to be considered similar.

        Returns:
            True if the average trait difference is below threshold.

        Example:
            >>> profile1 = TraitProfile()
            >>> profile2 = TraitProfile()
            >>> profile1.is_similar_to(profile2)
            True
        """
        common_traits = set(self._traits.keys()) & set(other._traits.keys())
        if not common_traits:
            return False

        total_diff = sum(abs(self._traits[t] - other._traits[t]) for t in common_traits)
        avg_diff = total_diff / len(common_traits)
        return avg_diff <= threshold

    def blend_with(
        self,
        other: TraitProfile,
        weight: float = 0.5,
    ) -> TraitProfile:
        """Create a new profile blended with another.

        Args:
            other: Another TraitProfile to blend with.
            weight: Weight of the other profile (0.0-1.0).
                0.0 = this profile only, 1.0 = other profile only.

        Returns:
            New TraitProfile with blended values.

        Example:
            >>> profile1 = TraitProfile()
            >>> profile1.set_trait("warmth", 0.9)
            >>> profile2 = TraitProfile()
            >>> profile2.set_trait("warmth", 0.3)
            >>> blended = profile1.blend_with(profile2, 0.5)
            >>> blended.get_trait("warmth")
            0.6
        """
        if not 0.0 <= weight <= 1.0:
            raise TraitValueError("weight", weight)

        # Use intersection of traits
        common_traits = list(set(self._traits.keys()) & set(other._traits.keys()))
        new_profile = TraitProfile(traits=common_traits)

        for trait in common_traits:
            self_val = self._traits[trait]
            other_val = other._traits[trait]
            blended_val = (1 - weight) * self_val + weight * other_val
            new_profile._traits[trait] = blended_val

        return new_profile

    def copy(self) -> TraitProfile:
        """Create a copy of this trait profile.

        Returns:
            A new TraitProfile with the same trait values.

        Example:
            >>> profile1 = TraitProfile()
            >>> profile1.set_trait("warmth", 0.8)
            >>> profile2 = profile1.copy()
            >>> profile2.set_trait("warmth", 0.2)
            >>> profile1.get_trait("warmth")  # Unchanged
            0.8
        """
        new_profile = TraitProfile(traits=list(self._traits.keys()))
        new_profile._traits = dict(self._traits)
        return new_profile

    def __len__(self) -> int:
        """Return the number of tracked traits."""
        return len(self._traits)

    def __contains__(self, trait: str) -> bool:
        """Check if a trait is tracked."""
        return trait in self._traits

    def __iter__(self) -> Iterator[str]:
        """Iterate over tracked trait names."""
        return iter(self._traits)

    def __eq__(self, other: object) -> bool:
        """Check equality with another TraitProfile."""
        if not isinstance(other, TraitProfile):
            return NotImplemented
        return self._traits == other._traits

    def __repr__(self) -> str:
        """Return a string representation of the trait profile."""
        extremes = self.get_extreme_traits()
        high_traits = extremes["high"][:2]
        low_traits = extremes["low"][:2]

        parts = []
        if high_traits:
            parts.append(f"high: {', '.join(t[0] for t in high_traits)}")
        if low_traits:
            parts.append(f"low: {', '.join(t[0] for t in low_traits)}")

        if parts:
            return f"TraitProfile({'; '.join(parts)})"
        return "TraitProfile(average)"


__all__ = [
    "TraitProfile",
]
