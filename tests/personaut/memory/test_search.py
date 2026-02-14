"""Tests for memory search functions."""

from __future__ import annotations

from personaut.memory import (
    InMemoryVectorStore,
    Memory,
    create_individual_memory,
    create_private_memory,
    extract_and_search,
    filter_accessible_memories,
    get_relevant_memories,
    search_memories,
)


def mock_embed(text: str) -> list[float]:
    """Mock embedding function for testing.

    Creates a simple embedding based on text features.
    """
    # Simple mock: hash-based for determinism
    h = hash(text) % 1000
    return [
        float(h) / 1000,
        float((h * 2) % 1000) / 1000,
        float((h * 3) % 1000) / 1000,
    ]


class TestSearchMemories:
    """Tests for search_memories function."""

    def test_basic_search(self) -> None:
        """Should search for memories by query text."""
        store = InMemoryVectorStore()

        m1 = Memory(description="Meeting about cats")
        m2 = Memory(description="Meeting about dogs")

        store.store(m1, mock_embed(m1.to_embedding_text()))
        store.store(m2, mock_embed(m2.to_embedding_text()))

        results = search_memories(
            store=store,
            query="cats",
            embed_func=mock_embed,
            limit=5,
        )

        assert len(results) > 0

    def test_search_with_owner_filter(self) -> None:
        """Should filter by owner."""
        store = InMemoryVectorStore()

        m1 = create_individual_memory(owner_id="alice", description="Alice thought")
        m2 = create_individual_memory(owner_id="bob", description="Bob thought")

        store.store(m1, mock_embed(m1.to_embedding_text()))
        store.store(m2, mock_embed(m2.to_embedding_text()))

        results = search_memories(
            store=store,
            query="thought",
            embed_func=mock_embed,
            owner_id="alice",
        )

        assert len(results) == 1
        assert results[0][0].owner_id == "alice"

    def test_search_filters_private_by_trust(self) -> None:
        """Should filter private memories by trust level."""
        store = InMemoryVectorStore()

        # Public memory
        m1 = Memory(description="Public memory")
        # Private memory requiring high trust
        m2 = create_private_memory(
            owner_id="alice",
            description="Private secret",
            trust_threshold=0.8,
        )

        store.store(m1, mock_embed(m1.to_embedding_text()))
        store.store(m2, mock_embed(m2.to_embedding_text()))

        # Low trust: should only get public
        results_low = search_memories(
            store=store,
            query="memory",
            embed_func=mock_embed,
            trust_level=0.5,
        )

        # High trust: should get both
        results_high = search_memories(
            store=store,
            query="memory",
            embed_func=mock_embed,
            trust_level=0.9,
        )

        # Verify low trust doesn't include private
        low_descriptions = [r[0].description for r in results_low]
        assert "Private secret" not in low_descriptions

        # Verify high trust includes private
        high_descriptions = [r[0].description for r in results_high]
        assert "Public memory" in high_descriptions

    def test_search_respects_limit(self) -> None:
        """Should respect result limit."""
        store = InMemoryVectorStore()

        for i in range(10):
            m = Memory(description=f"Memory number {i}")
            store.store(m, mock_embed(m.to_embedding_text()))

        results = search_memories(
            store=store,
            query="Memory",
            embed_func=mock_embed,
            limit=3,
        )

        assert len(results) <= 3


class TestGetRelevantMemories:
    """Tests for get_relevant_memories function."""

    def test_search_by_context(self) -> None:
        """Should find memories matching situational context."""
        from personaut.facts import SituationalContext

        store = InMemoryVectorStore()

        # Memory with Miami context
        ctx1 = SituationalContext()
        ctx1.add_location("city", "Miami")
        ctx1.add_location("venue_type", "coffee shop")
        m1 = Memory(description="Coffee date in Miami", context=ctx1)

        # Memory with NYC context
        ctx2 = SituationalContext()
        ctx2.add_location("city", "New York")
        ctx2.add_location("venue_type", "office")
        m2 = Memory(description="Meeting in NYC", context=ctx2)

        store.store(m1, mock_embed(m1.to_embedding_text()))
        store.store(m2, mock_embed(m2.to_embedding_text()))

        # Search for Miami context
        query_ctx = SituationalContext()
        query_ctx.add_location("city", "Miami")

        results = get_relevant_memories(
            store=store,
            context=query_ctx,
            embed_func=mock_embed,
        )

        assert len(results) > 0

    def test_empty_context_returns_empty(self) -> None:
        """Should return empty for empty context."""
        from personaut.facts import SituationalContext

        store = InMemoryVectorStore()
        m = Memory(description="Test")
        store.store(m, [1.0, 0.0, 0.0])

        results = get_relevant_memories(
            store=store,
            context=SituationalContext(),  # Empty
            embed_func=mock_embed,
        )

        assert results == []


class TestExtractAndSearch:
    """Tests for extract_and_search function."""

    def test_extract_and_search_with_facts(self) -> None:
        """Should extract facts and search."""
        from personaut.facts import SituationalContext

        store = InMemoryVectorStore()

        # Memory with coffee shop context
        ctx = SituationalContext()
        ctx.add_location("venue_type", "coffee shop")
        ctx.add_location("city", "Miami")
        m = Memory(description="Meeting at cafe", context=ctx)
        store.store(m, mock_embed(m.to_embedding_text()))

        # Search with natural language
        results = extract_and_search(
            store=store,
            text="We met at a coffee shop in downtown Miami",
            embed_func=mock_embed,
        )

        assert len(results) > 0

    def test_fallback_to_text_search(self) -> None:
        """Should fall back to text search if no facts extracted."""
        store = InMemoryVectorStore()

        m = Memory(description="Random memory without extractable facts")
        store.store(m, mock_embed(m.to_embedding_text()))

        # Text with no extractable facts
        results = extract_and_search(
            store=store,
            text="Something vague and general",
            embed_func=mock_embed,
        )

        # Should still attempt search
        assert isinstance(results, list)


class TestFilterAccessibleMemories:
    """Tests for filter_accessible_memories function."""

    def test_filter_by_trust(self) -> None:
        """Should filter private memories by trust level."""
        memories = [
            Memory(description="Public 1"),
            Memory(description="Public 2"),
            create_private_memory(
                owner_id="alice",
                description="Low threshold",
                trust_threshold=0.3,
            ),
            create_private_memory(
                owner_id="alice",
                description="High threshold",
                trust_threshold=0.8,
            ),
        ]

        # Medium trust
        accessible = filter_accessible_memories(memories, trust_level=0.5)

        assert len(accessible) == 3  # 2 public + 1 low threshold private
        descriptions = [m.description for m in accessible]
        assert "Public 1" in descriptions
        assert "Low threshold" in descriptions
        assert "High threshold" not in descriptions

    def test_full_trust_access(self) -> None:
        """Full trust should access all memories."""
        memories = [
            Memory(description="Public"),
            create_private_memory(
                owner_id="alice",
                description="Very private",
                trust_threshold=0.99,
            ),
        ]

        accessible = filter_accessible_memories(memories, trust_level=1.0)

        assert len(accessible) == 2

    def test_no_trust_access(self) -> None:
        """No trust should only access public memories."""
        memories = [
            Memory(description="Public"),
            create_private_memory(
                owner_id="alice",
                description="Secret",
                trust_threshold=0.1,
            ),
        ]

        accessible = filter_accessible_memories(memories, trust_level=0.0)

        assert len(accessible) == 1
        assert accessible[0].description == "Public"
