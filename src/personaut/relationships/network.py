"""Relationship network for Personaut PDK.

This module provides the RelationshipNetwork class for managing multiple
relationships as a graph structure, enabling queries across the network.

Example:
    >>> from personaut.relationships import RelationshipNetwork, create_relationship
    >>>
    >>> network = RelationshipNetwork()
    >>>
    >>> # Add relationships
    >>> network.add_relationship(create_relationship(
    ...     individual_ids=["alice", "bob"],
    ...     trust={"alice": 0.8, "bob": 0.7},
    ... ))
    >>> network.add_relationship(create_relationship(
    ...     individual_ids=["bob", "carol"],
    ...     trust={"bob": 0.6, "carol": 0.9},
    ... ))
    >>>
    >>> # Query network
    >>> network.get_relationships("bob")  # Returns both relationships
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from personaut.relationships.relationship import Relationship
from personaut.relationships.trust import get_stranger_trust


@dataclass
class RelationshipNetwork:
    """A network of relationships between individuals.

    Manages multiple relationships as a graph, allowing queries for
    connections, paths, and aggregate trust calculations.

    Attributes:
        relationships: Dict of relationship_id -> Relationship.

    Example:
        >>> network = RelationshipNetwork()
        >>> network.add_relationship(relationship)
        >>> alice_relationships = network.get_relationships("alice")
    """

    relationships: dict[str, Relationship] = field(default_factory=dict)

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the network.

        Args:
            relationship: The relationship to add.
        """
        self.relationships[relationship.id] = relationship

    def remove_relationship(self, relationship_id: str) -> bool:
        """Remove a relationship from the network.

        Args:
            relationship_id: ID of the relationship to remove.

        Returns:
            True if removed, False if not found.
        """
        if relationship_id in self.relationships:
            del self.relationships[relationship_id]
            return True
        return False

    def get_relationship(self, relationship_id: str) -> Relationship | None:
        """Get a relationship by ID.

        Args:
            relationship_id: ID of the relationship.

        Returns:
            The relationship if found, None otherwise.
        """
        return self.relationships.get(relationship_id)

    def get_relationships(self, individual_id: str) -> list[Relationship]:
        """Get all relationships involving an individual.

        Args:
            individual_id: ID of the individual.

        Returns:
            List of relationships involving the individual.

        Example:
            >>> alice_rels = network.get_relationships("alice")
        """
        return [rel for rel in self.relationships.values() if rel.has_individual(individual_id)]

    def get_relationship_between(
        self,
        ind_a: str,
        ind_b: str,
    ) -> Relationship | None:
        """Get the relationship between two specific individuals.

        Args:
            ind_a: First individual's ID.
            ind_b: Second individual's ID.

        Returns:
            The relationship if found, None otherwise.

        Example:
            >>> rel = network.get_relationship_between("alice", "bob")
        """
        for rel in self.relationships.values():
            if rel.involves(ind_a, ind_b):
                return rel
        return None

    def get_connected_individuals(self, individual_id: str) -> set[str]:
        """Get all individuals connected to someone.

        Args:
            individual_id: ID of the individual.

        Returns:
            Set of connected individual IDs.

        Example:
            >>> connected = network.get_connected_individuals("alice")
            >>> "bob" in connected
            True
        """
        connected: set[str] = set()
        for rel in self.get_relationships(individual_id):
            for ind_id in rel.individual_ids:
                if ind_id != individual_id:
                    connected.add(ind_id)
        return connected

    def get_trust_in_network(
        self,
        from_individual: str,
        to_individual: str,
    ) -> float:
        """Get trust between two individuals in the network.

        If they have a direct relationship, returns that trust.
        If not, returns stranger trust.

        Args:
            from_individual: ID of the trusting individual.
            to_individual: ID of the trusted individual.

        Returns:
            Trust level (0.0-1.0).

        Example:
            >>> network.get_trust_in_network("alice", "bob")
            0.8
        """
        rel = self.get_relationship_between(from_individual, to_individual)
        if rel is not None:
            return rel.get_trust(from_individual, to_individual)
        return get_stranger_trust()

    def find_path(
        self,
        from_individual: str,
        to_individual: str,
        max_depth: int = 6,
    ) -> list[str] | None:
        """Find a relationship path between two individuals.

        Uses breadth-first search to find the shortest path.

        Args:
            from_individual: Starting individual ID.
            to_individual: Target individual ID.
            max_depth: Maximum path length to search.

        Returns:
            List of individual IDs forming the path, or None if no path.

        Example:
            >>> path = network.find_path("alice", "david")
            >>> path
            ['alice', 'bob', 'carol', 'david']
        """
        if from_individual == to_individual:
            return [from_individual]

        visited: set[str] = set()
        queue: list[tuple[str, list[str]]] = [(from_individual, [from_individual])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            for connected in self.get_connected_individuals(current):
                if connected == to_individual:
                    return [*path, connected]
                if connected not in visited:
                    queue.append((connected, [*path, connected]))

        return None

    def calculate_path_trust(self, path: list[str]) -> float:
        """Calculate the trust along a path of individuals.

        Trust diminishes along longer paths using a decay factor.

        Args:
            path: List of individual IDs forming the path.

        Returns:
            Aggregate trust level along the path.

        Example:
            >>> network.calculate_path_trust(["alice", "bob", "carol"])
            0.56  # 0.8 * 0.7
        """
        if len(path) < 2:
            return 1.0

        trust = 1.0
        for i in range(len(path) - 1):
            link_trust = self.get_trust_in_network(path[i], path[i + 1])
            trust *= link_trust

        return trust

    def get_common_connections(self, ind_a: str, ind_b: str) -> set[str]:
        """Get individuals connected to both specified individuals.

        Args:
            ind_a: First individual's ID.
            ind_b: Second individual's ID.

        Returns:
            Set of individuals connected to both.

        Example:
            >>> common = network.get_common_connections("alice", "carol")
            >>> "bob" in common
            True
        """
        connections_a = self.get_connected_individuals(ind_a)
        connections_b = self.get_connected_individuals(ind_b)
        return connections_a & connections_b

    def get_relationship_count(self, individual_id: str) -> int:
        """Get the number of relationships for an individual.

        Args:
            individual_id: ID of the individual.

        Returns:
            Number of relationships.
        """
        return len(self.get_relationships(individual_id))

    def get_all_individuals(self) -> set[str]:
        """Get all individuals in the network.

        Returns:
            Set of all individual IDs.
        """
        individuals: set[str] = set()
        for rel in self.relationships.values():
            individuals.update(rel.individual_ids)
        return individuals

    def get_relationships_by_type(self, relationship_type: str) -> list[Relationship]:
        """Get all relationships of a specific type.

        Args:
            relationship_type: Type to filter by.

        Returns:
            List of matching relationships.
        """
        return [rel for rel in self.relationships.values() if rel.relationship_type == relationship_type]

    def update_trust(
        self,
        from_individual: str,
        to_individual: str,
        change: float,
        reason: str = "",
    ) -> float | None:
        """Update trust between individuals in the network.

        Args:
            from_individual: ID of the trusting individual.
            to_individual: ID of the trusted individual.
            change: Amount to change trust.
            reason: Optional reason for the change.

        Returns:
            New trust value, or None if no relationship found.
        """
        rel = self.get_relationship_between(from_individual, to_individual)
        if rel is None:
            return None

        return rel.update_trust(from_individual, to_individual, change, reason)

    def __len__(self) -> int:
        """Get the number of relationships in the network."""
        return len(self.relationships)

    def __iter__(self) -> Iterator[Relationship]:
        """Iterate over relationships."""
        return iter(self.relationships.values())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"relationships": {rel_id: rel.to_dict() for rel_id, rel in self.relationships.items()}}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RelationshipNetwork:
        """Create from dictionary."""
        relationships = {
            rel_id: Relationship.from_dict(rel_data) for rel_id, rel_data in data.get("relationships", {}).items()
        }
        return cls(relationships=relationships)


__all__ = [
    "RelationshipNetwork",
]
