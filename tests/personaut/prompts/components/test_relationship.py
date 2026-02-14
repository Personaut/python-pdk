"""Tests for RelationshipComponent."""

import pytest

from personaut.prompts.components.relationship import (
    RelationshipComponent,
    get_trust_description,
)


class MockIndividual:
    """Mock individual for testing."""

    def __init__(self, id: str, name: str) -> None:
        self.id = id
        self.name = name


class MockRelationship:
    """Mock relationship for testing."""

    def __init__(self, members: list[str], trust: dict[str, float]) -> None:
        self.members = members
        self.trust = trust

    def get_trust(self, individual_id: str) -> float:
        return self.trust.get(individual_id, 0.5)


class TestGetTrustDescription:
    """Tests for get_trust_description function."""

    def test_low_trust(self) -> None:
        """Test low trust description."""
        short, _detailed = get_trust_description(0.1)
        assert "distrustful" in short or "cautious" in short

    def test_neutral_trust(self) -> None:
        """Test neutral trust description."""
        short, _detailed = get_trust_description(0.5)
        assert "neutral" in short

    def test_high_trust(self) -> None:
        """Test high trust description."""
        short, _detailed = get_trust_description(0.9)
        assert "trusting" in short or "deeply" in short

    def test_returns_tuple(self) -> None:
        """Test that function returns both descriptions."""
        result = get_trust_description(0.5)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)


class TestRelationshipComponent:
    """Tests for RelationshipComponent class."""

    @pytest.fixture
    def component(self) -> RelationshipComponent:
        """Create a component for testing."""
        return RelationshipComponent()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        """Create Sarah individual."""
        return MockIndividual("sarah-1", "Sarah")

    @pytest.fixture
    def mike(self) -> MockIndividual:
        """Create Mike individual."""
        return MockIndividual("mike-1", "Mike")

    @pytest.fixture
    def relationship(self) -> MockRelationship:
        """Create a relationship between Sarah and Mike."""
        return MockRelationship(
            members=["sarah-1", "mike-1"],
            trust={"sarah-1": 0.7, "mike-1": 0.6},
        )

    def test_format_empty_others(
        self,
        component: RelationshipComponent,
        sarah: MockIndividual,
    ) -> None:
        """Test formatting with no other individuals."""
        text = component.format(sarah, [], [])
        assert text == ""

    def test_format_with_relationship(
        self,
        component: RelationshipComponent,
        sarah: MockIndividual,
        mike: MockIndividual,
        relationship: MockRelationship,
    ) -> None:
        """Test formatting with an existing relationship."""
        text = component.format(sarah, [mike], [relationship])
        assert "Mike" in text
        assert "Sarah" in text

    def test_format_without_relationship(
        self,
        component: RelationshipComponent,
        sarah: MockIndividual,
        mike: MockIndividual,
    ) -> None:
        """Test formatting without existing relationship."""
        text = component.format(sarah, [mike], [])
        assert "no prior relationship" in text.lower()

    def test_format_multiple_others(
        self,
        component: RelationshipComponent,
        sarah: MockIndividual,
    ) -> None:
        """Test formatting with multiple other individuals."""
        others = [
            MockIndividual("bob-1", "Bob"),
            MockIndividual("alice-1", "Alice"),
        ]
        text = component.format(sarah, others, [])
        assert "Bob" in text
        assert "Alice" in text

    def test_format_brief(
        self,
        component: RelationshipComponent,
        sarah: MockIndividual,
        mike: MockIndividual,
        relationship: MockRelationship,
    ) -> None:
        """Test brief format."""
        text = component.format_brief(sarah, [mike], [relationship])
        assert "others" in text

    def test_format_brief_no_others(
        self,
        component: RelationshipComponent,
        sarah: MockIndividual,
    ) -> None:
        """Test brief format with no others."""
        text = component.format_brief(sarah, [], [])
        assert "no relationships" in text

    def test_dict_individual(self, component: RelationshipComponent) -> None:
        """Test with dict-based individuals."""
        individual = {"id": "1", "name": "Test"}
        other = {"id": "2", "name": "Other"}
        text = component.format(individual, [other], [])
        assert "Other" in text
