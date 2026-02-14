"""Tests for individual types."""

from __future__ import annotations

import pytest

from personaut.types.individual import (
    HUMAN,
    NONTRACKED,
    SIMULATED,
    IndividualType,
    parse_individual_type,
)


class TestIndividualTypeEnum:
    """Tests for IndividualType enum."""

    def test_all_types_defined(self) -> None:
        """All 3 individual types should be defined."""
        assert len(IndividualType) == 3

    def test_type_values(self) -> None:
        """Individual types should have correct string values."""
        assert IndividualType.SIMULATED.value == "simulated"
        assert IndividualType.HUMAN.value == "human"
        assert IndividualType.NONTRACKED.value == "nontracked"

    def test_string_constants_match_enum(self) -> None:
        """String constants should match enum values."""
        assert IndividualType.SIMULATED.value == SIMULATED
        assert IndividualType.HUMAN.value == HUMAN
        assert IndividualType.NONTRACKED.value == NONTRACKED


class TestIndividualTypeDescription:
    """Tests for description property."""

    def test_all_types_have_descriptions(self) -> None:
        """All individual types should have descriptions."""
        for individual_type in IndividualType:
            assert individual_type.description
            assert isinstance(individual_type.description, str)
            assert len(individual_type.description) > 20

    def test_simulated_description(self) -> None:
        """SIMULATED should describe AI-driven persona."""
        desc = IndividualType.SIMULATED.description.lower()
        assert "ai" in desc or "persona" in desc

    def test_human_description(self) -> None:
        """HUMAN should describe real participant."""
        desc = IndividualType.HUMAN.description.lower()
        assert "human" in desc or "real" in desc


class TestIndividualTypeHasEmotionalState:
    """Tests for has_emotional_state property."""

    def test_simulated_has_emotional_state(self) -> None:
        """SIMULATED should have emotional state tracking."""
        assert IndividualType.SIMULATED.has_emotional_state is True

    def test_human_no_emotional_state(self) -> None:
        """HUMAN should not have emotional state tracking."""
        assert IndividualType.HUMAN.has_emotional_state is False

    def test_nontracked_no_emotional_state(self) -> None:
        """NONTRACKED should not have emotional state tracking."""
        assert IndividualType.NONTRACKED.has_emotional_state is False


class TestIndividualTypeHasMemory:
    """Tests for has_memory property."""

    def test_simulated_has_memory(self) -> None:
        """SIMULATED should support memory."""
        assert IndividualType.SIMULATED.has_memory is True

    def test_human_has_memory(self) -> None:
        """HUMAN should support memory (for context)."""
        assert IndividualType.HUMAN.has_memory is True

    def test_nontracked_no_memory(self) -> None:
        """NONTRACKED should not support memory."""
        assert IndividualType.NONTRACKED.has_memory is False


class TestIndividualTypeGeneratesResponses:
    """Tests for generates_responses property."""

    def test_simulated_generates_responses(self) -> None:
        """SIMULATED should generate AI responses."""
        assert IndividualType.SIMULATED.generates_responses is True

    def test_human_no_generate_responses(self) -> None:
        """HUMAN should not generate AI responses."""
        assert IndividualType.HUMAN.generates_responses is False

    def test_nontracked_no_generate_responses(self) -> None:
        """NONTRACKED should not generate AI responses."""
        assert IndividualType.NONTRACKED.generates_responses is False


class TestIndividualTypeRequiresContext:
    """Tests for requires_context property."""

    def test_simulated_no_requires_context(self) -> None:
        """SIMULATED generates its own context."""
        assert IndividualType.SIMULATED.requires_context is False

    def test_human_requires_context(self) -> None:
        """HUMAN requires external context/responses."""
        assert IndividualType.HUMAN.requires_context is True

    def test_nontracked_no_requires_context(self) -> None:
        """NONTRACKED doesn't participate meaningfully."""
        assert IndividualType.NONTRACKED.requires_context is False


class TestParseIndividualType:
    """Tests for parse_individual_type function."""

    def test_parse_string_value(self) -> None:
        """parse_individual_type should convert strings to IndividualType."""
        assert parse_individual_type("simulated") == IndividualType.SIMULATED
        assert parse_individual_type("human") == IndividualType.HUMAN
        assert parse_individual_type("nontracked") == IndividualType.NONTRACKED

    def test_parse_enum_value(self) -> None:
        """parse_individual_type should pass through enum values."""
        assert parse_individual_type(IndividualType.SIMULATED) == IndividualType.SIMULATED
        assert parse_individual_type(IndividualType.HUMAN) == IndividualType.HUMAN

    def test_parse_invalid_value(self) -> None:
        """parse_individual_type should raise ValueError for invalid values."""
        with pytest.raises(ValueError, match="Invalid individual type"):
            parse_individual_type("invalid_type")

    def test_parse_all_string_values(self) -> None:
        """parse_individual_type should work with all valid string values."""
        for individual_type in IndividualType:
            parsed = parse_individual_type(individual_type.value)
            assert parsed == individual_type
