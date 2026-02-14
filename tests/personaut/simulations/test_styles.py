"""Tests for simulation styles."""

from __future__ import annotations

import pytest

from personaut.simulations.styles import (
    JSON,
    NARRATIVE,
    QUESTIONNAIRE,
    SCRIPT,
    TXT,
    SimulationStyle,
    parse_simulation_style,
)


class TestSimulationStyle:
    """Tests for SimulationStyle enum."""

    def test_all_styles_exist(self) -> None:
        """Test all expected simulation styles exist."""
        assert SimulationStyle.SCRIPT is not None
        assert SimulationStyle.QUESTIONNAIRE is not None
        assert SimulationStyle.NARRATIVE is not None
        assert SimulationStyle.JSON is not None
        assert SimulationStyle.TXT is not None

    def test_string_values(self) -> None:
        """Test simulation styles have correct string values."""
        assert SimulationStyle.SCRIPT.value == "script"
        assert SimulationStyle.QUESTIONNAIRE.value == "questionnaire"
        assert SimulationStyle.NARRATIVE.value == "narrative"
        assert SimulationStyle.JSON.value == "json"
        assert SimulationStyle.TXT.value == "txt"

    def test_description_property(self) -> None:
        """Test description property returns non-empty strings."""
        for style in SimulationStyle:
            assert style.description
            assert isinstance(style.description, str)

    def test_extension_property(self) -> None:
        """Test extension property returns valid extensions."""
        for style in SimulationStyle:
            assert style.extension in ("txt", "json")

    def test_json_extension_is_json(self) -> None:
        """Test JSON style has json extension."""
        assert SimulationStyle.JSON.extension == "json"

    def test_is_structured_property(self) -> None:
        """Test is_structured correctly identifies JSON."""
        assert SimulationStyle.JSON.is_structured
        assert not SimulationStyle.SCRIPT.is_structured
        assert not SimulationStyle.QUESTIONNAIRE.is_structured
        assert not SimulationStyle.NARRATIVE.is_structured
        assert not SimulationStyle.TXT.is_structured

    def test_supports_metadata_property(self) -> None:
        """Test supports_metadata identifies correct styles."""
        assert SimulationStyle.JSON.supports_metadata
        assert SimulationStyle.QUESTIONNAIRE.supports_metadata
        assert not SimulationStyle.SCRIPT.supports_metadata
        assert not SimulationStyle.NARRATIVE.supports_metadata
        assert not SimulationStyle.TXT.supports_metadata


class TestStringConstants:
    """Tests for string constants."""

    def test_constants_match_enum_values(self) -> None:
        """Test constants match their enum counterparts."""
        assert SimulationStyle.SCRIPT.value == SCRIPT
        assert SimulationStyle.QUESTIONNAIRE.value == QUESTIONNAIRE
        assert SimulationStyle.NARRATIVE.value == NARRATIVE
        assert SimulationStyle.JSON.value == JSON
        assert SimulationStyle.TXT.value == TXT


class TestParseSimulationStyle:
    """Tests for parse_simulation_style function."""

    def test_parse_string_values(self) -> None:
        """Test parsing string values."""
        assert parse_simulation_style("script") == SimulationStyle.SCRIPT
        assert parse_simulation_style("questionnaire") == SimulationStyle.QUESTIONNAIRE
        assert parse_simulation_style("narrative") == SimulationStyle.NARRATIVE
        assert parse_simulation_style("json") == SimulationStyle.JSON
        assert parse_simulation_style("txt") == SimulationStyle.TXT

    def test_parse_enum_values(self) -> None:
        """Test parsing enum values returns same enum."""
        for style in SimulationStyle:
            assert parse_simulation_style(style) is style

    def test_parse_invalid_value_raises(self) -> None:
        """Test parsing invalid value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid simulation style"):
            parse_simulation_style("not_a_style")
