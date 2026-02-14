"""Tests for SituationalContext."""

from __future__ import annotations

from personaut.facts.context import (
    SituationalContext,
    create_coffee_shop_context,
    create_office_context,
)
from personaut.facts.fact import Fact, FactCategory


class TestSituationalContextCreation:
    """Tests for SituationalContext initialization."""

    def test_default_creation(self) -> None:
        """Default creation should have empty facts."""
        ctx = SituationalContext()
        assert len(ctx) == 0
        assert ctx.description is None

    def test_creation_with_description(self) -> None:
        """Should accept description."""
        ctx = SituationalContext(description="Test situation")
        assert ctx.description == "Test situation"


class TestAddFacts:
    """Tests for add_* methods."""

    def test_add_fact(self) -> None:
        """add_fact should add a fact."""
        ctx = SituationalContext()
        fact = Fact(FactCategory.LOCATION, "city", "Miami")
        ctx.add_fact(fact)
        assert len(ctx) == 1

    def test_add_location(self) -> None:
        """add_location should add LOCATION fact."""
        ctx = SituationalContext()
        fact = ctx.add_location("city", "Miami")
        assert fact.category == FactCategory.LOCATION
        assert ctx.get_value("city") == "Miami"

    def test_add_environment(self) -> None:
        """add_environment should add ENVIRONMENT fact."""
        ctx = SituationalContext()
        fact = ctx.add_environment("capacity", 80, unit="percent")
        assert fact.category == FactCategory.ENVIRONMENT
        assert fact.unit == "percent"

    def test_add_behavioral(self) -> None:
        """add_behavioral should add BEHAVIORAL fact."""
        ctx = SituationalContext()
        fact = ctx.add_behavioral("queue_length", 5, unit="people")
        assert fact.category == FactCategory.BEHAVIORAL

    def test_add_temporal(self) -> None:
        """add_temporal should add TEMPORAL fact."""
        ctx = SituationalContext()
        fact = ctx.add_temporal("time_of_day", "afternoon")
        assert fact.category == FactCategory.TEMPORAL

    def test_add_social(self) -> None:
        """add_social should add SOCIAL fact."""
        ctx = SituationalContext()
        fact = ctx.add_social("people_count", 25, unit="people")
        assert fact.category == FactCategory.SOCIAL

    def test_add_sensory(self) -> None:
        """add_sensory should add SENSORY fact."""
        ctx = SituationalContext()
        fact = ctx.add_sensory("smell", "coffee")
        assert fact.category == FactCategory.SENSORY


class TestGetFacts:
    """Tests for fact retrieval methods."""

    def test_get_facts_by_category(self) -> None:
        """Should filter by category."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        ctx.add_location("venue", "cafe")
        ctx.add_environment("noise", "loud")

        location_facts = ctx.get_facts_by_category(FactCategory.LOCATION)
        assert len(location_facts) == 2

    def test_get_fact(self) -> None:
        """Should get fact by key."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        fact = ctx.get_fact("city")
        assert fact is not None
        assert fact.value == "Miami"

    def test_get_fact_not_found(self) -> None:
        """Should return None for unknown key."""
        ctx = SituationalContext()
        assert ctx.get_fact("unknown") is None

    def test_get_value(self) -> None:
        """Should get value by key."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        assert ctx.get_value("city") == "Miami"

    def test_get_value_with_default(self) -> None:
        """Should return default for unknown key."""
        ctx = SituationalContext()
        assert ctx.get_value("unknown", "N/A") == "N/A"


class TestEmbeddingGeneration:
    """Tests for embedding text generation."""

    def test_to_embedding_text(self) -> None:
        """Should generate multi-line text."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        ctx.add_environment("noise", "loud")

        text = ctx.to_embedding_text()
        assert "city: Miami" in text
        assert "noise: loud" in text

    def test_to_embedding_text_sorted_by_weight(self) -> None:
        """Facts should be sorted by category weight."""
        ctx = SituationalContext()
        ctx.add_environment("noise", "loud")  # weight 0.8
        ctx.add_location("city", "Miami")  # weight 1.0

        text = ctx.to_embedding_text()
        lines = text.strip().split("\n")
        # LOCATION should come first (higher weight)
        assert "city" in lines[0]

    def test_to_embedding_text_with_filter(self) -> None:
        """Should filter by categories."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        ctx.add_environment("noise", "loud")

        text = ctx.to_embedding_text(include_categories=[FactCategory.LOCATION])
        assert "city: Miami" in text
        assert "noise" not in text

    def test_to_weighted_embedding_pairs(self) -> None:
        """Should generate weighted pairs."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")

        pairs = ctx.to_weighted_embedding_pairs()
        assert len(pairs) == 1
        assert pairs[0][0] == "city: Miami"
        assert pairs[0][1] == 1.0  # LOCATION weight


class TestSerialization:
    """Tests for to_dict and from_dict."""

    def test_to_dict(self) -> None:
        """Should convert to dictionary."""
        ctx = SituationalContext(description="Test")
        ctx.add_location("city", "Miami")

        data = ctx.to_dict()
        assert len(data["facts"]) == 1
        assert data["description"] == "Test"
        assert "timestamp" in data

    def test_from_dict(self) -> None:
        """Should create from dictionary."""
        data = {
            "facts": [{"category": "location", "key": "city", "value": "Miami"}],
            "description": "Test",
        }
        ctx = SituationalContext.from_dict(data)
        assert len(ctx) == 1
        assert ctx.get_value("city") == "Miami"

    def test_roundtrip(self) -> None:
        """to_dict and from_dict should roundtrip."""
        original = SituationalContext(description="Test")
        original.add_location("city", "Miami")
        original.add_environment("noise", "loud")

        data = original.to_dict()
        restored = SituationalContext.from_dict(data)

        assert len(restored) == len(original)
        assert restored.get_value("city") == "Miami"


class TestContextOperations:
    """Tests for context operations."""

    def test_copy(self) -> None:
        """copy should create independent context."""
        ctx1 = SituationalContext()
        ctx1.add_location("city", "Miami")
        ctx2 = ctx1.copy()
        ctx2.add_location("venue", "cafe")

        assert len(ctx1) == 1
        assert len(ctx2) == 2

    def test_merge(self) -> None:
        """merge should combine contexts."""
        ctx1 = SituationalContext()
        ctx1.add_location("city", "Miami")
        ctx2 = SituationalContext()
        ctx2.add_environment("noise", "loud")

        merged = ctx1.merge(ctx2)
        assert len(merged) == 2
        assert merged.get_value("city") == "Miami"
        assert merged.get_value("noise") == "loud"


class TestDunderMethods:
    """Tests for dunder methods."""

    def test_len(self) -> None:
        """len() should return fact count."""
        ctx = SituationalContext()
        assert len(ctx) == 0
        ctx.add_location("city", "Miami")
        assert len(ctx) == 1

    def test_iter(self) -> None:
        """Should be iterable."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        facts = list(ctx)
        assert len(facts) == 1

    def test_contains(self) -> None:
        """in operator should check key existence."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        assert "city" in ctx
        assert "unknown" not in ctx

    def test_repr(self) -> None:
        """repr should show category counts."""
        ctx = SituationalContext()
        ctx.add_location("city", "Miami")
        ctx.add_location("venue", "cafe")
        repr_str = repr(ctx)
        assert "SituationalContext" in repr_str
        assert "location=2" in repr_str


class TestContextTemplates:
    """Tests for context template functions."""

    def test_create_coffee_shop_context(self) -> None:
        """create_coffee_shop_context should create valid context."""
        ctx = create_coffee_shop_context(
            city="Miami, FL",
            venue_name="Sunrise Cafe",
            capacity_percent=80,
            queue_length=5,
        )
        assert ctx.get_value("city") == "Miami, FL"
        assert ctx.get_value("venue_type") == "coffee shop"
        assert ctx.get_value("venue_name") == "Sunrise Cafe"
        assert ctx.get_value("capacity_percent") == 80
        assert ctx.get_value("queue_length") == 5

    def test_create_office_context(self) -> None:
        """create_office_context should create valid context."""
        ctx = create_office_context(
            city="New York, NY",
            company_name="Acme Corp",
            people_count=50,
        )
        assert ctx.get_value("city") == "New York, NY"
        assert ctx.get_value("venue_type") == "office"
        assert ctx.get_value("venue_name") == "Acme Corp"
