"""Tests for TraitProfile class."""

from __future__ import annotations

import pytest

from personaut.traits.profile import TraitProfile
from personaut.types.exceptions import TraitNotFoundError, TraitValueError


class TestTraitProfileCreation:
    """Tests for TraitProfile initialization."""

    def test_default_creation(self) -> None:
        """Default creation should include all 17 traits at 0.5."""
        profile = TraitProfile()
        assert len(profile) == 17
        assert profile.get_trait("warmth") == 0.5

    def test_creation_with_baseline(self) -> None:
        """Creation with baseline should set all traits to that value."""
        profile = TraitProfile(baseline=0.7)
        assert profile.get_trait("warmth") == 0.7
        assert profile.get_trait("dominance") == 0.7

    def test_creation_with_subset(self) -> None:
        """Creation with trait list should only track those traits."""
        profile = TraitProfile(traits=["warmth", "dominance"])
        assert len(profile) == 2
        assert "warmth" in profile
        assert "dominance" in profile
        assert "reasoning" not in profile

    def test_creation_with_invalid_baseline(self) -> None:
        """Creation with invalid baseline should raise TraitValueError."""
        with pytest.raises(TraitValueError):
            TraitProfile(baseline=1.5)
        with pytest.raises(TraitValueError):
            TraitProfile(baseline=-0.1)

    def test_creation_with_invalid_trait(self) -> None:
        """Creation with unknown trait should raise TraitNotFoundError."""
        with pytest.raises(TraitNotFoundError):
            TraitProfile(traits=["warmth", "charisma"])


class TestSetTrait:
    """Tests for set_trait method."""

    def test_set_valid_trait(self) -> None:
        """Should set trait value successfully."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.9)
        assert profile.get_trait("warmth") == 0.9

    def test_set_trait_boundary_values(self) -> None:
        """Should accept boundary values 0.0 and 1.0."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.0)
        assert profile.get_trait("warmth") == 0.0
        profile.set_trait("warmth", 1.0)
        assert profile.get_trait("warmth") == 1.0

    def test_set_unknown_trait(self) -> None:
        """Should raise TraitNotFoundError for unknown traits."""
        profile = TraitProfile()
        with pytest.raises(TraitNotFoundError):
            profile.set_trait("charisma", 0.5)

    def test_set_trait_invalid_value_high(self) -> None:
        """Should raise TraitValueError for values > 1.0."""
        profile = TraitProfile()
        with pytest.raises(TraitValueError):
            profile.set_trait("warmth", 1.1)

    def test_set_trait_invalid_value_low(self) -> None:
        """Should raise TraitValueError for values < 0.0."""
        profile = TraitProfile()
        with pytest.raises(TraitValueError):
            profile.set_trait("warmth", -0.1)


class TestSetTraits:
    """Tests for set_traits method."""

    def test_set_multiple_traits(self) -> None:
        """Should set multiple traits at once."""
        profile = TraitProfile()
        profile.set_traits({"warmth": 0.9, "dominance": 0.3})
        assert profile.get_trait("warmth") == 0.9
        assert profile.get_trait("dominance") == 0.3

    def test_set_traits_invalid_trait(self) -> None:
        """Should raise TraitNotFoundError for unknown traits."""
        profile = TraitProfile()
        with pytest.raises(TraitNotFoundError):
            profile.set_traits({"warmth": 0.9, "charisma": 0.5})

    def test_set_traits_invalid_value(self) -> None:
        """Should raise TraitValueError for invalid values."""
        profile = TraitProfile()
        with pytest.raises(TraitValueError):
            profile.set_traits({"warmth": 1.5})


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict_returns_copy(self) -> None:
        """Should return a copy of the internal dictionary."""
        profile = TraitProfile(traits=["warmth", "dominance"])
        profile.set_trait("warmth", 0.8)
        result = profile.to_dict()
        result["warmth"] = 0.1  # Modify the returned dict
        assert profile.get_trait("warmth") == 0.8  # Original unchanged

    def test_to_dict_contents(self) -> None:
        """Should return dictionary with correct values."""
        profile = TraitProfile(traits=["warmth", "dominance"])
        profile.set_trait("warmth", 0.8)
        result = profile.to_dict()
        assert result == {"warmth": 0.8, "dominance": 0.5}


class TestGetHighLowTraits:
    """Tests for get_high_traits and get_low_traits methods."""

    def test_get_high_traits(self) -> None:
        """Should return traits above threshold."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.9)
        profile.set_trait("dominance", 0.8)
        high = profile.get_high_traits()
        trait_names = [t[0] for t in high]
        assert "warmth" in trait_names
        assert "dominance" in trait_names

    def test_get_high_traits_sorted(self) -> None:
        """High traits should be sorted by value descending."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.9)
        profile.set_trait("dominance", 0.8)
        high = profile.get_high_traits()
        # Filter to only our set traits
        our_high = [t for t in high if t[0] in ["warmth", "dominance"]]
        assert our_high[0] == ("warmth", 0.9)
        assert our_high[1] == ("dominance", 0.8)

    def test_get_low_traits(self) -> None:
        """Should return traits below threshold."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.2)
        profile.set_trait("dominance", 0.1)
        low = profile.get_low_traits()
        trait_names = [t[0] for t in low]
        assert "warmth" in trait_names
        assert "dominance" in trait_names

    def test_get_low_traits_sorted(self) -> None:
        """Low traits should be sorted by value ascending."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.2)
        profile.set_trait("dominance", 0.1)
        low = profile.get_low_traits()
        # Filter to only our set traits
        our_low = [t for t in low if t[0] in ["warmth", "dominance"]]
        assert our_low[0] == ("dominance", 0.1)
        assert our_low[1] == ("warmth", 0.2)


class TestGetExtremeTraits:
    """Tests for get_extreme_traits method."""

    def test_get_extreme_traits(self) -> None:
        """Should return both high and low extreme traits."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.9)
        profile.set_trait("dominance", 0.1)
        extremes = profile.get_extreme_traits()
        assert "high" in extremes
        assert "low" in extremes
        high_names = [t[0] for t in extremes["high"]]
        low_names = [t[0] for t in extremes["low"]]
        assert "warmth" in high_names
        assert "dominance" in low_names


class TestDeviationFromAverage:
    """Tests for get_deviation_from_average method."""

    def test_no_deviation(self) -> None:
        """All traits at 0.5 should have zero deviation."""
        profile = TraitProfile()
        assert profile.get_deviation_from_average() == 0.0

    def test_max_deviation(self) -> None:
        """All traits at extremes should have high deviation."""
        profile = TraitProfile(traits=["warmth", "dominance"])
        profile.set_trait("warmth", 1.0)
        profile.set_trait("dominance", 0.0)
        assert profile.get_deviation_from_average() == 0.5

    def test_partial_deviation(self) -> None:
        """Mixed traits should have partial deviation."""
        profile = TraitProfile(traits=["warmth", "dominance"])
        profile.set_trait("warmth", 0.7)  # 0.2 deviation
        profile.set_trait("dominance", 0.3)  # 0.2 deviation
        assert abs(profile.get_deviation_from_average() - 0.2) < 0.001


class TestIsSimilarTo:
    """Tests for is_similar_to method."""

    def test_same_profiles_similar(self) -> None:
        """Identical profiles should be similar."""
        profile1 = TraitProfile()
        profile2 = TraitProfile()
        assert profile1.is_similar_to(profile2) is True

    def test_different_profiles_not_similar(self) -> None:
        """Very different profiles should not be similar."""
        # Use subset profiles so one different trait matters
        profile1 = TraitProfile(traits=["warmth"])
        profile2 = TraitProfile(traits=["warmth"])
        profile1.set_trait("warmth", 1.0)
        profile2.set_trait("warmth", 0.0)
        # With just one trait, difference is 1.0 which exceeds 0.1 threshold
        assert profile1.is_similar_to(profile2, threshold=0.1) is False


class TestBlendWith:
    """Tests for blend_with method."""

    def test_blend_50_50(self) -> None:
        """50/50 blend should average values."""
        profile1 = TraitProfile(traits=["warmth"])
        profile2 = TraitProfile(traits=["warmth"])
        profile1.set_trait("warmth", 0.9)
        profile2.set_trait("warmth", 0.3)
        blended = profile1.blend_with(profile2, 0.5)
        assert abs(blended.get_trait("warmth") - 0.6) < 0.001

    def test_blend_weight_0(self) -> None:
        """Weight 0 should use only first profile."""
        profile1 = TraitProfile(traits=["warmth"])
        profile2 = TraitProfile(traits=["warmth"])
        profile1.set_trait("warmth", 0.9)
        profile2.set_trait("warmth", 0.3)
        blended = profile1.blend_with(profile2, 0.0)
        assert blended.get_trait("warmth") == 0.9

    def test_blend_weight_1(self) -> None:
        """Weight 1 should use only second profile."""
        profile1 = TraitProfile(traits=["warmth"])
        profile2 = TraitProfile(traits=["warmth"])
        profile1.set_trait("warmth", 0.9)
        profile2.set_trait("warmth", 0.3)
        blended = profile1.blend_with(profile2, 1.0)
        assert blended.get_trait("warmth") == 0.3


class TestCopy:
    """Tests for copy method."""

    def test_copy_creates_independent_profile(self) -> None:
        """Copy should be independent of original."""
        profile1 = TraitProfile()
        profile1.set_trait("warmth", 0.8)
        profile2 = profile1.copy()
        profile2.set_trait("warmth", 0.2)
        assert profile1.get_trait("warmth") == 0.8
        assert profile2.get_trait("warmth") == 0.2


class TestDunderMethods:
    """Tests for dunder methods."""

    def test_len(self) -> None:
        """len() should return number of tracked traits."""
        profile = TraitProfile(traits=["warmth", "dominance"])
        assert len(profile) == 2

    def test_contains(self) -> None:
        """in operator should check if trait is tracked."""
        profile = TraitProfile(traits=["warmth"])
        assert "warmth" in profile
        assert "dominance" not in profile

    def test_iter(self) -> None:
        """Should be iterable over trait names."""
        profile = TraitProfile(traits=["warmth", "dominance"])
        traits = list(profile)
        assert "warmth" in traits
        assert "dominance" in traits

    def test_eq(self) -> None:
        """Equality should compare trait values."""
        profile1 = TraitProfile(traits=["warmth"])
        profile2 = TraitProfile(traits=["warmth"])
        profile1.set_trait("warmth", 0.8)
        profile2.set_trait("warmth", 0.8)
        assert profile1 == profile2

    def test_repr(self) -> None:
        """repr should show extreme traits."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.9)
        repr_str = repr(profile)
        assert "TraitProfile" in repr_str

    def test_repr_average(self) -> None:
        """repr should show average for balanced profile."""
        profile = TraitProfile()
        assert "average" in repr(profile)
