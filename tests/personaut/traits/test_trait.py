"""Tests for trait definitions."""

from __future__ import annotations

from personaut.traits.trait import (
    ALL_TRAITS,
    BEHAVIORAL_TRAITS,
    COGNITIVE_TRAITS,
    DOMINANCE,
    EMOTIONAL_TRAITS,
    INTERPERSONAL_TRAITS,
    TRAIT_METADATA,
    WARMTH,
    Trait,
    get_trait_cluster,
    get_trait_metadata,
    is_valid_trait,
)


class TestTraitConstants:
    """Tests for trait constants."""

    def test_all_traits_count(self) -> None:
        """ALL_TRAITS should contain exactly 17 traits."""
        assert len(ALL_TRAITS) == 17

    def test_all_traits_are_lowercase(self) -> None:
        """All trait values should be lowercase strings."""
        for trait in ALL_TRAITS:
            assert trait == trait.lower()
            assert isinstance(trait, str)

    def test_all_traits_unique(self) -> None:
        """All traits should be unique."""
        assert len(ALL_TRAITS) == len(set(ALL_TRAITS))

    def test_trait_constants_values(self) -> None:
        """Trait constants should have correct string values."""
        assert WARMTH == "warmth"
        assert DOMINANCE == "dominance"


class TestTraitClusters:
    """Tests for trait cluster lists."""

    def test_interpersonal_traits(self) -> None:
        """INTERPERSONAL_TRAITS should contain correct traits."""
        assert "warmth" in INTERPERSONAL_TRAITS
        assert "dominance" in INTERPERSONAL_TRAITS
        assert "social_boldness" in INTERPERSONAL_TRAITS
        assert len(INTERPERSONAL_TRAITS) == 5

    def test_emotional_traits(self) -> None:
        """EMOTIONAL_TRAITS should contain correct traits."""
        assert "emotional_stability" in EMOTIONAL_TRAITS
        assert "apprehension" in EMOTIONAL_TRAITS
        assert "tension" in EMOTIONAL_TRAITS
        assert len(EMOTIONAL_TRAITS) == 4

    def test_cognitive_traits(self) -> None:
        """COGNITIVE_TRAITS should contain correct traits."""
        assert "reasoning" in COGNITIVE_TRAITS
        assert "abstractedness" in COGNITIVE_TRAITS
        assert len(COGNITIVE_TRAITS) == 3

    def test_behavioral_traits(self) -> None:
        """BEHAVIORAL_TRAITS should contain correct traits."""
        assert "liveliness" in BEHAVIORAL_TRAITS
        assert "perfectionism" in BEHAVIORAL_TRAITS
        assert len(BEHAVIORAL_TRAITS) == 5

    def test_clusters_cover_all_traits(self) -> None:
        """All trait clusters should cover all 17 traits."""
        all_from_clusters = INTERPERSONAL_TRAITS + EMOTIONAL_TRAITS + COGNITIVE_TRAITS + BEHAVIORAL_TRAITS
        assert len(all_from_clusters) == 17
        assert set(all_from_clusters) == set(ALL_TRAITS)


class TestTraitClass:
    """Tests for Trait dataclass."""

    def test_trait_creation(self) -> None:
        """Trait should be creatable with all fields."""
        trait = Trait("test", "A test trait", "Low end", "High end")
        assert trait.name == "test"
        assert trait.description == "A test trait"
        assert trait.low_pole == "Low end"
        assert trait.high_pole == "High end"

    def test_trait_str(self) -> None:
        """Trait should return its name when converted to string."""
        trait = Trait("test", "A test trait", "Low end", "High end")
        assert str(trait) == "test"

    def test_trait_is_frozen(self) -> None:
        """Trait should be immutable."""
        trait = Trait("test", "A test trait", "Low end", "High end")
        try:
            trait.name = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised FrozenInstanceError")
        except Exception:
            pass  # Expected


class TestTraitMetadata:
    """Tests for TRAIT_METADATA registry."""

    def test_all_traits_have_metadata(self) -> None:
        """All 17 traits should have metadata entries."""
        assert len(TRAIT_METADATA) == 17

    def test_metadata_matches_traits(self) -> None:
        """Metadata keys should match ALL_TRAITS."""
        assert set(TRAIT_METADATA.keys()) == set(ALL_TRAITS)

    def test_metadata_has_poles(self) -> None:
        """All metadata should have low and high pole descriptions."""
        for trait, metadata in TRAIT_METADATA.items():
            assert metadata.low_pole, f"{trait} missing low_pole"
            assert metadata.high_pole, f"{trait} missing high_pole"

    def test_metadata_names_match_keys(self) -> None:
        """Metadata trait names should match their dictionary keys."""
        for trait, metadata in TRAIT_METADATA.items():
            assert metadata.name == trait


class TestGetTraitMetadata:
    """Tests for get_trait_metadata function."""

    def test_get_valid_trait(self) -> None:
        """get_trait_metadata should return correct data for valid traits."""
        metadata = get_trait_metadata("warmth")
        assert metadata.name == "warmth"
        assert "warmth" in metadata.description.lower() or "interpersonal" in metadata.description.lower()
        assert metadata.low_pole
        assert metadata.high_pole

    def test_get_invalid_trait(self) -> None:
        """get_trait_metadata should raise KeyError for unknown traits."""
        try:
            get_trait_metadata("charisma")
            raise AssertionError("Should have raised KeyError")
        except KeyError:
            pass


class TestIsValidTrait:
    """Tests for is_valid_trait function."""

    def test_valid_trait(self) -> None:
        """is_valid_trait should return True for valid traits."""
        assert is_valid_trait("warmth") is True
        assert is_valid_trait("dominance") is True
        assert is_valid_trait("emotional_stability") is True

    def test_invalid_trait(self) -> None:
        """is_valid_trait should return False for invalid traits."""
        assert is_valid_trait("charisma") is False
        assert is_valid_trait("WARMTH") is False  # Case sensitive
        assert is_valid_trait("") is False


class TestGetTraitCluster:
    """Tests for get_trait_cluster function."""

    def test_interpersonal_cluster(self) -> None:
        """Interpersonal traits should return 'interpersonal'."""
        assert get_trait_cluster("warmth") == "interpersonal"
        assert get_trait_cluster("dominance") == "interpersonal"

    def test_emotional_cluster(self) -> None:
        """Emotional traits should return 'emotional'."""
        assert get_trait_cluster("emotional_stability") == "emotional"
        assert get_trait_cluster("apprehension") == "emotional"

    def test_cognitive_cluster(self) -> None:
        """Cognitive traits should return 'cognitive'."""
        assert get_trait_cluster("reasoning") == "cognitive"
        assert get_trait_cluster("abstractedness") == "cognitive"

    def test_behavioral_cluster(self) -> None:
        """Behavioral traits should return 'behavioral'."""
        assert get_trait_cluster("liveliness") == "behavioral"
        assert get_trait_cluster("perfectionism") == "behavioral"

    def test_invalid_trait(self) -> None:
        """Invalid traits should raise KeyError."""
        try:
            get_trait_cluster("charisma")
            raise AssertionError("Should have raised KeyError")
        except KeyError:
            pass
