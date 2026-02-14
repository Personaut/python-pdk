"""Tests for SituationComponent."""

import pytest

from personaut.prompts.components.situation import (
    MODALITY_DESCRIPTIONS,
    SituationComponent,
)
from personaut.situations.situation import Situation, create_situation
from personaut.types.modality import Modality


class TestModalityDescriptions:
    """Tests for modality descriptions."""

    def test_all_modalities_have_descriptions(self) -> None:
        """Test that all modalities have descriptions."""
        for modality in Modality:
            assert modality in MODALITY_DESCRIPTIONS

    def test_descriptions_have_required_keys(self) -> None:
        """Test that descriptions have required keys."""
        for _modality, info in MODALITY_DESCRIPTIONS.items():
            assert "setting" in info
            assert "cues" in info
            assert "timing" in info


class TestSituationComponent:
    """Tests for SituationComponent class."""

    @pytest.fixture
    def component(self) -> SituationComponent:
        """Create a component for testing."""
        return SituationComponent()

    @pytest.fixture
    def in_person_situation(self) -> Situation:
        """Create an in-person situation."""
        return create_situation(
            modality=Modality.IN_PERSON,
            description="Coffee shop meeting",
            location="Downtown Cafe",
        )

    @pytest.fixture
    def text_situation(self) -> Situation:
        """Create a text message situation."""
        return create_situation(
            modality=Modality.TEXT_MESSAGE,
            description="Catching up with friend",
        )

    def test_format_in_person(
        self,
        component: SituationComponent,
        in_person_situation: Situation,
    ) -> None:
        """Test formatting in-person situation."""
        text = component.format(in_person_situation)
        assert "Downtown Cafe" in text
        assert "physically present" in text.lower()

    def test_format_text_message(
        self,
        component: SituationComponent,
        text_situation: Situation,
    ) -> None:
        """Test formatting text message situation."""
        text = component.format(text_situation)
        assert "text message" in text.lower()

    def test_format_with_name(
        self,
        component: SituationComponent,
        in_person_situation: Situation,
    ) -> None:
        """Test formatting with custom name."""
        text = component.format(in_person_situation, name="Sarah")
        assert "Sarah" in text

    def test_format_includes_description(
        self,
        component: SituationComponent,
        in_person_situation: Situation,
    ) -> None:
        """Test that description is included."""
        text = component.format(in_person_situation)
        assert "Coffee shop meeting" in text

    def test_modality_traits_included(
        self,
        component: SituationComponent,
        in_person_situation: Situation,
    ) -> None:
        """Test that modality traits are included."""
        text = component.format(in_person_situation)
        assert "body language" in text.lower() or "cues" in text.lower()

    def test_modality_traits_disabled(
        self,
        in_person_situation: Situation,
    ) -> None:
        """Test disabling modality traits."""
        component = SituationComponent(include_modality_traits=False)
        text = component.format(in_person_situation)
        # Should not have the detailed cue description
        assert "environmental cues" not in text

    def test_format_brief(
        self,
        component: SituationComponent,
        in_person_situation: Situation,
    ) -> None:
        """Test brief format."""
        text = component.format_brief(in_person_situation)
        assert "Downtown Cafe" in text

    def test_format_modality_context(
        self,
        component: SituationComponent,
    ) -> None:
        """Test format_modality_context method."""
        text = component.format_modality_context(Modality.VIDEO_CALL)
        assert "video" in text.lower() or "facial" in text.lower()

    def test_dict_situation(self, component: SituationComponent) -> None:
        """Test with dict-based situation."""
        situation = {
            "modality": "in_person",
            "description": "Meeting",
            "location": "Office",
        }
        text = component.format(situation)
        assert "Office" in text
