"""Tests for Relationship class."""

from __future__ import annotations

from datetime import datetime

import pytest

from personaut.relationships import (
    Relationship,
    TrustChange,
    TrustLevel,
    create_relationship,
    get_default_trust,
)


class TestRelationship:
    """Tests for Relationship class."""

    def test_create_relationship(self) -> None:
        """Should create a relationship with basic attributes."""
        rel = Relationship(
            individual_ids=["alice", "bob"],
            history="Friends since childhood",
        )

        assert "alice" in rel.individual_ids
        assert "bob" in rel.individual_ids
        assert rel.history == "Friends since childhood"
        assert rel.id is not None

    def test_default_trust_initialized(self) -> None:
        """Should initialize default trust for all pairs."""
        rel = Relationship(individual_ids=["alice", "bob"])

        # Both should have default trust toward each other
        alice_bob = rel.get_trust("alice", "bob")
        bob_alice = rel.get_trust("bob", "alice")

        assert alice_bob == get_default_trust()
        assert bob_alice == get_default_trust()

    def test_get_trust(self) -> None:
        """Should get trust from one individual to another."""
        rel = Relationship(
            individual_ids=["alice", "bob"],
            trust={
                "alice": {"bob": 0.8},
                "bob": {"alice": 0.5},
            },
        )

        assert rel.get_trust("alice", "bob") == 0.8
        assert rel.get_trust("bob", "alice") == 0.5

    def test_get_trust_not_found(self) -> None:
        """Should return 0.0 for unknown individuals."""
        rel = Relationship(individual_ids=["alice", "bob"])

        assert rel.get_trust("charlie", "bob") == 0.0
        assert rel.get_trust("alice", "charlie") == 0.0

    def test_get_mutual_trust(self) -> None:
        """Should calculate average mutual trust."""
        rel = Relationship(
            individual_ids=["alice", "bob"],
            trust={
                "alice": {"bob": 0.8},
                "bob": {"alice": 0.6},
            },
        )

        mutual = rel.get_mutual_trust("alice", "bob")

        assert mutual == pytest.approx(0.7, abs=0.01)

    def test_get_trust_asymmetry(self) -> None:
        """Should calculate trust asymmetry."""
        rel = Relationship(
            individual_ids=["alice", "bob"],
            trust={
                "alice": {"bob": 0.9},
                "bob": {"alice": 0.5},
            },
        )

        # Alice trusts Bob more
        asymmetry = rel.get_trust_asymmetry("alice", "bob")
        assert asymmetry == pytest.approx(0.4, abs=0.01)

        # Reverse direction
        asymmetry_rev = rel.get_trust_asymmetry("bob", "alice")
        assert asymmetry_rev == pytest.approx(-0.4, abs=0.01)

    def test_update_trust(self) -> None:
        """Should update trust and return new value."""
        rel = Relationship(
            individual_ids=["alice", "bob"],
            trust={"alice": {"bob": 0.5}, "bob": {"alice": 0.5}},
        )

        new_val = rel.update_trust("alice", "bob", 0.2, "helped move")

        assert new_val == pytest.approx(0.7, abs=0.01)
        assert rel.get_trust("alice", "bob") == new_val

    def test_update_trust_records_history(self) -> None:
        """Should record trust changes in history."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.update_trust("alice", "bob", 0.1, "coffee meeting")

        assert len(rel.trust_history) == 1
        change = rel.trust_history[0]
        assert change.from_individual == "alice"
        assert change.to_individual == "bob"
        assert change.reason == "coffee meeting"

    def test_set_trust(self) -> None:
        """Should set trust to specific value."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.set_trust("alice", "bob", 0.9)

        assert rel.get_trust("alice", "bob") == 0.9

    def test_set_trust_clamps(self) -> None:
        """Should clamp trust when setting."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.set_trust("alice", "bob", 1.5)
        assert rel.get_trust("alice", "bob") == 1.0

        rel.set_trust("alice", "bob", -0.5)
        assert rel.get_trust("alice", "bob") == 0.0

    def test_get_trust_level(self) -> None:
        """Should return TrustLevel enum."""
        rel = Relationship(
            individual_ids=["alice", "bob"],
            trust={"alice": {"bob": 0.85}, "bob": {"alice": 0.85}},
        )

        level = rel.get_trust_level("alice", "bob")

        assert level == TrustLevel.COMPLETE

    def test_add_individual(self) -> None:
        """Should add individual to relationship."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.add_individual("carol")

        assert "carol" in rel.individual_ids
        assert rel.get_trust("carol", "alice") == get_default_trust()
        assert rel.get_trust("alice", "carol") == get_default_trust()

    def test_add_individual_custom_trust(self) -> None:
        """Should add individual with custom default trust."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.add_individual("carol", default_trust=0.7)

        assert rel.get_trust("carol", "alice") == 0.7
        assert rel.get_trust("alice", "carol") == 0.7

    def test_add_individual_already_exists(self) -> None:
        """Should not add duplicate individual."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.add_individual("alice")

        assert rel.individual_ids.count("alice") == 1

    def test_remove_individual(self) -> None:
        """Should remove individual from relationship."""
        rel = Relationship(individual_ids=["alice", "bob", "carol"])

        rel.remove_individual("carol")

        assert "carol" not in rel.individual_ids
        assert "carol" not in rel.trust
        assert "carol" not in rel.trust.get("alice", {})

    def test_remove_individual_not_found(self) -> None:
        """Should handle removing non-existent individual."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.remove_individual("charlie")  # Should not raise

        assert len(rel.individual_ids) == 2

    def test_add_shared_memory(self) -> None:
        """Should add shared memory ID."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.add_shared_memory("mem_123")

        assert "mem_123" in rel.shared_memory_ids

    def test_add_shared_memory_no_duplicates(self) -> None:
        """Should not add duplicate memory IDs."""
        rel = Relationship(individual_ids=["alice", "bob"])

        rel.add_shared_memory("mem_123")
        rel.add_shared_memory("mem_123")

        assert rel.shared_memory_ids.count("mem_123") == 1

    def test_has_individual(self) -> None:
        """Should check if individual is in relationship."""
        rel = Relationship(individual_ids=["alice", "bob"])

        assert rel.has_individual("alice") is True
        assert rel.has_individual("charlie") is False

    def test_involves(self) -> None:
        """Should check if relationship involves all specified individuals."""
        rel = Relationship(individual_ids=["alice", "bob", "carol"])

        assert rel.involves("alice", "bob") is True
        assert rel.involves("alice", "carol") is True
        assert rel.involves("alice", "bob", "carol") is True
        assert rel.involves("alice", "david") is False

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        rel = Relationship(
            individual_ids=["alice", "bob"],
            trust={"alice": {"bob": 0.8}, "bob": {"alice": 0.6}},
            history="Old friends",
            relationship_type="friends",
        )

        data = rel.to_dict()

        assert data["individual_ids"] == ["alice", "bob"]
        assert data["trust"]["alice"]["bob"] == 0.8
        assert data["history"] == "Old friends"
        assert "created_at" in data

    def test_from_dict(self) -> None:
        """Should deserialize from dictionary."""
        data = {
            "id": "rel_123",
            "individual_ids": ["alice", "bob"],
            "trust": {"alice": {"bob": 0.8}, "bob": {"alice": 0.6}},
            "shared_memory_ids": ["mem_1"],
            "history": "College friends",
            "relationship_type": "friends",
            "created_at": "2024-01-15T10:30:00",
            "trust_history": [],
        }

        rel = Relationship.from_dict(data)

        assert rel.id == "rel_123"
        assert rel.get_trust("alice", "bob") == 0.8
        assert rel.history == "College friends"


class TestCreateRelationship:
    """Tests for create_relationship factory."""

    def test_create_with_symmetric_trust(self) -> None:
        """Should create relationship with symmetric trust format."""
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            trust={"alice": 0.8, "bob": 0.6},
        )

        # Alice's trust toward everyone is 0.8
        assert rel.get_trust("alice", "bob") == 0.8
        # Bob's trust toward everyone is 0.6
        assert rel.get_trust("bob", "alice") == 0.6

    def test_create_with_asymmetric_trust(self) -> None:
        """Should create relationship with asymmetric trust format."""
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            trust={
                "alice": {"bob": 0.9},
                "bob": {"alice": 0.4},
            },
        )

        assert rel.get_trust("alice", "bob") == 0.9
        assert rel.get_trust("bob", "alice") == 0.4

    def test_create_with_history(self) -> None:
        """Should create relationship with history."""
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            history="Met at university",
        )

        assert rel.history == "Met at university"

    def test_create_with_type(self) -> None:
        """Should create relationship with type."""
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            relationship_type="coworkers",
        )

        assert rel.relationship_type == "coworkers"

    def test_create_without_trust(self) -> None:
        """Should use default trust when not specified."""
        rel = create_relationship(
            individual_ids=["alice", "bob"],
        )

        assert rel.get_trust("alice", "bob") == get_default_trust()

    def test_create_three_person_relationship(self) -> None:
        """Should handle relationships with more than 2 individuals."""
        rel = create_relationship(
            individual_ids=["alice", "bob", "carol"],
            trust={"alice": 0.8, "bob": 0.6, "carol": 0.7},
        )

        assert rel.get_trust("alice", "bob") == 0.8
        assert rel.get_trust("alice", "carol") == 0.8
        assert rel.get_trust("bob", "alice") == 0.6
        assert rel.get_trust("carol", "bob") == 0.7


class TestTrustChange:
    """Tests for TrustChange dataclass."""

    def test_create_trust_change(self) -> None:
        """Should create trust change record."""
        tc = TrustChange(
            timestamp=datetime.now(),
            from_individual="alice",
            to_individual="bob",
            old_value=0.5,
            new_value=0.7,
            reason="helped during crisis",
        )

        assert tc.from_individual == "alice"
        assert tc.to_individual == "bob"
        assert tc.old_value == 0.5
        assert tc.new_value == 0.7
        assert tc.reason == "helped during crisis"
