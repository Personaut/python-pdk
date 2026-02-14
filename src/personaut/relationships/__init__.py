"""Relationships module for Personaut PDK.

This module provides relationship modeling between individuals,
including trust dynamics, shared memories, and network queries.

Basic Usage:
    >>> from personaut.relationships import create_relationship
    >>>
    >>> # Create a relationship with trust levels
    >>> rel = create_relationship(
    ...     individual_ids=["sarah", "mike"],
    ...     trust={"sarah": 0.8, "mike": 0.5},
    ...     history="Roommates in college for 2 years",
    ...     relationship_type="friends",
    ... )
    >>>
    >>> # Get trust between individuals
    >>> rel.get_trust("sarah", "mike")
    0.8
    >>> rel.get_trust("mike", "sarah")
    0.5
    >>>
    >>> # Update trust
    >>> rel.update_trust("mike", "sarah", 0.2, "helped during crisis")
    0.7

Trust Levels:
    >>> from personaut.relationships import get_trust_level, TrustLevel
    >>>
    >>> level = get_trust_level(0.85)
    >>> level == TrustLevel.COMPLETE
    True

Relationship Networks:
    >>> from personaut.relationships import RelationshipNetwork
    >>>
    >>> network = RelationshipNetwork()
    >>> network.add_relationship(rel)
    >>>
    >>> # Query the network
    >>> sarah_rels = network.get_relationships("sarah")
    >>> connected = network.get_connected_individuals("sarah")

Trust Level Meanings:
    - NONE (0.0-0.1): Actively suspicious or hostile
    - MINIMAL (0.1-0.25): Cautious acquaintance
    - LOW (0.25-0.4): Guarded, withholds information
    - MODERATE (0.4-0.6): Open communication, some reservations
    - HIGH (0.6-0.8): Shares personal information freely
    - COMPLETE (0.8-1.0): Deep bond, shares everything
"""

from personaut.relationships.network import RelationshipNetwork
from personaut.relationships.relationship import (
    Relationship,
    TrustChange,
    create_relationship,
)
from personaut.relationships.trust import (
    TRUST_BEHAVIORS,
    TRUST_DESCRIPTIONS,
    TRUST_THRESHOLDS,
    TrustInfo,
    TrustLevel,
    calculate_trust_change,
    clamp_trust,
    get_default_trust,
    get_stranger_trust,
    get_trust_info,
    get_trust_level,
    trust_allows_disclosure,
)


__all__ = [
    # Trust utilities
    "TrustLevel",
    "TrustInfo",
    "TRUST_THRESHOLDS",
    "TRUST_DESCRIPTIONS",
    "TRUST_BEHAVIORS",
    "get_trust_level",
    "get_trust_info",
    "clamp_trust",
    "calculate_trust_change",
    "trust_allows_disclosure",
    "get_default_trust",
    "get_stranger_trust",
    # Relationship
    "Relationship",
    "TrustChange",
    "create_relationship",
    # Network
    "RelationshipNetwork",
]
