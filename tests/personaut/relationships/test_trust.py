"""Tests for trust utilities."""

from __future__ import annotations

import pytest

from personaut.relationships import (
    TRUST_BEHAVIORS,
    TRUST_DESCRIPTIONS,
    TRUST_THRESHOLDS,
    TrustLevel,
    calculate_trust_change,
    clamp_trust,
    get_default_trust,
    get_stranger_trust,
    get_trust_info,
    get_trust_level,
    trust_allows_disclosure,
)


class TestTrustLevel:
    """Tests for TrustLevel enum."""

    def test_all_levels_defined(self) -> None:
        """Should have all expected trust levels."""
        assert TrustLevel.NONE.value == "none"
        assert TrustLevel.MINIMAL.value == "minimal"
        assert TrustLevel.LOW.value == "low"
        assert TrustLevel.MODERATE.value == "moderate"
        assert TrustLevel.HIGH.value == "high"
        assert TrustLevel.COMPLETE.value == "complete"

    def test_thresholds_cover_range(self) -> None:
        """Trust thresholds should cover 0.0 to 1.0."""
        # Check coverage
        for level in TrustLevel:
            assert level in TRUST_THRESHOLDS

    def test_descriptions_for_all_levels(self) -> None:
        """All levels should have descriptions."""
        for level in TrustLevel:
            assert level in TRUST_DESCRIPTIONS
            assert len(TRUST_DESCRIPTIONS[level]) > 0

    def test_behaviors_for_all_levels(self) -> None:
        """All levels should have behavior definitions."""
        for level in TrustLevel:
            assert level in TRUST_BEHAVIORS
            behaviors = TRUST_BEHAVIORS[level]
            assert "shares_private_memories" in behaviors
            assert "emotional_openness" in behaviors
            assert "responds_to_requests" in behaviors


class TestGetTrustLevel:
    """Tests for get_trust_level function."""

    def test_zero_is_none(self) -> None:
        """Zero trust should be NONE."""
        assert get_trust_level(0.0) == TrustLevel.NONE

    def test_minimal_range(self) -> None:
        """Values in minimal range should return MINIMAL."""
        assert get_trust_level(0.15) == TrustLevel.MINIMAL
        assert get_trust_level(0.2) == TrustLevel.MINIMAL

    def test_low_range(self) -> None:
        """Values in low range should return LOW."""
        assert get_trust_level(0.3) == TrustLevel.LOW
        assert get_trust_level(0.35) == TrustLevel.LOW

    def test_moderate_range(self) -> None:
        """Values in moderate range should return MODERATE."""
        assert get_trust_level(0.5) == TrustLevel.MODERATE
        assert get_trust_level(0.55) == TrustLevel.MODERATE

    def test_high_range(self) -> None:
        """Values in high range should return HIGH."""
        assert get_trust_level(0.7) == TrustLevel.HIGH
        assert get_trust_level(0.75) == TrustLevel.HIGH

    def test_complete_range(self) -> None:
        """Values in complete range should return COMPLETE."""
        assert get_trust_level(0.85) == TrustLevel.COMPLETE
        assert get_trust_level(0.95) == TrustLevel.COMPLETE

    def test_one_is_complete(self) -> None:
        """1.0 should be COMPLETE."""
        assert get_trust_level(1.0) == TrustLevel.COMPLETE

    def test_above_one_is_complete(self) -> None:
        """Values above 1.0 should be COMPLETE."""
        assert get_trust_level(1.5) == TrustLevel.COMPLETE


class TestGetTrustInfo:
    """Tests for get_trust_info function."""

    def test_returns_trust_info(self) -> None:
        """Should return TrustInfo object."""
        info = get_trust_info(0.75)

        assert info.level == TrustLevel.HIGH
        assert info.value == 0.75
        assert len(info.description) > 0
        assert "behaviors" in dir(info)

    def test_high_trust_shares_private(self) -> None:
        """High trust should allow private memory sharing."""
        info = get_trust_info(0.75)

        assert info.behaviors["shares_private_memories"] is True

    def test_low_trust_withholds(self) -> None:
        """Low trust should not share private memories."""
        info = get_trust_info(0.3)

        assert info.behaviors["shares_private_memories"] is False

    def test_complete_trust_full_openness(self) -> None:
        """Complete trust should have full emotional openness."""
        info = get_trust_info(0.9)

        assert info.behaviors["emotional_openness"] == 1.0


class TestClampTrust:
    """Tests for clamp_trust function."""

    def test_clamp_above_one(self) -> None:
        """Should clamp values above 1.0."""
        assert clamp_trust(1.5) == 1.0
        assert clamp_trust(100) == 1.0

    def test_clamp_below_zero(self) -> None:
        """Should clamp values below 0.0."""
        assert clamp_trust(-0.5) == 0.0
        assert clamp_trust(-100) == 0.0

    def test_valid_range_unchanged(self) -> None:
        """Should not change values in valid range."""
        assert clamp_trust(0.5) == 0.5
        assert clamp_trust(0.0) == 0.0
        assert clamp_trust(1.0) == 1.0


class TestCalculateTrustChange:
    """Tests for calculate_trust_change function."""

    def test_simple_increase(self) -> None:
        """Should increase trust."""
        new_val, desc = calculate_trust_change(0.5, 0.2)

        assert new_val == pytest.approx(0.7, abs=0.01)
        assert "0.5" in desc or "0.50" in desc
        assert "0.7" in desc

    def test_simple_decrease(self) -> None:
        """Should decrease trust."""
        new_val, _desc = calculate_trust_change(0.5, -0.2)

        assert new_val == pytest.approx(0.3, abs=0.01)

    def test_clamps_at_max(self) -> None:
        """Should clamp at 1.0."""
        new_val, _ = calculate_trust_change(0.9, 0.5)

        assert new_val == 1.0

    def test_clamps_at_min(self) -> None:
        """Should clamp at 0.0."""
        new_val, _ = calculate_trust_change(0.1, -0.5)

        assert new_val == 0.0

    def test_diminishing_returns_high_trust(self) -> None:
        """Should have diminishing returns when trust is high."""
        change = 0.2

        # Normal gain at low trust
        low_new, _ = calculate_trust_change(0.3, change)
        low_gain = low_new - 0.3

        # Diminished gain at high trust
        high_new, _ = calculate_trust_change(0.85, change)
        high_gain = high_new - 0.85

        assert high_gain < low_gain

    def test_reason_included(self) -> None:
        """Should include reason in description."""
        _, desc = calculate_trust_change(0.5, 0.1, "helped in a crisis")

        assert "helped in a crisis" in desc
        assert "increased" in desc

    def test_decrease_reason(self) -> None:
        """Should describe decreases correctly."""
        _, desc = calculate_trust_change(0.5, -0.1, "broke a promise")

        assert "broke a promise" in desc
        assert "decreased" in desc


class TestTrustAllowsDisclosure:
    """Tests for trust_allows_disclosure function."""

    def test_above_threshold(self) -> None:
        """Should allow when trust exceeds threshold."""
        assert trust_allows_disclosure(0.8, 0.7) is True

    def test_equal_threshold(self) -> None:
        """Should allow when trust equals threshold."""
        assert trust_allows_disclosure(0.7, 0.7) is True

    def test_below_threshold(self) -> None:
        """Should deny when trust is below threshold."""
        assert trust_allows_disclosure(0.5, 0.7) is False


class TestDefaults:
    """Tests for default trust functions."""

    def test_default_trust(self) -> None:
        """Should return default trust value."""
        default = get_default_trust()

        assert 0.0 <= default <= 1.0
        assert get_trust_level(default) == TrustLevel.LOW

    def test_stranger_trust(self) -> None:
        """Should return stranger trust value."""
        stranger = get_stranger_trust()

        assert stranger < get_default_trust()
        assert get_trust_level(stranger) == TrustLevel.MINIMAL
