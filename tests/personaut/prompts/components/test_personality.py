"""Tests for PersonalityComponent."""

import pytest

from personaut.prompts.components.personality import (
    PersonalityComponent,
    get_trait_description,
    interpret_trait_value,
)
from personaut.traits.profile import TraitProfile


class TestInterpretTraitValue:
    """Tests for interpret_trait_value function."""

    def test_high_trait_value(self) -> None:
        """Test high trait value interpretation."""
        result = interpret_trait_value("warmth", 0.9)
        assert result is not None
        assert "warm" in result or "attentive" in result

    def test_low_trait_value(self) -> None:
        """Test low trait value interpretation."""
        result = interpret_trait_value("warmth", 0.1)
        assert result is not None
        assert "reserved" in result or "impersonal" in result

    def test_neutral_value_returns_none(self) -> None:
        """Test neutral value returns None."""
        result = interpret_trait_value("warmth", 0.5)
        assert result is None

    def test_unknown_trait(self) -> None:
        """Test unknown trait returns None."""
        result = interpret_trait_value("unknown_trait", 0.9)
        assert result is None


class TestGetTraitDescription:
    """Tests for get_trait_description function."""

    def test_high_trait_description(self) -> None:
        """Test high trait description."""
        desc = get_trait_description("warmth", 0.9)
        assert "very" in desc or "notably" in desc

    def test_low_trait_description(self) -> None:
        """Test low trait description."""
        desc = get_trait_description("warmth", 0.1)
        assert "very" in desc or "somewhat" in desc

    def test_moderate_trait_description(self) -> None:
        """Test moderate trait description."""
        desc = get_trait_description("warmth", 0.5)
        assert "moderate" in desc


class TestPersonalityComponent:
    """Tests for PersonalityComponent class."""

    @pytest.fixture
    def component(self) -> PersonalityComponent:
        """Create a component for testing."""
        return PersonalityComponent()

    @pytest.fixture
    def balanced_profile(self) -> TraitProfile:
        """Create a balanced trait profile."""
        return TraitProfile()

    @pytest.fixture
    def extreme_profile(self) -> TraitProfile:
        """Create a profile with extreme traits."""
        profile = TraitProfile()
        profile.set_trait("warmth", 0.9)
        profile.set_trait("dominance", 0.2)
        return profile

    def test_format_balanced_profile(
        self,
        component: PersonalityComponent,
        balanced_profile: TraitProfile,
    ) -> None:
        """Test formatting a balanced profile."""
        text = component.format(balanced_profile)
        assert "balanced" in text.lower() or "fairly" in text.lower()

    def test_format_extreme_profile(
        self,
        component: PersonalityComponent,
        extreme_profile: TraitProfile,
    ) -> None:
        """Test formatting a profile with extreme traits."""
        text = component.format(extreme_profile)
        # Should mention high warmth
        assert "warm" in text.lower() or "outgoing" in text.lower()

    def test_format_with_custom_name(
        self,
        component: PersonalityComponent,
        extreme_profile: TraitProfile,
    ) -> None:
        """Test formatting with custom name."""
        text = component.format(extreme_profile, name="Sarah")
        assert "Sarah" in text

    def test_format_list_style(
        self,
        component: PersonalityComponent,
        extreme_profile: TraitProfile,
    ) -> None:
        """Test list format style."""
        text = component.format(extreme_profile, style="list")
        assert "-" in text  # List markers

    def test_format_brief_style(
        self,
        component: PersonalityComponent,
        extreme_profile: TraitProfile,
    ) -> None:
        """Test brief format style."""
        text = component.format(extreme_profile, style="brief")
        # Should be short
        assert len(text) < 200

    def test_thresholds_configurable(self, balanced_profile: TraitProfile) -> None:
        """Test that thresholds are configurable."""
        # With extreme thresholds, should show balanced
        component = PersonalityComponent(high_threshold=0.95, low_threshold=0.05)
        text = component.format(balanced_profile)
        assert "balanced" in text.lower()
