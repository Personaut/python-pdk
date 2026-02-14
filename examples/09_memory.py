#!/usr/bin/env python3
"""Example 09: Memory System

This example demonstrates the **Memory** system in Personaut PDK.

The memory system provides:
    • Memory types — IndividualMemory, SharedMemory, PrivateMemory
    • Trust-gated access — private memories require minimum trust to view
    • Vector storage — InMemoryVectorStore for semantic similarity search
    • Convenience functions — search_memories, filter_accessible_memories
"""

# ── PDK imports ────────────────────────────────────────────────────────────
from personaut import create_individual
from personaut.memory import (
    InMemoryVectorStore,
    Memory,
    MemoryType,
    PrivateMemory,
    SharedMemory,
    create_individual_memory,
    create_memory,
    create_private_memory,
    create_shared_memory,
    filter_accessible_memories,
    search_memories,
)


def main() -> None:
    print("=" * 60)
    print("Example 09: Memory System")
    print("=" * 60)

    # Create two individuals for the examples
    sarah = create_individual(
        name="Sarah",
        traits={"warmth": 0.9, "liveliness": 0.8},
        metadata={"occupation": "barista"},
    )
    mike = create_individual(
        name="Mike",
        traits={"reasoning": 0.9},
        metadata={"occupation": "architect"},
    )

    # ── 1. Create a basic memory ──────────────────────────────────────
    print("\n1. Basic memory (create_memory):")
    memory1 = create_memory(
        description="First day working at Sunrise Cafe — spilled a latte on the counter",
    )
    print(f"   Memory: {memory1.description}")
    print(f"   Type: {memory1.memory_type.value}")
    print(f"   ID: {memory1.id}")

    # ── 2. Individual memory (owned by a person) ──────────────────────
    print("\n2. Individual memory (create_individual_memory):")
    ind_mem = create_individual_memory(
        owner_id=sarah.id,
        description="Learned to make the perfect rosetta latte art",
        salience=0.8,
    )
    print(f"   Description: {ind_mem.description}")
    print(f"   Owner: {ind_mem.owner_id}")
    print(f"   Salience: {ind_mem.salience}")

    # ── 3. Private memories with trust gating ─────────────────────────
    print("\n3. Trust-gated private memories:")
    casual_secret = create_private_memory(
        owner_id=sarah.id,
        description="I love trying new coffee roasts from Ethiopia",
        trust_threshold=0.1,  # Tells anyone
    )
    personal_secret = create_private_memory(
        owner_id=sarah.id,
        description="Sometimes I worry I'm not good enough at this job",
        trust_threshold=0.6,  # Only tells close friends
    )
    deep_secret = create_private_memory(
        owner_id=sarah.id,
        description="I've been applying to culinary school in secret",
        trust_threshold=0.9,  # Only tells closest confidants
    )

    all_memories: list[Memory] = [casual_secret, personal_secret, deep_secret]
    for trust in [0.2, 0.5, 0.7, 1.0]:
        accessible = filter_accessible_memories(all_memories, trust)
        names = [m.description[:30] + "..." for m in accessible]
        print(f"   Trust {trust:.1f}: {len(accessible)} accessible → {names}")

    # ── 4. Private memory features ────────────────────────────────────
    print("\n4. Private memory features:")
    print(f"   Can access at 0.5? {deep_secret.can_access(0.5)}")
    print(f"   Can access at 0.95? {deep_secret.can_access(0.95)}")
    print(f"   Sensitivity: {deep_secret.get_sensitivity_level()}")
    print(f"   Belongs to Sarah? {deep_secret.belongs_to(sarah.id)}")

    # ── 5. Shared memories (between individuals) ──────────────────────
    print("\n5. Shared memories:")
    shared = create_shared_memory(
        description="That time we both got caught in the rain and ran into the cafe laughing",
        participant_ids=[sarah.id, mike.id],
        perspectives={
            sarah.id: "I remember how hard we both laughed!",
            mike.id: "I was just trying to keep my sketches dry...",
        },
    )
    print(f"   Participants: {len(shared.participant_ids)}")
    print(f"   Description: {shared.description}")
    print(f"   Sarah's perspective: {shared.perspectives.get(sarah.id)}")
    print(f"   Mike's perspective: {shared.perspectives.get(mike.id)}")

    # ── 6. Vector store — storing and searching ───────────────────────
    print("\n6. In-memory vector store:")
    store = InMemoryVectorStore()

    # Create memories with fake embeddings
    # (In production you'd use get_embedding() for real embeddings)
    memories_with_embeddings = [
        (
            create_memory(description="Learned to make the perfect espresso shot"),
            [0.9, 0.1, 0.3, 0.0, 0.0],  # Coffee-related
        ),
        (
            create_memory(description="Had a wonderful conversation about art with a customer"),
            [0.2, 0.8, 0.1, 0.1, 0.0],  # Social-related
        ),
        (
            create_memory(description="Felt nervous before the regional latte art competition"),
            [0.7, 0.0, 0.6, 0.4, 0.0],  # Competition-related
        ),
    ]

    for memory, embedding in memories_with_embeddings:
        store.store(memory, embedding)

    print(f"   Stored {store.count()} memories")

    # ── 7. Search by similarity ───────────────────────────────────────
    print("\n7. Similarity search:")
    # Search with a coffee-related query embedding
    coffee_query = [0.85, 0.05, 0.2, 0.0, 0.0]
    results = store.search(coffee_query, limit=2)
    print(f"   Query: 'coffee-related' (embedding)")
    for memory, score in results:
        print(f"   {score:.3f}: {memory.description}")

    # Search with a social-related query embedding
    social_query = [0.1, 0.9, 0.0, 0.1, 0.0]
    results = store.search(social_query, limit=2)
    print(f"\n   Query: 'social-related' (embedding)")
    for memory, score in results:
        print(f"   {score:.3f}: {memory.description}")

    # ── 8. Search with owner filtering ────────────────────────────────
    print("\n8. search_memories with embed function:")

    def simple_embed(text: str) -> list[float]:
        """Toy embedding: word-presence for coffee/art/nervous/chat/work."""
        lower = text.lower()
        return [
            1.0 if "coffee" in lower or "espresso" in lower else 0.0,
            1.0 if "art" in lower or "conversation" in lower else 0.0,
            1.0 if "nervous" in lower or "competition" in lower else 0.0,
            1.0 if "customer" in lower or "chat" in lower else 0.0,
            0.0,
        ]

    results = search_memories(
        store=store,
        query="tell me about coffee",
        embed_func=simple_embed,
        limit=2,
    )
    print(f"   Query: 'tell me about coffee'")
    for memory, score in results:
        print(f"   {score:.3f}: {memory.description}")

    # ── 9. Memory embedding text ──────────────────────────────────────
    print("\n9. Memory embedding text:")
    embed_text = memory1.to_embedding_text()
    print(f"   '{embed_text}'")

    # ── 10. Memory serialization ──────────────────────────────────────
    print("\n10. Memory serialization:")
    data = memory1.to_dict()
    print(f"   Keys: {list(data.keys())}")
    restored = Memory.from_dict(data)
    print(f"   Round-trip: {restored.description[:40]}...")
    print(f"   Type match: {restored.memory_type == memory1.memory_type}")

    print("\n" + "=" * 60)
    print("✅ Example 09 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: The memory system lets personas accumulate")
    print("experiences with trust-gated access and semantic retrieval,")
    print("enabling realistic recall during conversations.")


if __name__ == "__main__":
    main()
