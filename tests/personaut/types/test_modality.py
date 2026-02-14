"""Tests for modality types."""

from __future__ import annotations

import pytest

from personaut.types.modality import (
    EMAIL,
    IN_PERSON,
    PHONE_CALL,
    SURVEY,
    TEXT_MESSAGE,
    VIDEO_CALL,
    Modality,
    parse_modality,
)


class TestModalityEnum:
    """Tests for Modality enum."""

    def test_all_modalities_defined(self) -> None:
        """All 6 modalities should be defined."""
        assert len(Modality) == 6

    def test_modality_values(self) -> None:
        """Modalities should have correct string values."""
        assert Modality.IN_PERSON.value == "in_person"
        assert Modality.TEXT_MESSAGE.value == "text_message"
        assert Modality.EMAIL.value == "email"
        assert Modality.PHONE_CALL.value == "phone_call"
        assert Modality.VIDEO_CALL.value == "video_call"
        assert Modality.SURVEY.value == "survey"

    def test_string_constants_match_enum(self) -> None:
        """String constants should match enum values."""
        assert Modality.IN_PERSON.value == IN_PERSON
        assert Modality.TEXT_MESSAGE.value == TEXT_MESSAGE
        assert Modality.EMAIL.value == EMAIL
        assert Modality.PHONE_CALL.value == PHONE_CALL
        assert Modality.VIDEO_CALL.value == VIDEO_CALL
        assert Modality.SURVEY.value == SURVEY


class TestModalityDescription:
    """Tests for modality description property."""

    def test_all_modalities_have_descriptions(self) -> None:
        """All modalities should have descriptions."""
        for modality in Modality:
            assert modality.description
            assert isinstance(modality.description, str)
            assert len(modality.description) > 10  # Meaningful description

    def test_in_person_description(self) -> None:
        """IN_PERSON should describe face-to-face communication."""
        desc = Modality.IN_PERSON.description.lower()
        assert "face" in desc or "non-verbal" in desc


class TestModalityIsSynchronous:
    """Tests for is_synchronous property."""

    def test_synchronous_modalities(self) -> None:
        """Real-time modalities should be synchronous."""
        assert Modality.IN_PERSON.is_synchronous is True
        assert Modality.PHONE_CALL.is_synchronous is True
        assert Modality.VIDEO_CALL.is_synchronous is True

    def test_asynchronous_modalities(self) -> None:
        """Non-real-time modalities should be asynchronous."""
        assert Modality.TEXT_MESSAGE.is_synchronous is False
        assert Modality.EMAIL.is_synchronous is False
        assert Modality.SURVEY.is_synchronous is False


class TestModalityVisualCues:
    """Tests for has_visual_cues property."""

    def test_visual_modalities(self) -> None:
        """Visual modalities should have visual cues."""
        assert Modality.IN_PERSON.has_visual_cues is True
        assert Modality.VIDEO_CALL.has_visual_cues is True

    def test_non_visual_modalities(self) -> None:
        """Non-visual modalities should not have visual cues."""
        assert Modality.TEXT_MESSAGE.has_visual_cues is False
        assert Modality.EMAIL.has_visual_cues is False
        assert Modality.PHONE_CALL.has_visual_cues is False
        assert Modality.SURVEY.has_visual_cues is False


class TestModalityAudioCues:
    """Tests for has_audio_cues property."""

    def test_audio_modalities(self) -> None:
        """Audio modalities should have audio cues."""
        assert Modality.IN_PERSON.has_audio_cues is True
        assert Modality.PHONE_CALL.has_audio_cues is True
        assert Modality.VIDEO_CALL.has_audio_cues is True

    def test_non_audio_modalities(self) -> None:
        """Text-only modalities should not have audio cues."""
        assert Modality.TEXT_MESSAGE.has_audio_cues is False
        assert Modality.EMAIL.has_audio_cues is False
        assert Modality.SURVEY.has_audio_cues is False


class TestModalityUiTemplate:
    """Tests for ui_template property."""

    def test_all_modalities_have_templates(self) -> None:
        """All modalities should have UI templates."""
        for modality in Modality:
            assert modality.ui_template
            assert modality.ui_template.endswith(".html")

    def test_template_paths(self) -> None:
        """UI templates should have correct paths."""
        assert "text_message" in Modality.TEXT_MESSAGE.ui_template
        assert "email" in Modality.EMAIL.ui_template
        assert "in_person" in Modality.IN_PERSON.ui_template


class TestModalityFormalityLevel:
    """Tests for formality_level property."""

    def test_casual_modalities(self) -> None:
        """Casual modalities should be marked as casual."""
        assert Modality.IN_PERSON.formality_level == "casual"
        assert Modality.TEXT_MESSAGE.formality_level == "casual"

    def test_semi_formal_modalities(self) -> None:
        """Semi-formal modalities should be marked as semi-formal."""
        assert Modality.EMAIL.formality_level == "semi-formal"
        assert Modality.PHONE_CALL.formality_level == "semi-formal"
        assert Modality.VIDEO_CALL.formality_level == "semi-formal"

    def test_formal_modalities(self) -> None:
        """Formal modalities should be marked as formal."""
        assert Modality.SURVEY.formality_level == "formal"


class TestParseModality:
    """Tests for parse_modality function."""

    def test_parse_string_value(self) -> None:
        """parse_modality should convert strings to Modality."""
        assert parse_modality("text_message") == Modality.TEXT_MESSAGE
        assert parse_modality("email") == Modality.EMAIL
        assert parse_modality("in_person") == Modality.IN_PERSON

    def test_parse_modality_enum(self) -> None:
        """parse_modality should pass through Modality enum values."""
        assert parse_modality(Modality.TEXT_MESSAGE) == Modality.TEXT_MESSAGE
        assert parse_modality(Modality.EMAIL) == Modality.EMAIL

    def test_parse_invalid_value(self) -> None:
        """parse_modality should raise ValueError for invalid values."""
        with pytest.raises(ValueError, match="Invalid modality"):
            parse_modality("invalid_modality")

    def test_parse_all_string_values(self) -> None:
        """parse_modality should work with all valid string values."""
        for modality in Modality:
            parsed = parse_modality(modality.value)
            assert parsed == modality
