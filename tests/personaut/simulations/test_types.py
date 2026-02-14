"""Tests for simulation types."""

from __future__ import annotations

import pytest

from personaut.simulations.types import (
    CONVERSATION,
    LIVE_CONVERSATION,
    OUTCOME_SUMMARY,
    SURVEY,
    SimulationType,
    parse_simulation_type,
)


class TestSimulationType:
    """Tests for SimulationType enum."""

    def test_all_types_exist(self) -> None:
        """Test all expected simulation types exist."""
        assert SimulationType.CONVERSATION is not None
        assert SimulationType.SURVEY is not None
        assert SimulationType.OUTCOME_SUMMARY is not None
        assert SimulationType.LIVE_CONVERSATION is not None

    def test_string_values(self) -> None:
        """Test simulation types have correct string values."""
        assert SimulationType.CONVERSATION.value == "conversation"
        assert SimulationType.SURVEY.value == "survey"
        assert SimulationType.OUTCOME_SUMMARY.value == "outcome_summary"
        assert SimulationType.LIVE_CONVERSATION.value == "live_conversation"

    def test_description_property(self) -> None:
        """Test description property returns non-empty strings."""
        for sim_type in SimulationType:
            assert sim_type.description
            assert isinstance(sim_type.description, str)

    def test_is_interactive_property(self) -> None:
        """Test is_interactive correctly identifies live simulations."""
        assert not SimulationType.CONVERSATION.is_interactive
        assert not SimulationType.SURVEY.is_interactive
        assert not SimulationType.OUTCOME_SUMMARY.is_interactive
        assert SimulationType.LIVE_CONVERSATION.is_interactive

    def test_supports_multi_turn_property(self) -> None:
        """Test supports_multi_turn correctly identifies dialogue types."""
        assert SimulationType.CONVERSATION.supports_multi_turn
        assert not SimulationType.SURVEY.supports_multi_turn
        assert not SimulationType.OUTCOME_SUMMARY.supports_multi_turn
        assert SimulationType.LIVE_CONVERSATION.supports_multi_turn

    def test_default_style_property(self) -> None:
        """Test default_style returns a valid style for each type."""
        expected_styles = {
            SimulationType.CONVERSATION: "script",
            SimulationType.SURVEY: "questionnaire",
            SimulationType.OUTCOME_SUMMARY: "narrative",
            SimulationType.LIVE_CONVERSATION: "json",
        }
        for sim_type, expected in expected_styles.items():
            assert sim_type.default_style == expected


class TestStringConstants:
    """Tests for string constants."""

    def test_constants_match_enum_values(self) -> None:
        """Test constants match their enum counterparts."""
        assert SimulationType.CONVERSATION.value == CONVERSATION
        assert SimulationType.SURVEY.value == SURVEY
        assert SimulationType.OUTCOME_SUMMARY.value == OUTCOME_SUMMARY
        assert SimulationType.LIVE_CONVERSATION.value == LIVE_CONVERSATION


class TestParseSimulationType:
    """Tests for parse_simulation_type function."""

    def test_parse_string_values(self) -> None:
        """Test parsing string values."""
        assert parse_simulation_type("conversation") == SimulationType.CONVERSATION
        assert parse_simulation_type("survey") == SimulationType.SURVEY
        assert parse_simulation_type("outcome_summary") == SimulationType.OUTCOME_SUMMARY
        assert parse_simulation_type("live_conversation") == SimulationType.LIVE_CONVERSATION

    def test_parse_enum_values(self) -> None:
        """Test parsing enum values returns same enum."""
        for sim_type in SimulationType:
            assert parse_simulation_type(sim_type) is sim_type

    def test_parse_invalid_value_raises(self) -> None:
        """Test parsing invalid value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid simulation type"):
            parse_simulation_type("not_a_type")
