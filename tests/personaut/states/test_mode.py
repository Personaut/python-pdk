"""Tests for state calculation modes."""

from __future__ import annotations

import pytest

from personaut.states.mode import (
    AVERAGE,
    CUSTOM,
    MAXIMUM,
    MINIMUM,
    RECENT,
    StateMode,
    parse_state_mode,
)


class TestStateModeEnum:
    """Tests for StateMode enum."""

    def test_all_modes_defined(self) -> None:
        """All expected modes should be defined."""
        assert len(StateMode) == 5

    def test_mode_values(self) -> None:
        """Mode values should be lowercase strings."""
        assert StateMode.AVERAGE.value == "average"
        assert StateMode.MAXIMUM.value == "maximum"
        assert StateMode.MINIMUM.value == "minimum"
        assert StateMode.RECENT.value == "recent"
        assert StateMode.CUSTOM.value == "custom"

    def test_string_constants_match_enum(self) -> None:
        """String constants should match enum values."""
        assert StateMode.AVERAGE.value == AVERAGE
        assert StateMode.MAXIMUM.value == MAXIMUM
        assert StateMode.MINIMUM.value == MINIMUM
        assert StateMode.RECENT.value == RECENT
        assert StateMode.CUSTOM.value == CUSTOM


class TestStateModeDescription:
    """Tests for StateMode description property."""

    def test_all_modes_have_descriptions(self) -> None:
        """All modes should have non-empty descriptions."""
        for mode in StateMode:
            assert mode.description
            assert len(mode.description) > 10

    def test_average_description(self) -> None:
        """AVERAGE should have appropriate description."""
        assert "average" in StateMode.AVERAGE.description.lower()

    def test_maximum_description(self) -> None:
        """MAXIMUM should have appropriate description."""
        assert "maximum" in StateMode.MAXIMUM.description.lower()

    def test_custom_description(self) -> None:
        """CUSTOM should have appropriate description."""
        assert "custom" in StateMode.CUSTOM.description.lower()


class TestStateModeRequiresCustomFunction:
    """Tests for requires_custom_function property."""

    def test_custom_requires_function(self) -> None:
        """CUSTOM mode should require a custom function."""
        assert StateMode.CUSTOM.requires_custom_function is True

    def test_other_modes_dont_require_function(self) -> None:
        """Non-CUSTOM modes should not require a function."""
        assert StateMode.AVERAGE.requires_custom_function is False
        assert StateMode.MAXIMUM.requires_custom_function is False
        assert StateMode.MINIMUM.requires_custom_function is False
        assert StateMode.RECENT.requires_custom_function is False


class TestParseStateMode:
    """Tests for parse_state_mode function."""

    def test_parse_string_value(self) -> None:
        """Should parse valid string values."""
        assert parse_state_mode("average") == StateMode.AVERAGE
        assert parse_state_mode("maximum") == StateMode.MAXIMUM
        assert parse_state_mode("minimum") == StateMode.MINIMUM

    def test_parse_enum_value(self) -> None:
        """Should return enum values unchanged."""
        assert parse_state_mode(StateMode.AVERAGE) == StateMode.AVERAGE
        assert parse_state_mode(StateMode.CUSTOM) == StateMode.CUSTOM

    def test_parse_invalid_value(self) -> None:
        """Should raise ValueError for invalid values."""
        with pytest.raises(ValueError, match="Unknown state mode"):
            parse_state_mode("invalid")

    def test_parse_case_insensitive(self) -> None:
        """Should parse case-insensitively."""
        assert parse_state_mode("AVERAGE") == StateMode.AVERAGE
        assert parse_state_mode("Average") == StateMode.AVERAGE
