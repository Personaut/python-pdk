"""Tests for Fact and FactCategory."""

from __future__ import annotations

import pytest

from personaut.facts.fact import (
    BEHAVIORAL_FACTS,
    ENVIRONMENT_FACTS,
    LOCATION_FACTS,
    Fact,
    FactCategory,
    create_behavioral_fact,
    create_environment_fact,
    create_location_fact,
)


class TestFactCategoryEnum:
    """Tests for FactCategory enum."""

    def test_all_categories_defined(self) -> None:
        """All 8 categories should be defined."""
        assert len(FactCategory) == 8

    def test_category_values(self) -> None:
        """Category values should be lowercase strings."""
        assert FactCategory.LOCATION.value == "location"
        assert FactCategory.ENVIRONMENT.value == "environment"
        assert FactCategory.TEMPORAL.value == "temporal"
        assert FactCategory.SOCIAL.value == "social"

    def test_all_categories_have_descriptions(self) -> None:
        """All categories should have descriptions."""
        for category in FactCategory:
            assert category.description
            assert len(category.description) > 10

    def test_embedding_weights_in_range(self) -> None:
        """Embedding weights should be between 0.5 and 1.0."""
        for category in FactCategory:
            assert 0.5 <= category.embedding_weight <= 1.0

    def test_location_highest_weight(self) -> None:
        """LOCATION should have highest weight."""
        assert FactCategory.LOCATION.embedding_weight == 1.0


class TestFact:
    """Tests for Fact dataclass."""

    def test_create_basic_fact(self) -> None:
        """Should create a basic fact."""
        fact = Fact(
            category=FactCategory.LOCATION,
            key="city",
            value="Miami, FL",
        )
        assert fact.category == FactCategory.LOCATION
        assert fact.key == "city"
        assert fact.value == "Miami, FL"
        assert fact.confidence == 1.0

    def test_create_fact_with_unit(self) -> None:
        """Should create a fact with unit."""
        fact = Fact(
            category=FactCategory.ENVIRONMENT,
            key="capacity",
            value=80,
            unit="percent",
        )
        assert fact.unit == "percent"

    def test_create_fact_with_metadata(self) -> None:
        """Should create a fact with metadata."""
        fact = Fact(
            category=FactCategory.LOCATION,
            key="city",
            value="Miami",
            metadata={"source": "user_input"},
        )
        assert fact.metadata["source"] == "user_input"

    def test_invalid_confidence_raises(self) -> None:
        """Invalid confidence should raise ValueError."""
        with pytest.raises(ValueError, match="confidence must be between"):
            Fact(FactCategory.LOCATION, "city", "Miami", confidence=1.5)

    def test_fact_is_frozen(self) -> None:
        """Fact should be immutable."""
        from dataclasses import FrozenInstanceError

        fact = Fact(FactCategory.LOCATION, "city", "Miami")
        with pytest.raises(FrozenInstanceError):
            fact.value = "Boston"  # type: ignore[misc]


class TestFactEmbeddingText:
    """Tests for to_embedding_text method."""

    def test_basic_embedding_text(self) -> None:
        """Should generate basic embedding text."""
        fact = Fact(FactCategory.LOCATION, "city", "Miami")
        assert fact.to_embedding_text() == "city: Miami"

    def test_embedding_text_with_unit(self) -> None:
        """Should include unit in embedding text."""
        fact = Fact(FactCategory.ENVIRONMENT, "capacity", 80, unit="percent")
        assert fact.to_embedding_text() == "capacity: 80 percent"

    def test_str_returns_embedding_text(self) -> None:
        """str() should return embedding text."""
        fact = Fact(FactCategory.LOCATION, "city", "Miami")
        assert str(fact) == "city: Miami"


class TestFactSerialization:
    """Tests for to_dict and from_dict methods."""

    def test_to_dict(self) -> None:
        """Should convert to dictionary."""
        fact = Fact(
            category=FactCategory.LOCATION,
            key="city",
            value="Miami",
            confidence=0.9,
        )
        data = fact.to_dict()
        assert data["category"] == "location"
        assert data["key"] == "city"
        assert data["value"] == "Miami"
        assert data["confidence"] == 0.9

    def test_from_dict(self) -> None:
        """Should create from dictionary."""
        data = {
            "category": "location",
            "key": "city",
            "value": "Miami",
            "confidence": 0.9,
        }
        fact = Fact.from_dict(data)
        assert fact.category == FactCategory.LOCATION
        assert fact.key == "city"
        assert fact.value == "Miami"

    def test_roundtrip(self) -> None:
        """to_dict and from_dict should roundtrip."""
        original = Fact(
            category=FactCategory.ENVIRONMENT,
            key="capacity",
            value=80,
            unit="percent",
            confidence=0.95,
        )
        data = original.to_dict()
        restored = Fact.from_dict(data)
        assert restored.category == original.category
        assert restored.key == original.key
        assert restored.value == original.value
        assert restored.unit == original.unit


class TestFactFactories:
    """Tests for factory functions."""

    def test_create_location_fact(self) -> None:
        """create_location_fact should create LOCATION facts."""
        fact = create_location_fact("city", "Miami")
        assert fact.category == FactCategory.LOCATION
        assert fact.key == "city"
        assert fact.value == "Miami"

    def test_create_environment_fact(self) -> None:
        """create_environment_fact should create ENVIRONMENT facts."""
        fact = create_environment_fact("capacity", 80, unit="percent")
        assert fact.category == FactCategory.ENVIRONMENT
        assert fact.unit == "percent"

    def test_create_behavioral_fact(self) -> None:
        """create_behavioral_fact should create BEHAVIORAL facts."""
        fact = create_behavioral_fact("queue_length", 5, unit="people")
        assert fact.category == FactCategory.BEHAVIORAL
        assert fact.unit == "people"


class TestFactTemplates:
    """Tests for fact templates."""

    def test_location_facts_template(self) -> None:
        """LOCATION_FACTS should have expected keys."""
        assert "city" in LOCATION_FACTS
        assert "venue_type" in LOCATION_FACTS

    def test_environment_facts_template(self) -> None:
        """ENVIRONMENT_FACTS should have expected keys."""
        assert "capacity_percent" in ENVIRONMENT_FACTS
        assert "noise_level" in ENVIRONMENT_FACTS

    def test_behavioral_facts_template(self) -> None:
        """BEHAVIORAL_FACTS should have expected keys."""
        assert "queue_length" in BEHAVIORAL_FACTS
        assert "wait_time" in BEHAVIORAL_FACTS
