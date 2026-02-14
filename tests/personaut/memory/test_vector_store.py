"""Tests for VectorStore implementations."""

from __future__ import annotations

from personaut.memory import (
    InMemoryVectorStore,
    Memory,
    create_individual_memory,
)


class TestInMemoryVectorStore:
    """Tests for InMemoryVectorStore."""

    def test_create_empty_store(self) -> None:
        """Should create an empty store."""
        store = InMemoryVectorStore()

        assert store.count() == 0
        assert store.get_all() == []

    def test_store_memory(self) -> None:
        """Should store a memory with embedding."""
        store = InMemoryVectorStore()
        memory = Memory(description="Test memory")
        embedding = [0.1, 0.2, 0.3, 0.4]

        store.store(memory, embedding)

        assert store.count() == 1
        assert memory.embedding == embedding

    def test_store_multiple_memories(self) -> None:
        """Should store multiple memories."""
        store = InMemoryVectorStore()

        for i in range(5):
            memory = Memory(description=f"Memory {i}")
            store.store(memory, [float(i), 0.0, 0.0])

        assert store.count() == 5

    def test_get_by_id(self) -> None:
        """Should retrieve memory by ID."""
        store = InMemoryVectorStore()
        memory = Memory(description="Findable memory")
        store.store(memory, [1.0, 0.0])

        found = store.get(memory.id)

        assert found is not None
        assert found.description == "Findable memory"

    def test_get_not_found(self) -> None:
        """Should return None for unknown ID."""
        store = InMemoryVectorStore()

        assert store.get("nonexistent") is None

    def test_delete_memory(self) -> None:
        """Should delete a memory."""
        store = InMemoryVectorStore()
        memory = Memory(description="Deletable")
        store.store(memory, [1.0, 0.0])

        assert store.count() == 1

        result = store.delete(memory.id)

        assert result is True
        assert store.count() == 0
        assert store.get(memory.id) is None

    def test_delete_not_found(self) -> None:
        """Should return False for unknown ID."""
        store = InMemoryVectorStore()

        assert store.delete("nonexistent") is False

    def test_update_embedding(self) -> None:
        """Should update a memory's embedding."""
        store = InMemoryVectorStore()
        memory = Memory(description="Test")
        store.store(memory, [1.0, 0.0])

        new_embedding = [0.5, 0.5]
        result = store.update_embedding(memory.id, new_embedding)

        assert result is True
        assert memory.embedding == new_embedding

    def test_update_embedding_not_found(self) -> None:
        """Should return False for unknown ID."""
        store = InMemoryVectorStore()

        assert store.update_embedding("nonexistent", [0.0]) is False

    def test_clear(self) -> None:
        """Should clear all memories."""
        store = InMemoryVectorStore()

        for i in range(5):
            store.store(Memory(description=f"M{i}"), [float(i)])

        store.clear()

        assert store.count() == 0

    def test_search_similar(self) -> None:
        """Should find similar memories."""
        store = InMemoryVectorStore()

        # Store memories with different embeddings
        m1 = Memory(description="About cats")
        m2 = Memory(description="About dogs")
        m3 = Memory(description="About fish")

        store.store(m1, [1.0, 0.0, 0.0])  # Cat direction
        store.store(m2, [0.0, 1.0, 0.0])  # Dog direction
        store.store(m3, [0.0, 0.0, 1.0])  # Fish direction

        # Search for cat-like memories
        results = store.search([1.0, 0.1, 0.0], limit=3)

        assert len(results) == 3
        # First result should be most similar (cats)
        assert results[0][0].description == "About cats"
        assert results[0][1] > results[1][1]  # Higher similarity

    def test_search_limit(self) -> None:
        """Should respect limit."""
        store = InMemoryVectorStore()

        for i in range(10):
            store.store(Memory(description=f"M{i}"), [float(i), 0.0])

        results = store.search([5.0, 0.0], limit=3)

        assert len(results) == 3

    def test_search_by_owner(self) -> None:
        """Should filter by owner_id."""
        store = InMemoryVectorStore()

        m1 = create_individual_memory(
            owner_id="alice",
            description="Alice memory",
        )
        m2 = create_individual_memory(
            owner_id="bob",
            description="Bob memory",
        )
        m3 = create_individual_memory(
            owner_id="alice",
            description="Another Alice memory",
        )

        store.store(m1, [1.0, 0.0])
        store.store(m2, [0.0, 1.0])
        store.store(m3, [0.9, 0.1])

        results = store.search([1.0, 0.0], limit=10, owner_id="alice")

        assert len(results) == 2
        assert all(r[0].owner_id == "alice" for r in results)

    def test_count_by_owner(self) -> None:
        """Should count by owner."""
        store = InMemoryVectorStore()

        for i in range(3):
            m = create_individual_memory(
                owner_id="alice",
                description=f"A{i}",
            )
            store.store(m, [float(i)])

        for i in range(2):
            m = create_individual_memory(
                owner_id="bob",
                description=f"B{i}",
            )
            store.store(m, [float(i)])

        assert store.count() == 5
        assert store.count(owner_id="alice") == 3
        assert store.count(owner_id="bob") == 2

    def test_get_all(self) -> None:
        """Should return all memories."""
        store = InMemoryVectorStore()

        memories = []
        for i in range(3):
            m = Memory(description=f"M{i}")
            memories.append(m)
            store.store(m, [float(i)])

        all_memories = store.get_all()

        assert len(all_memories) == 3
        assert {m.id for m in all_memories} == {m.id for m in memories}


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_identical_vectors(self) -> None:
        """Identical vectors should have similarity 1."""
        store = InMemoryVectorStore()
        v = [1.0, 2.0, 3.0]

        similarity = store._cosine_similarity(v, v)

        assert abs(similarity - 1.0) < 0.0001

    def test_orthogonal_vectors(self) -> None:
        """Orthogonal vectors should have similarity 0."""
        store = InMemoryVectorStore()

        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]

        similarity = store._cosine_similarity(v1, v2)

        assert abs(similarity) < 0.0001

    def test_opposite_vectors(self) -> None:
        """Opposite vectors should have similarity -1."""
        store = InMemoryVectorStore()

        v1 = [1.0, 0.0, 0.0]
        v2 = [-1.0, 0.0, 0.0]

        similarity = store._cosine_similarity(v1, v2)

        assert abs(similarity + 1.0) < 0.0001

    def test_different_lengths(self) -> None:
        """Different length vectors should return 0."""
        store = InMemoryVectorStore()

        v1 = [1.0, 2.0]
        v2 = [1.0, 2.0, 3.0]

        similarity = store._cosine_similarity(v1, v2)

        assert similarity == 0.0

    def test_zero_vector(self) -> None:
        """Zero vector should return 0 similarity."""
        store = InMemoryVectorStore()

        v1 = [1.0, 2.0, 3.0]
        v2 = [0.0, 0.0, 0.0]

        similarity = store._cosine_similarity(v1, v2)

        assert similarity == 0.0
