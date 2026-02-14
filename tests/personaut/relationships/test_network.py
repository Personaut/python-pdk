"""Tests for RelationshipNetwork class."""

from __future__ import annotations

import pytest

from personaut.relationships import (
    RelationshipNetwork,
    create_relationship,
    get_stranger_trust,
)


class TestRelationshipNetwork:
    """Tests for RelationshipNetwork class."""

    def test_create_empty_network(self) -> None:
        """Should create an empty network."""
        network = RelationshipNetwork()

        assert len(network) == 0

    def test_add_relationship(self) -> None:
        """Should add relationship to network."""
        network = RelationshipNetwork()
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            trust={"alice": 0.8, "bob": 0.7},
        )

        network.add_relationship(rel)

        assert len(network) == 1

    def test_remove_relationship(self) -> None:
        """Should remove relationship from network."""
        network = RelationshipNetwork()
        rel = create_relationship(individual_ids=["alice", "bob"])
        network.add_relationship(rel)

        result = network.remove_relationship(rel.id)

        assert result is True
        assert len(network) == 0

    def test_remove_nonexistent_relationship(self) -> None:
        """Should return False for non-existent relationship."""
        network = RelationshipNetwork()

        result = network.remove_relationship("fake_id")

        assert result is False

    def test_get_relationship(self) -> None:
        """Should get relationship by ID."""
        network = RelationshipNetwork()
        rel = create_relationship(individual_ids=["alice", "bob"])
        network.add_relationship(rel)

        found = network.get_relationship(rel.id)

        assert found is rel

    def test_get_relationship_not_found(self) -> None:
        """Should return None for non-existent ID."""
        network = RelationshipNetwork()

        found = network.get_relationship("fake_id")

        assert found is None

    def test_get_relationships_for_individual(self) -> None:
        """Should get all relationships for an individual."""
        network = RelationshipNetwork()
        rel1 = create_relationship(individual_ids=["alice", "bob"])
        rel2 = create_relationship(individual_ids=["alice", "carol"])
        rel3 = create_relationship(individual_ids=["bob", "carol"])
        network.add_relationship(rel1)
        network.add_relationship(rel2)
        network.add_relationship(rel3)

        alice_rels = network.get_relationships("alice")

        assert len(alice_rels) == 2
        assert rel1 in alice_rels
        assert rel2 in alice_rels
        assert rel3 not in alice_rels

    def test_get_relationship_between(self) -> None:
        """Should get relationship between two individuals."""
        network = RelationshipNetwork()
        rel = create_relationship(individual_ids=["alice", "bob"])
        network.add_relationship(rel)

        found = network.get_relationship_between("alice", "bob")

        assert found is rel

    def test_get_relationship_between_order_independent(self) -> None:
        """Should find relationship regardless of argument order."""
        network = RelationshipNetwork()
        rel = create_relationship(individual_ids=["alice", "bob"])
        network.add_relationship(rel)

        found1 = network.get_relationship_between("alice", "bob")
        found2 = network.get_relationship_between("bob", "alice")

        assert found1 is rel
        assert found2 is rel

    def test_get_relationship_between_not_found(self) -> None:
        """Should return None if no relationship exists."""
        network = RelationshipNetwork()
        rel = create_relationship(individual_ids=["alice", "bob"])
        network.add_relationship(rel)

        found = network.get_relationship_between("alice", "carol")

        assert found is None

    def test_get_connected_individuals(self) -> None:
        """Should get all individuals connected to someone."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["alice", "bob"]))
        network.add_relationship(create_relationship(individual_ids=["alice", "carol"]))
        network.add_relationship(create_relationship(individual_ids=["bob", "david"]))

        connected = network.get_connected_individuals("alice")

        assert connected == {"bob", "carol"}

    def test_get_trust_in_network_direct(self) -> None:
        """Should get trust for direct relationship."""
        network = RelationshipNetwork()
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            trust={"alice": 0.9, "bob": 0.7},
        )
        network.add_relationship(rel)

        trust = network.get_trust_in_network("alice", "bob")

        assert trust == 0.9

    def test_get_trust_in_network_no_relationship(self) -> None:
        """Should return stranger trust when no relationship."""
        network = RelationshipNetwork()

        trust = network.get_trust_in_network("alice", "bob")

        assert trust == get_stranger_trust()


class TestPathFinding:
    """Tests for path finding in networks."""

    def test_find_path_direct(self) -> None:
        """Should find direct path between connected individuals."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["alice", "bob"]))

        path = network.find_path("alice", "bob")

        assert path == ["alice", "bob"]

    def test_find_path_indirect(self) -> None:
        """Should find path through intermediaries."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["alice", "bob"]))
        network.add_relationship(create_relationship(individual_ids=["bob", "carol"]))

        path = network.find_path("alice", "carol")

        assert path == ["alice", "bob", "carol"]

    def test_find_path_self(self) -> None:
        """Should return single-element path to self."""
        network = RelationshipNetwork()

        path = network.find_path("alice", "alice")

        assert path == ["alice"]

    def test_find_path_no_connection(self) -> None:
        """Should return None if no path exists."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["alice", "bob"]))
        network.add_relationship(create_relationship(individual_ids=["carol", "david"]))

        path = network.find_path("alice", "carol")

        assert path is None

    def test_find_path_respects_max_depth(self) -> None:
        """Should respect max depth limit."""
        network = RelationshipNetwork()
        # Create a long chain: a-b-c-d-e-f-g
        network.add_relationship(create_relationship(individual_ids=["a", "b"]))
        network.add_relationship(create_relationship(individual_ids=["b", "c"]))
        network.add_relationship(create_relationship(individual_ids=["c", "d"]))
        network.add_relationship(create_relationship(individual_ids=["d", "e"]))
        network.add_relationship(create_relationship(individual_ids=["e", "f"]))
        network.add_relationship(create_relationship(individual_ids=["f", "g"]))

        # Path of length 4 should work with default max_depth=6
        path = network.find_path("a", "e")
        assert path is not None

        # Path of length 7 should not work with max_depth=3
        path = network.find_path("a", "g", max_depth=3)
        assert path is None

    def test_calculate_path_trust(self) -> None:
        """Should calculate trust along path."""
        network = RelationshipNetwork()
        network.add_relationship(
            create_relationship(
                individual_ids=["alice", "bob"],
                trust={"alice": 0.8, "bob": 0.8},
            )
        )
        network.add_relationship(
            create_relationship(
                individual_ids=["bob", "carol"],
                trust={"bob": 0.5, "carol": 0.5},
            )
        )

        trust = network.calculate_path_trust(["alice", "bob", "carol"])

        # 0.8 * 0.5 = 0.4
        assert trust == pytest.approx(0.4, abs=0.01)

    def test_calculate_path_trust_single(self) -> None:
        """Should return 1.0 for single-element path."""
        network = RelationshipNetwork()

        trust = network.calculate_path_trust(["alice"])

        assert trust == 1.0


class TestNetworkQueries:
    """Tests for network query methods."""

    def test_get_common_connections(self) -> None:
        """Should find individuals connected to both."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["alice", "bob"]))
        network.add_relationship(create_relationship(individual_ids=["alice", "carol"]))
        network.add_relationship(create_relationship(individual_ids=["david", "bob"]))
        network.add_relationship(create_relationship(individual_ids=["david", "carol"]))

        common = network.get_common_connections("alice", "david")

        assert common == {"bob", "carol"}

    def test_get_common_connections_none(self) -> None:
        """Should return empty set if no common connections."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["alice", "bob"]))
        network.add_relationship(create_relationship(individual_ids=["carol", "david"]))

        common = network.get_common_connections("alice", "carol")

        assert common == set()

    def test_get_relationship_count(self) -> None:
        """Should count relationships for an individual."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["alice", "bob"]))
        network.add_relationship(create_relationship(individual_ids=["alice", "carol"]))
        network.add_relationship(create_relationship(individual_ids=["bob", "carol"]))

        assert network.get_relationship_count("alice") == 2
        assert network.get_relationship_count("david") == 0

    def test_get_all_individuals(self) -> None:
        """Should get all individuals in network."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["alice", "bob"]))
        network.add_relationship(create_relationship(individual_ids=["carol", "david"]))

        all_individuals = network.get_all_individuals()

        assert all_individuals == {"alice", "bob", "carol", "david"}

    def test_get_relationships_by_type(self) -> None:
        """Should filter by relationship type."""
        network = RelationshipNetwork()
        network.add_relationship(
            create_relationship(
                individual_ids=["alice", "bob"],
                relationship_type="friends",
            )
        )
        network.add_relationship(
            create_relationship(
                individual_ids=["alice", "carol"],
                relationship_type="coworkers",
            )
        )
        network.add_relationship(
            create_relationship(
                individual_ids=["bob", "david"],
                relationship_type="friends",
            )
        )

        friends = network.get_relationships_by_type("friends")

        assert len(friends) == 2

    def test_update_trust_in_network(self) -> None:
        """Should update trust through network."""
        network = RelationshipNetwork()
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            trust={"alice": 0.5, "bob": 0.5},
        )
        network.add_relationship(rel)

        new_trust = network.update_trust("alice", "bob", 0.2, "helped out")

        assert new_trust is not None
        assert new_trust == pytest.approx(0.7, abs=0.01)

    def test_update_trust_no_relationship(self) -> None:
        """Should return None if no relationship exists."""
        network = RelationshipNetwork()

        result = network.update_trust("alice", "bob", 0.2)

        assert result is None


class TestNetworkIteration:
    """Tests for network iteration."""

    def test_len(self) -> None:
        """Should return number of relationships."""
        network = RelationshipNetwork()
        network.add_relationship(create_relationship(individual_ids=["a", "b"]))
        network.add_relationship(create_relationship(individual_ids=["c", "d"]))

        assert len(network) == 2

    def test_iter(self) -> None:
        """Should iterate over relationships."""
        network = RelationshipNetwork()
        rel1 = create_relationship(individual_ids=["a", "b"])
        rel2 = create_relationship(individual_ids=["c", "d"])
        network.add_relationship(rel1)
        network.add_relationship(rel2)

        rels = list(network)

        assert len(rels) == 2
        assert rel1 in rels
        assert rel2 in rels


class TestNetworkSerialization:
    """Tests for network serialization."""

    def test_to_dict(self) -> None:
        """Should serialize network to dictionary."""
        network = RelationshipNetwork()
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            history="Friends",
        )
        network.add_relationship(rel)

        data = network.to_dict()

        assert "relationships" in data
        assert rel.id in data["relationships"]

    def test_from_dict(self) -> None:
        """Should deserialize network from dictionary."""
        network = RelationshipNetwork()
        rel = create_relationship(
            individual_ids=["alice", "bob"],
            trust={"alice": 0.8, "bob": 0.7},
            history="Old friends",
        )
        network.add_relationship(rel)

        data = network.to_dict()
        restored = RelationshipNetwork.from_dict(data)

        assert len(restored) == 1
        restored_rel = restored.get_relationship(rel.id)
        assert restored_rel is not None
        assert restored_rel.history == "Old friends"
        assert restored_rel.get_trust("alice", "bob") == 0.8
