"""Relationship implementation for Personaut PDK.

This module provides the Relationship class for modeling connections
between individuals with trust dynamics and shared memories.

Example:
    >>> from personaut.relationships import create_relationship
    >>>
    >>> relationship = create_relationship(
    ...     individual_ids=["sarah", "mike"],
    ...     trust={"sarah": 0.8, "mike": 0.5},
    ...     history="Met at college, roommates for 2 years",
    ... )
    >>>
    >>> # Get trust between individuals
    >>> relationship.get_trust("sarah", "mike")
    0.8
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from personaut.relationships.trust import (
    TrustLevel,
    calculate_trust_change,
    clamp_trust,
    get_default_trust,
    get_trust_level,
)


@dataclass
class TrustChange:
    """Record of a trust change event.

    Attributes:
        timestamp: When the change occurred.
        from_individual: Who is trusting.
        to_individual: Who is being trusted.
        old_value: Previous trust value.
        new_value: New trust value.
        reason: Optional reason for the change.
    """

    timestamp: datetime
    from_individual: str
    to_individual: str
    old_value: float
    new_value: float
    reason: str = ""


@dataclass
class Relationship:
    """A relationship between two or more individuals.

    Models the connection between individuals including bilateral or
    multilateral trust levels, shared memories, and relationship history.

    Attributes:
        id: Unique identifier for the relationship.
        individual_ids: List of individual IDs in this relationship.
        trust: Directional trust levels {from_id -> {to_id -> level}}.
        shared_memory_ids: IDs of shared memories.
        history: Description of the relationship history.
        relationship_type: Type of relationship (e.g., "friends", "coworkers").
        created_at: When the relationship was created.
        trust_history: Log of trust changes.

    Example:
        >>> rel = Relationship(
        ...     individual_ids=["alice", "bob"],
        ...     trust={"alice": {"bob": 0.8}, "bob": {"alice": 0.6}},
        ...     history="College roommates",
        ... )
        >>> rel.get_trust("alice", "bob")
        0.8
    """

    individual_ids: list[str]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trust: dict[str, dict[str, float]] = field(default_factory=dict)
    shared_memory_ids: list[str] = field(default_factory=list)
    history: str = ""
    relationship_type: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    trust_history: list[TrustChange] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize trust matrix if not provided."""
        # Ensure all individuals have trust entries
        for ind_id in self.individual_ids:
            if ind_id not in self.trust:
                self.trust[ind_id] = {}

            # Initialize trust toward other individuals
            for other_id in self.individual_ids:
                if other_id != ind_id and other_id not in self.trust[ind_id]:
                    self.trust[ind_id][other_id] = get_default_trust()

    def get_trust(self, from_individual: str, to_individual: str) -> float:
        """Get trust level from one individual to another.

        Args:
            from_individual: ID of the trusting individual.
            to_individual: ID of the trusted individual.

        Returns:
            Trust level (0.0-1.0), or 0.0 if not found.

        Example:
            >>> rel.get_trust("alice", "bob")
            0.8
        """
        if from_individual not in self.trust:
            return 0.0
        return self.trust[from_individual].get(to_individual, 0.0)

    def get_mutual_trust(self, ind_a: str, ind_b: str) -> float:
        """Get the average mutual trust between two individuals.

        Args:
            ind_a: First individual's ID.
            ind_b: Second individual's ID.

        Returns:
            Average of bidirectional trust levels.

        Example:
            >>> rel.get_mutual_trust("alice", "bob")
            0.7  # Average of 0.8 and 0.6
        """
        trust_ab = self.get_trust(ind_a, ind_b)
        trust_ba = self.get_trust(ind_b, ind_a)
        return (trust_ab + trust_ba) / 2

    def get_trust_asymmetry(self, ind_a: str, ind_b: str) -> float:
        """Get the trust asymmetry between two individuals.

        Positive means ind_a trusts ind_b more than vice versa.

        Args:
            ind_a: First individual's ID.
            ind_b: Second individual's ID.

        Returns:
            Difference in trust levels (can be negative).

        Example:
            >>> rel.get_trust_asymmetry("alice", "bob")
            0.2  # Alice trusts Bob 0.2 more than Bob trusts Alice
        """
        trust_ab = self.get_trust(ind_a, ind_b)
        trust_ba = self.get_trust(ind_b, ind_a)
        return trust_ab - trust_ba

    def update_trust(
        self,
        from_individual: str,
        to_individual: str,
        change: float,
        reason: str = "",
    ) -> float:
        """Update trust from one individual to another.

        Args:
            from_individual: ID of the trusting individual.
            to_individual: ID of the trusted individual.
            change: Amount to change trust (positive or negative).
            reason: Optional reason for the change.

        Returns:
            The new trust value.

        Example:
            >>> rel.update_trust("alice", "bob", 0.1, "helped move apartments")
            0.9
        """
        current = self.get_trust(from_individual, to_individual)
        new_value, _ = calculate_trust_change(current, change, reason)

        # Ensure structure exists
        if from_individual not in self.trust:
            self.trust[from_individual] = {}

        self.trust[from_individual][to_individual] = new_value

        # Record change
        self.trust_history.append(
            TrustChange(
                timestamp=datetime.now(),
                from_individual=from_individual,
                to_individual=to_individual,
                old_value=current,
                new_value=new_value,
                reason=reason,
            )
        )

        return new_value

    def set_trust(
        self,
        from_individual: str,
        to_individual: str,
        value: float,
    ) -> None:
        """Set trust to a specific value.

        Args:
            from_individual: ID of the trusting individual.
            to_individual: ID of the trusted individual.
            value: Trust value to set (0.0-1.0).
        """
        if from_individual not in self.trust:
            self.trust[from_individual] = {}

        self.trust[from_individual][to_individual] = clamp_trust(value)

    def get_trust_level(self, from_individual: str, to_individual: str) -> TrustLevel:
        """Get the trust level enum between individuals.

        Args:
            from_individual: ID of the trusting individual.
            to_individual: ID of the trusted individual.

        Returns:
            The TrustLevel enum value.
        """
        trust_value = self.get_trust(from_individual, to_individual)
        return get_trust_level(trust_value)

    def add_individual(self, individual_id: str, default_trust: float | None = None) -> None:
        """Add an individual to the relationship.

        Args:
            individual_id: ID of the individual to add.
            default_trust: Optional default trust level.
        """
        if individual_id in self.individual_ids:
            return

        self.individual_ids.append(individual_id)

        # Initialize trust with existing members
        trust_value = default_trust if default_trust is not None else get_default_trust()
        self.trust[individual_id] = {}

        for other_id in self.individual_ids:
            if other_id != individual_id:
                self.trust[individual_id][other_id] = trust_value
                self.trust[other_id][individual_id] = trust_value

    def remove_individual(self, individual_id: str) -> None:
        """Remove an individual from the relationship.

        Args:
            individual_id: ID of the individual to remove.
        """
        if individual_id not in self.individual_ids:
            return

        self.individual_ids.remove(individual_id)

        # Remove from trust matrix
        self.trust.pop(individual_id, None)
        for other_trust in self.trust.values():
            other_trust.pop(individual_id, None)

    def add_shared_memory(self, memory_id: str) -> None:
        """Add a shared memory to the relationship.

        Args:
            memory_id: ID of the shared memory.
        """
        if memory_id not in self.shared_memory_ids:
            self.shared_memory_ids.append(memory_id)

    def has_individual(self, individual_id: str) -> bool:
        """Check if an individual is part of this relationship.

        Args:
            individual_id: ID to check.

        Returns:
            True if the individual is in the relationship.
        """
        return individual_id in self.individual_ids

    def involves(self, *individual_ids: str) -> bool:
        """Check if the relationship involves all specified individuals.

        Args:
            *individual_ids: IDs to check.

        Returns:
            True if all individuals are in the relationship.
        """
        return all(ind_id in self.individual_ids for ind_id in individual_ids)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "individual_ids": self.individual_ids,
            "trust": self.trust,
            "shared_memory_ids": self.shared_memory_ids,
            "history": self.history,
            "relationship_type": self.relationship_type,
            "created_at": self.created_at.isoformat(),
            "trust_history": [
                {
                    "timestamp": tc.timestamp.isoformat(),
                    "from_individual": tc.from_individual,
                    "to_individual": tc.to_individual,
                    "old_value": tc.old_value,
                    "new_value": tc.new_value,
                    "reason": tc.reason,
                }
                for tc in self.trust_history
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Relationship:
        """Create from dictionary."""
        trust_history = [
            TrustChange(
                timestamp=datetime.fromisoformat(tc["timestamp"]),
                from_individual=tc["from_individual"],
                to_individual=tc["to_individual"],
                old_value=tc["old_value"],
                new_value=tc["new_value"],
                reason=tc.get("reason", ""),
            )
            for tc in data.get("trust_history", [])
        ]

        return cls(
            id=data["id"],
            individual_ids=data["individual_ids"],
            trust=data.get("trust", {}),
            shared_memory_ids=data.get("shared_memory_ids", []),
            history=data.get("history", ""),
            relationship_type=data.get("relationship_type", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            trust_history=trust_history,
        )


def create_relationship(
    individual_ids: list[str],
    trust: dict[str, float] | dict[str, dict[str, float]] | None = None,
    history: str = "",
    relationship_type: str = "",
) -> Relationship:
    """Create a new relationship.

    Factory function for creating Relationship instances.

    Args:
        individual_ids: List of individual IDs in the relationship.
            Must contain at least 2 unique IDs; self-relationships are rejected.
        trust: Trust levels. Can be:
            - Simple dict {id -> level} for symmetric trust
            - Nested dict {from_id -> {to_id -> level}} for asymmetric
            Trust values are clamped to [0.0, 1.0].
        history: Description of relationship history.
        relationship_type: Type of relationship.

    Returns:
        A new Relationship instance.

    Raises:
        ValidationError: If individual_ids contains fewer than 2 unique IDs.

    Example:
        >>> # Symmetric trust
        >>> rel = create_relationship(
        ...     individual_ids=["alice", "bob"],
        ...     trust={"alice": 0.8, "bob": 0.6},
        ...     history="Friends since childhood",
        ... )
        >>>
        >>> # Asymmetric trust
        >>> rel = create_relationship(
        ...     individual_ids=["alice", "bob"],
        ...     trust={
        ...         "alice": {"bob": 0.9},
        ...         "bob": {"alice": 0.5},
        ...     },
        ... )
    """
    from personaut.types.exceptions import ValidationError as _ValidationError

    # Validate: require at least 2 unique individuals
    unique_ids = list(dict.fromkeys(individual_ids))  # preserve order, deduplicate
    if len(unique_ids) < 2:
        raise _ValidationError(
            f"Relationship requires at least 2 unique individual IDs (got {individual_ids!r})",
            field="individual_ids",
            value=individual_ids,
        )

    # Validate and convert trust dict to nested format
    nested_trust: dict[str, dict[str, float]] = {}

    if trust:
        # Validate all trust values are in [0.0, 1.0]
        first_value = next(iter(trust.values()), None)
        if isinstance(first_value, dict):
            # Nested format — validate then store
            for key, value in trust.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        if not isinstance(v, (int, float)) or v < 0.0 or v > 1.0:
                            raise _ValidationError(
                                f"Trust value for {key}→{k} must be between 0.0 and 1.0 (got {v!r})",
                                field="trust",
                                value=v,
                            )
                    nested_trust[key] = {k: float(v) for k, v in value.items()}
        else:
            # Simple format — validate then use as symmetric trust
            for ind_id, raw_trust in trust.items():
                if isinstance(raw_trust, (int, float)) and (raw_trust < 0.0 or raw_trust > 1.0):
                    raise _ValidationError(
                        f"Trust value for '{ind_id}' must be between 0.0 and 1.0 (got {raw_trust!r})",
                        field="trust",
                        value=raw_trust,
                    )

            for ind_id in unique_ids:
                nested_trust[ind_id] = {}
                trust_val = trust.get(ind_id)
                if isinstance(trust_val, (int, float)):
                    ind_trust = float(trust_val)
                else:
                    ind_trust = get_default_trust()
                for other_id in unique_ids:
                    if other_id != ind_id:
                        nested_trust[ind_id][other_id] = ind_trust

    return Relationship(
        individual_ids=unique_ids,
        trust=nested_trust,
        history=history,
        relationship_type=relationship_type,
    )


__all__ = [
    "Relationship",
    "TrustChange",
    "create_relationship",
]
