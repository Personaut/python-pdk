"""Tests for PhysicalFeatures class."""

from __future__ import annotations

from personaut.individuals.physical import (
    AGE_GROUPS,
    BUILDS,
    EYE_COLORS,
    HAIR_COLORS,
    HAIR_TYPES,
    SKIN_TONES,
    PhysicalFeatures,
)


class TestPhysicalFeaturesCreation:
    """Tests for PhysicalFeatures initialization."""

    def test_create_empty(self) -> None:
        """Creating without arguments should produce empty features."""
        pf = PhysicalFeatures()
        assert pf.height is None
        assert pf.build is None
        assert pf.hair is None
        assert pf.eyes is None
        assert pf.skin_tone is None
        assert pf.age_appearance is None
        assert pf.facial_features is None
        assert pf.distinguishing_features == []
        assert pf.clothing_style is None
        assert pf.accessories == []
        assert pf.other is None

    def test_create_with_all_fields(self) -> None:
        """Creating with all fields should populate them."""
        pf = PhysicalFeatures(
            height="5'10\"",
            build="athletic",
            hair="short dark curly hair",
            eyes="brown",
            skin_tone="warm olive",
            age_appearance="mid-30s",
            facial_features="sharp jawline, dimples",
            distinguishing_features=["scar above left eyebrow"],
            clothing_style="casual",
            accessories=["watch", "glasses"],
            other="always smiling",
        )

        assert pf.height == "5'10\""
        assert pf.build == "athletic"
        assert pf.hair == "short dark curly hair"
        assert pf.eyes == "brown"
        assert pf.skin_tone == "warm olive"
        assert pf.age_appearance == "mid-30s"
        assert pf.facial_features == "sharp jawline, dimples"
        assert pf.distinguishing_features == ["scar above left eyebrow"]
        assert pf.clothing_style == "casual"
        assert pf.accessories == ["watch", "glasses"]
        assert pf.other == "always smiling"

    def test_create_with_partial_fields(self) -> None:
        """Creating with some fields should leave others as None."""
        pf = PhysicalFeatures(hair="long red hair", eyes="green")
        assert pf.hair == "long red hair"
        assert pf.eyes == "green"
        assert pf.height is None
        assert pf.build is None


class TestPhysicalFeaturesIsEmpty:
    """Tests for is_empty method."""

    def test_empty_features_is_empty(self) -> None:
        """Empty features should report as empty."""
        pf = PhysicalFeatures()
        assert pf.is_empty() is True

    def test_with_height_not_empty(self) -> None:
        """Features with height should not be empty."""
        pf = PhysicalFeatures(height="tall")
        assert pf.is_empty() is False

    def test_with_build_not_empty(self) -> None:
        """Features with build should not be empty."""
        pf = PhysicalFeatures(build="slim")
        assert pf.is_empty() is False

    def test_with_hair_not_empty(self) -> None:
        """Features with hair should not be empty."""
        pf = PhysicalFeatures(hair="blonde")
        assert pf.is_empty() is False

    def test_with_eyes_not_empty(self) -> None:
        """Features with eyes should not be empty."""
        pf = PhysicalFeatures(eyes="blue")
        assert pf.is_empty() is False

    def test_with_skin_tone_not_empty(self) -> None:
        """Features with skin_tone should not be empty."""
        pf = PhysicalFeatures(skin_tone="olive")
        assert pf.is_empty() is False

    def test_with_age_appearance_not_empty(self) -> None:
        """Features with age_appearance should not be empty."""
        pf = PhysicalFeatures(age_appearance="mid-30s")
        assert pf.is_empty() is False

    def test_with_facial_features_not_empty(self) -> None:
        """Features with facial_features should not be empty."""
        pf = PhysicalFeatures(facial_features="sharp jawline")
        assert pf.is_empty() is False

    def test_with_distinguishing_features_not_empty(self) -> None:
        """Features with distinguishing_features should not be empty."""
        pf = PhysicalFeatures(distinguishing_features=["scar"])
        assert pf.is_empty() is False

    def test_with_clothing_style_not_empty(self) -> None:
        """Features with clothing_style should not be empty."""
        pf = PhysicalFeatures(clothing_style="casual")
        assert pf.is_empty() is False

    def test_with_accessories_not_empty(self) -> None:
        """Features with accessories should not be empty."""
        pf = PhysicalFeatures(accessories=["watch"])
        assert pf.is_empty() is False

    def test_with_other_not_empty(self) -> None:
        """Features with other should not be empty."""
        pf = PhysicalFeatures(other="note")
        assert pf.is_empty() is False


class TestPhysicalFeaturesToPrompt:
    """Tests for to_prompt method."""

    def test_empty_returns_empty_string(self) -> None:
        """Empty features should return empty string."""
        pf = PhysicalFeatures()
        assert pf.to_prompt() == ""

    def test_single_field(self) -> None:
        """Single field should render correctly."""
        pf = PhysicalFeatures(height="tall")
        result = pf.to_prompt()
        assert result == "Height: tall."

    def test_multiple_fields(self) -> None:
        """Multiple fields should be separated by periods."""
        pf = PhysicalFeatures(height="tall", build="lean", eyes="blue")
        result = pf.to_prompt()
        assert "Height: tall" in result
        assert "Build: lean" in result
        assert "Eyes: blue" in result

    def test_age_appearance_uses_appears(self) -> None:
        """Age appearance should use 'Appears' prefix."""
        pf = PhysicalFeatures(age_appearance="mid-30s")
        assert "Appears mid-30s" in pf.to_prompt()

    def test_hair_field(self) -> None:
        """Hair field should render with 'Hair:' prefix."""
        pf = PhysicalFeatures(hair="long red hair")
        assert "Hair: long red hair" in pf.to_prompt()

    def test_skin_tone_field(self) -> None:
        """Skin tone should render with 'Skin tone:' prefix."""
        pf = PhysicalFeatures(skin_tone="warm olive")
        assert "Skin tone: warm olive" in pf.to_prompt()

    def test_facial_features_field(self) -> None:
        """Facial features should render with 'Face:' prefix."""
        pf = PhysicalFeatures(facial_features="sharp jawline")
        assert "Face: sharp jawline" in pf.to_prompt()

    def test_distinguishing_features_joined(self) -> None:
        """Distinguishing features should be comma-joined."""
        pf = PhysicalFeatures(
            distinguishing_features=["scar", "tattoo", "piercing"],
        )
        result = pf.to_prompt()
        assert "Distinguishing features: scar, tattoo, piercing" in result

    def test_clothing_style_field(self) -> None:
        """Clothing style should render with 'Usually wears:' prefix."""
        pf = PhysicalFeatures(clothing_style="casual business")
        assert "Usually wears: casual business" in pf.to_prompt()

    def test_accessories_joined(self) -> None:
        """Accessories should be comma-joined."""
        pf = PhysicalFeatures(accessories=["watch", "glasses"])
        result = pf.to_prompt()
        assert "Accessories: watch, glasses" in result

    def test_other_appended_directly(self) -> None:
        """Other field should be appended directly."""
        pf = PhysicalFeatures(other="always smiling")
        assert "always smiling" in pf.to_prompt()

    def test_full_prompt_ends_with_period(self) -> None:
        """Prompt should end with a period."""
        pf = PhysicalFeatures(height="tall", hair="dark")
        assert pf.to_prompt().endswith(".")

    def test_field_ordering(self) -> None:
        """Fields should appear in a consistent order."""
        pf = PhysicalFeatures(
            eyes="green",
            age_appearance="young",
            height="tall",
            build="lean",
            hair="dark",
        )
        result = pf.to_prompt()
        # age_appearance should come before height
        assert result.index("Appears young") < result.index("Height: tall")
        # height before build
        assert result.index("Height: tall") < result.index("Build: lean")
        # build before hair
        assert result.index("Build: lean") < result.index("Hair: dark")
        # hair before eyes
        assert result.index("Hair: dark") < result.index("Eyes: green")


class TestPhysicalFeaturesToDict:
    """Tests for to_dict method."""

    def test_empty_returns_empty_dict(self) -> None:
        """Empty features should return empty dict."""
        pf = PhysicalFeatures()
        assert pf.to_dict() == {}

    def test_omits_none_fields(self) -> None:
        """None fields should be omitted."""
        pf = PhysicalFeatures(height="tall")
        d = pf.to_dict()
        assert "height" in d
        assert "build" not in d
        assert "hair" not in d

    def test_omits_empty_lists(self) -> None:
        """Empty lists should be omitted."""
        pf = PhysicalFeatures(height="tall")
        d = pf.to_dict()
        assert "distinguishing_features" not in d
        assert "accessories" not in d

    def test_includes_populated_lists(self) -> None:
        """Populated lists should be included."""
        pf = PhysicalFeatures(
            distinguishing_features=["scar"],
            accessories=["watch"],
        )
        d = pf.to_dict()
        assert d["distinguishing_features"] == ["scar"]
        assert d["accessories"] == ["watch"]

    def test_all_fields_serialized(self) -> None:
        """All populated fields should be serialized."""
        pf = PhysicalFeatures(
            height="tall",
            build="lean",
            hair="dark",
            eyes="blue",
            skin_tone="fair",
            age_appearance="young",
            facial_features="dimples",
            distinguishing_features=["scar"],
            clothing_style="casual",
            accessories=["watch"],
            other="note",
        )
        d = pf.to_dict()
        assert d["height"] == "tall"
        assert d["build"] == "lean"
        assert d["hair"] == "dark"
        assert d["eyes"] == "blue"
        assert d["skin_tone"] == "fair"
        assert d["age_appearance"] == "young"
        assert d["facial_features"] == "dimples"
        assert d["distinguishing_features"] == ["scar"]
        assert d["clothing_style"] == "casual"
        assert d["accessories"] == ["watch"]
        assert d["other"] == "note"


class TestPhysicalFeaturesFromDict:
    """Tests for from_dict classmethod."""

    def test_from_none_returns_empty(self) -> None:
        """None input should return empty features."""
        pf = PhysicalFeatures.from_dict(None)
        assert pf.is_empty() is True

    def test_from_empty_dict_returns_empty(self) -> None:
        """Empty dict should return empty features."""
        pf = PhysicalFeatures.from_dict({})
        assert pf.is_empty() is True

    def test_from_dict_with_all_fields(self) -> None:
        """All fields should be restored from dict."""
        data = {
            "height": "5'10\"",
            "build": "athletic",
            "hair": "dark",
            "eyes": "brown",
            "skin_tone": "olive",
            "age_appearance": "30s",
            "facial_features": "dimples",
            "distinguishing_features": ["scar"],
            "clothing_style": "casual",
            "accessories": ["watch"],
            "other": "note",
        }
        pf = PhysicalFeatures.from_dict(data)
        assert pf.height == "5'10\""
        assert pf.build == "athletic"
        assert pf.hair == "dark"
        assert pf.eyes == "brown"
        assert pf.skin_tone == "olive"
        assert pf.age_appearance == "30s"
        assert pf.facial_features == "dimples"
        assert pf.distinguishing_features == ["scar"]
        assert pf.clothing_style == "casual"
        assert pf.accessories == ["watch"]
        assert pf.other == "note"

    def test_from_dict_partial(self) -> None:
        """Partial dict should set provided fields, default others."""
        data = {"hair": "red", "eyes": "green"}
        pf = PhysicalFeatures.from_dict(data)
        assert pf.hair == "red"
        assert pf.eyes == "green"
        assert pf.height is None

    def test_from_dict_missing_lists_default_empty(self) -> None:
        """Missing list fields should default to empty lists."""
        data = {"height": "tall"}
        pf = PhysicalFeatures.from_dict(data)
        assert pf.distinguishing_features == []
        assert pf.accessories == []

    def test_roundtrip_serialization(self) -> None:
        """to_dict -> from_dict should produce equivalent object."""
        original = PhysicalFeatures(
            height="tall",
            build="lean",
            hair="dark curly",
            eyes="green",
            skin_tone="fair",
            age_appearance="mid-20s",
            facial_features="freckles",
            distinguishing_features=["scar", "tattoo"],
            clothing_style="smart casual",
            accessories=["watch", "ring"],
            other="always wears sunglasses indoors",
        )
        restored = PhysicalFeatures.from_dict(original.to_dict())
        assert restored.height == original.height
        assert restored.build == original.build
        assert restored.hair == original.hair
        assert restored.eyes == original.eyes
        assert restored.skin_tone == original.skin_tone
        assert restored.age_appearance == original.age_appearance
        assert restored.facial_features == original.facial_features
        assert restored.distinguishing_features == original.distinguishing_features
        assert restored.clothing_style == original.clothing_style
        assert restored.accessories == original.accessories
        assert restored.other == original.other


class TestPhysicalFeaturesStr:
    """Tests for __str__ method."""

    def test_str_empty(self) -> None:
        """Empty features should show placeholder text."""
        pf = PhysicalFeatures()
        assert str(pf) == "(no physical features set)"

    def test_str_with_data(self) -> None:
        """Features with data should show prompt text."""
        pf = PhysicalFeatures(eyes="blue")
        assert str(pf) == "Eyes: blue."


class TestConstants:
    """Tests for module-level constants."""

    def test_builds_is_list(self) -> None:
        """BUILDS should be a non-empty list of strings."""
        assert isinstance(BUILDS, list)
        assert len(BUILDS) > 0
        assert all(isinstance(b, str) for b in BUILDS)

    def test_eye_colors_is_list(self) -> None:
        """EYE_COLORS should be a non-empty list of strings."""
        assert isinstance(EYE_COLORS, list)
        assert len(EYE_COLORS) > 0

    def test_hair_types_is_list(self) -> None:
        """HAIR_TYPES should be a non-empty list of strings."""
        assert isinstance(HAIR_TYPES, list)
        assert len(HAIR_TYPES) > 0

    def test_hair_colors_is_list(self) -> None:
        """HAIR_COLORS should be a non-empty list of strings."""
        assert isinstance(HAIR_COLORS, list)
        assert len(HAIR_COLORS) > 0

    def test_skin_tones_is_list(self) -> None:
        """SKIN_TONES should be a non-empty list of strings."""
        assert isinstance(SKIN_TONES, list)
        assert len(SKIN_TONES) > 0

    def test_age_groups_is_list(self) -> None:
        """AGE_GROUPS should be a non-empty list of strings."""
        assert isinstance(AGE_GROUPS, list)
        assert len(AGE_GROUPS) > 0
