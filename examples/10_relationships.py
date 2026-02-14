#!/usr/bin/env python3
"""Example 10: Relationships & Trust

This example demonstrates the **Relationships** system in Personaut PDK.

Key concepts:
    • Relationship — connection between two or more individuals with
      asymmetric trust levels (Sarah might trust Mike more than he trusts her)
    • TrustLevel enum — NONE, MINIMAL, LOW, MODERATE, HIGH, COMPLETE
    • Trust utilities — get_trust_level, trust_allows_disclosure, etc.
    • RelationshipNetwork — graph of all relationships for querying
"""

# ── PDK imports ────────────────────────────────────────────────────────────
from personaut import create_individual
from personaut.relationships import (
    RelationshipNetwork,
    TrustLevel,
    calculate_trust_change,
    create_relationship,
    get_default_trust,
    get_stranger_trust,
    get_trust_info,
    get_trust_level,
    trust_allows_disclosure,
)


def main() -> None:
    print("=" * 60)
    print("Example 10: Relationships & Trust")
    print("=" * 60)

    # Create individuals
    sarah = create_individual(name="Sarah", metadata={"occupation": "barista"})
    mike  = create_individual(name="Mike",  metadata={"occupation": "architect"})
    eve   = create_individual(name="Eve",   metadata={"occupation": "researcher"})

    # ── 1. Trust levels ───────────────────────────────────────────────
    print("\n1. Trust level scale:")
    for value in [0.0, 0.15, 0.3, 0.5, 0.7, 0.9]:
        level = get_trust_level(value)
        info = get_trust_info(value)
        print(f"   {value:.2f} → {level.value:<10}  {info.description}")

    # ── 2. Stranger trust ─────────────────────────────────────────────
    print("\n2. Default trust values:")
    print(f"   Default trust: {get_default_trust()}")
    print(f"   Stranger trust: {get_stranger_trust()}")

    # ── 3. Create a relationship ──────────────────────────────────────
    print("\n3. Creating a relationship:")
    friends = create_relationship(
        individual_ids=[sarah.id, mike.id],
        trust={sarah.id: 0.8, mike.id: 0.5},
        history="Roommates in college for 2 years",
        relationship_type="friends",
    )
    print(f"   Type: {friends.relationship_type}")
    print(f"   History: {friends.history}")
    print(f"   Sarah trusts Mike: {friends.get_trust(sarah.id, mike.id)}")
    print(f"   Mike trusts Sarah: {friends.get_trust(mike.id, sarah.id)}")
    print("   → Trust is asymmetric!")

    # ── 4. Update trust ──────────────────────────────────────────────
    print("\n4. Trust changes over time:")
    original = friends.get_trust(mike.id, sarah.id)
    new_trust = friends.update_trust(
        mike.id, sarah.id,
        change=0.2,
        reason="Sarah helped Mike through a difficult time",
    )
    print(f"   Mike → Sarah trust: {original:.1f} → {new_trust:.2f}")
    print(f"   Trust history: {len(friends.trust_history)} event(s)")
    print(f"   Latest reason: {friends.trust_history[-1].reason}")

    # ── 5. Trust-gated disclosure ─────────────────────────────────────
    print("\n5. Trust-gated disclosure:")
    scenarios = [
        ("casual hobbies", 0.2),
        ("personal struggles", 0.6),
        ("deepest secrets", 0.9),
    ]
    sarah_mike_trust = friends.get_trust(sarah.id, mike.id)
    print(f"   Sarah → Mike trust: {sarah_mike_trust}")
    for topic, required_trust in scenarios:
        allowed = trust_allows_disclosure(sarah_mike_trust, required_trust)
        marker = "✅" if allowed else "❌"
        print(f"   {marker} '{topic}' (needs {required_trust}): {allowed}")

    # ── 6. Calculate trust change ─────────────────────────────────────
    print("\n6. Trust change calculation:")
    new_val, desc = calculate_trust_change(
        current=0.4,
        change=0.2,
        reason="Very positive interaction",
    )
    print(f"   Current: 0.40, Change: +0.20")
    print(f"   Result: {new_val:.2f}")
    print(f"   Description: {desc}")

    # ── 7. Relationship network ───────────────────────────────────────
    print("\n7. Relationship network:")
    network = RelationshipNetwork()

    # Add friendships
    network.add_relationship(friends)  # Sarah ↔ Mike

    colleagues = create_relationship(
        individual_ids=[mike.id, eve.id],
        trust={mike.id: 0.6, eve.id: 0.7},
        relationship_type="colleagues",
    )
    network.add_relationship(colleagues)

    acquaintances = create_relationship(
        individual_ids=[sarah.id, eve.id],
        trust={sarah.id: 0.3, eve.id: 0.4},
        relationship_type="acquaintances",
    )
    network.add_relationship(acquaintances)

    # Query the network
    sarah_rels = network.get_relationships(sarah.id)
    print(f"   Sarah's relationships: {len(sarah_rels)}")

    connected = network.get_connected_individuals(sarah.id)
    print(f"   Sarah is connected to: {len(connected)} individuals")

    # ── 8. Network queries ────────────────────────────────────────────
    print("\n8. Network queries:")
    mike_rels = network.get_relationships(mike.id)
    print(f"   Mike's relationship count: {len(mike_rels)}")
    for rel in mike_rels:
        others = [r for r in rel.individual_ids if r != mike.id]
        for other in others:
            trust = rel.get_trust(mike.id, other)
            print(f"   Mike → {other[:8]}...: trust={trust:.2f}, type={rel.relationship_type}")

    # ── 9. Serialization ──────────────────────────────────────────────
    print("\n9. Relationship serialization:")
    data = friends.to_dict()
    print(f"   Serialized keys: {list(data.keys())}")

    print("\n" + "=" * 60)
    print("✅ Example 10 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: Relationships model asymmetric trust that changes")
    print("over time and gates what information individuals share with")
    print("each other — just like real human relationships.")


if __name__ == "__main__":
    main()
