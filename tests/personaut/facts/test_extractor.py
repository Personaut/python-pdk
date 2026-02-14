"""Tests for FactExtractor."""

from __future__ import annotations

from personaut.facts.context import SituationalContext
from personaut.facts.extractor import (
    DEFAULT_PATTERNS,
    ExtractionPattern,
    FactExtractor,
)
from personaut.facts.fact import FactCategory


class TestExtractionPattern:
    """Tests for ExtractionPattern dataclass."""

    def test_create_pattern(self) -> None:
        """Should create a pattern."""
        pattern = ExtractionPattern(
            category=FactCategory.LOCATION,
            key="city",
            pattern=r"in\s+(\w+)",
        )
        assert pattern.category == FactCategory.LOCATION
        assert pattern.key == "city"


class TestDefaultPatterns:
    """Tests for DEFAULT_PATTERNS."""

    def test_default_patterns_exist(self) -> None:
        """DEFAULT_PATTERNS should have patterns."""
        assert len(DEFAULT_PATTERNS) > 10

    def test_patterns_cover_categories(self) -> None:
        """Patterns should cover multiple categories."""
        categories = {p.category for p in DEFAULT_PATTERNS}
        assert FactCategory.LOCATION in categories
        assert FactCategory.ENVIRONMENT in categories
        assert FactCategory.TEMPORAL in categories
        assert FactCategory.BEHAVIORAL in categories


class TestFactExtractor:
    """Tests for FactExtractor class."""

    def test_default_creation(self) -> None:
        """Default creation should use default patterns."""
        extractor = FactExtractor()
        assert len(extractor.patterns) == len(DEFAULT_PATTERNS)

    def test_extract_venue_type(self) -> None:
        """Should extract venue type."""
        extractor = FactExtractor()
        ctx = extractor.extract("We met at a coffee shop")
        assert ctx.get_value("venue_type") == "coffee shop"

    def test_extract_crowd_level(self) -> None:
        """Should extract crowd level."""
        extractor = FactExtractor()
        ctx = extractor.extract("It was a busy restaurant")
        assert ctx.get_value("crowd_level") == "busy"

    def test_extract_capacity_percent(self) -> None:
        """Should extract capacity percentage."""
        extractor = FactExtractor()
        ctx = extractor.extract("The venue was at 80% capacity")
        assert ctx.get_value("capacity_percent") == 80

    def test_extract_queue_length(self) -> None:
        """Should extract queue length."""
        extractor = FactExtractor()
        ctx = extractor.extract("There was a line of 5 people")
        assert ctx.get_value("queue_length") == 5

    def test_extract_time_of_day(self) -> None:
        """Should extract time of day."""
        extractor = FactExtractor()
        ctx = extractor.extract("We arrived in the afternoon")
        assert ctx.get_value("time_of_day") == "afternoon"

    def test_extract_noise_level(self) -> None:
        """Should extract noise level."""
        extractor = FactExtractor()
        ctx = extractor.extract("It was a quiet library")
        assert ctx.get_value("noise_level") == "quiet"

    def test_extract_atmosphere(self) -> None:
        """Should extract atmosphere."""
        extractor = FactExtractor()
        ctx = extractor.extract("The atmosphere was relaxed")
        assert ctx.get_value("atmosphere") == "relaxed"

    def test_extract_multiple_facts(self) -> None:
        """Should extract multiple facts from text."""
        extractor = FactExtractor()
        text = "We met at a busy coffee shop around 3pm with a line of 5 people"
        ctx = extractor.extract(text)

        assert ctx.get_value("venue_type") == "coffee shop"
        assert ctx.get_value("crowd_level") == "busy"
        assert ctx.get_value("queue_length") == 5

    def test_extract_with_existing_context(self) -> None:
        """Should add to existing context."""
        extractor = FactExtractor()
        existing = SituationalContext()
        existing.add_location("city", "Miami")

        ctx = extractor.extract("at a busy cafe", existing_context=existing)
        assert ctx.get_value("city") == "Miami"
        assert ctx.get_value("venue_type") == "cafe"

    def test_extract_sets_description(self) -> None:
        """Should set description from text."""
        extractor = FactExtractor()
        ctx = extractor.extract("A short description")
        assert ctx.description == "A short description"

    def test_add_pattern(self) -> None:
        """add_pattern should add a custom pattern."""
        extractor = FactExtractor()
        original_count = len(extractor.patterns)

        pattern = ExtractionPattern(
            category=FactCategory.LOCATION,
            key="parking",
            pattern=r"(free|paid)\s+parking",
        )
        extractor.add_pattern(pattern)

        assert len(extractor.patterns) == original_count + 1

    def test_extract_all_matches(self) -> None:
        """extract_all_matches should return raw tuples."""
        extractor = FactExtractor()
        matches = extractor.extract_all_matches("a busy coffee shop")

        assert len(matches) >= 2
        keys = [m[0] for m in matches]
        assert "venue_type" in keys
        assert "crowd_level" in keys


class TestComplexExtraction:
    """Tests for complex extraction scenarios."""

    def test_coffee_shop_scenario(self) -> None:
        """Should handle the coffee shop example."""
        extractor = FactExtractor()
        text = (
            "We met at a cozy coffee shop in Miami around 3pm. "
            "It was about 80% capacity with a line of 5 people waiting. "
            "The atmosphere was relaxed despite being busy."
        )
        ctx = extractor.extract(text)

        assert ctx.get_value("venue_type") == "coffee shop"
        assert ctx.get_value("capacity_percent") == 80
        assert ctx.get_value("queue_length") == 5
        assert ctx.get_value("atmosphere") in ("relaxed", "cozy")

    def test_office_scenario(self) -> None:
        """Should handle office scenario."""
        extractor = FactExtractor()
        text = (
            "The meeting was in a quiet office on Monday morning. "
            "About 20 people were present in a professional atmosphere."
        )
        ctx = extractor.extract(text)

        assert ctx.get_value("venue_type") == "office"
        assert ctx.get_value("noise_level") == "quiet"
        assert ctx.get_value("day_of_week") == "Monday"
        assert ctx.get_value("time_of_day") == "morning"
        assert ctx.get_value("people_count") == 20

    def test_no_matches(self) -> None:
        """Should handle text with no matches."""
        extractor = FactExtractor()
        ctx = extractor.extract("Random text with no extractable facts")
        assert len(ctx) == 0
