"""Integration tests for SQLite vector store.

These tests use a real SQLite database with actual embeddings.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from personaut.memory import (
    Memory,
    IndividualMemory,
    SharedMemory,
    PrivateMemory,
    create_individual_memory,
    create_shared_memory,
    create_private_memory,
    SQLiteVectorStore,
    InMemoryVectorStore,
    search_memories,
)
from personaut.emotions import EmotionalState
from personaut.models import get_embedding, Provider


# Skip if no API key for embeddings
pytestmark = pytest.mark.skipif(
    not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("AWS_ACCESS_KEY_ID")),
    reason="No API credentials available for embeddings",
)


def get_embedding_func():
    """Get an available embedding function."""
    if os.environ.get("GOOGLE_API_KEY"):
        embed = get_embedding(Provider.GEMINI)
    elif os.environ.get("AWS_ACCESS_KEY_ID"):
        embed = get_embedding(Provider.BEDROCK)
    else:
        raise RuntimeError("No API credentials available")

    return embed.embed


class TestSQLiteVectorStore:
    """Tests for SQLite vector store with real embeddings."""

    @pytest.fixture
    def db_path(self) -> str:
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def embed_func(self):
        """Get embedding function."""
        return get_embedding_func()

    def test_store_and_retrieve(self, db_path, embed_func) -> None:
        """Test storing and retrieving memories."""
        store = SQLiteVectorStore(db_path)

        memory = create_individual_memory(
            owner_id="user_123",
            description="Had a great coffee at the new cafe downtown",
        )

        embedding = embed_func(memory.description)
        store.store(memory, embedding)

        # Should be able to search
        results = store.search(embedding, limit=1)

        assert len(results) == 1
        assert results[0][0].description == memory.description

    def test_similarity_search(self, db_path, embed_func) -> None:
        """Test similarity search returns relevant results."""
        store = SQLiteVectorStore(db_path)

        # Store several memories
        memories = [
            "Had a great coffee at the cafe",
            "Enjoyed tea at the coffee shop",
            "Went hiking in the mountains",
            "Read a book about programming",
            "Met Sarah for espresso",
        ]

        for desc in memories:
            memory = create_individual_memory(owner_id="user_123", description=desc)
            embedding = embed_func(desc)
            store.store(memory, embedding)

        # Search for coffee-related memories
        query_embedding = embed_func("coffee and cafes")
        results = store.search(query_embedding, limit=3)

        # Coffee-related memories should rank higher
        descriptions = [r[0].description for r in results]
        coffee_count = sum(1 for d in descriptions if "coffee" in d.lower() or "espresso" in d.lower())
        assert coffee_count >= 2

    def test_owner_filter(self, db_path, embed_func) -> None:
        """Test filtering by owner ID."""
        store = SQLiteVectorStore(db_path)

        # Store memories for different owners
        for owner in ["alice", "bob"]:
            for i in range(3):
                memory = create_individual_memory(
                    owner_id=owner,
                    description=f"{owner}'s memory {i}",
                )
                embedding = embed_func(memory.description)
                store.store(memory, embedding)

        # Search only Alice's memories
        query_embedding = embed_func("memory")
        results = store.search(query_embedding, limit=10, owner_id="alice")

        assert len(results) == 3
        assert all(r[0].owner_id == "alice" for r in results)

    def test_persistence(self, db_path, embed_func) -> None:
        """Test data persists across store instances."""
        # Store in first instance
        store1 = SQLiteVectorStore(db_path)
        memory = create_individual_memory(
            owner_id="persist_test",
            description="This memory should persist",
        )
        embedding = embed_func(memory.description)
        store1.store(memory, embedding)
        store1.close()

        # Retrieve from second instance
        store2 = SQLiteVectorStore(db_path)
        results = store2.search(embedding, limit=1)

        assert len(results) == 1
        assert "persist" in results[0][0].description.lower()
        store2.close()


class TestMemoryWithEmbeddings:
    """Tests for different memory types with real embeddings."""

    @pytest.fixture
    def embed_func(self):
        """Get embedding function."""
        return get_embedding_func()

    @pytest.fixture
    def store(self):
        """Create temporary in-memory store."""
        return InMemoryVectorStore()

    def test_individual_memory_embedding(self, store, embed_func) -> None:
        """Test individual memory with emotional context."""
        emotional_state = EmotionalState()
        emotional_state.change_emotion("happy", 0.8)

        memory = create_individual_memory(
            owner_id="sarah",
            description="Celebrated my birthday with friends at the rooftop bar",
            emotional_state=emotional_state,
        )

        embedding_text = memory.to_embedding_text()
        embedding = embed_func(embedding_text)

        store.store(memory, embedding)

        # Search should find this memory
        query_embedding = embed_func("birthday celebration with friends")
        results = store.search(query_embedding, limit=1)

        assert len(results) == 1
        assert "birthday" in results[0][0].description.lower()

    def test_shared_memory_embedding(self, store, embed_func) -> None:
        """Test shared memory between individuals."""
        memory = create_shared_memory(
            participant_ids=["sarah", "mike"],
            description="Sarah and Mike's road trip to California",
        )

        embedding = embed_func(memory.description)
        store.store(memory, embedding)

        # Both participants should be able to find it
        query_embedding = embed_func("road trip")
        results = store.search(query_embedding, limit=1)

        assert len(results) == 1
        shared_mem = results[0][0]
        assert isinstance(shared_mem, SharedMemory)

    def test_private_memory_trust_gated(self, store, embed_func) -> None:
        """Test private memory requires trust to access."""
        private = create_private_memory(
            owner_id="sarah",
            description="My secret fear of heights",
            required_trust=0.8,
        )

        embedding = embed_func(private.description)
        store.store(private, embedding)

        # Search for it
        query_embedding = embed_func("fear")
        results = store.search(query_embedding, limit=1)

        # Memory is found
        assert len(results) == 1
        mem = results[0][0]
        assert isinstance(mem, PrivateMemory)

        # But access is gated
        assert not mem.can_access(0.5)  # Low trust
        assert mem.can_access(0.9)  # High trust


class TestSearchMemoriesFunction:
    """Tests for the search_memories convenience function."""

    @pytest.fixture
    def embed_func(self):
        """Get embedding function."""
        return get_embedding_func()

    @pytest.fixture
    def populated_store(self, embed_func):
        """Create store with sample memories."""
        store = InMemoryVectorStore()

        memories_data = [
            ("user1", "Coffee with Sarah at the downtown cafe", None),
            ("user1", "Meeting with the team about the project", None),
            ("user1", "Secret about my fear of public speaking", 0.8),
            ("user2", "Hiking trip in the mountains", None),
        ]

        for owner, desc, trust_req in memories_data:
            if trust_req:
                memory = create_private_memory(
                    owner_id=owner,
                    description=desc,
                    required_trust=trust_req,
                )
            else:
                memory = create_individual_memory(
                    owner_id=owner,
                    description=desc,
                )
            embedding = embed_func(desc)
            store.store(memory, embedding)

        return store

    def test_basic_search(self, populated_store, embed_func) -> None:
        """Test basic text search."""
        results = search_memories(
            store=populated_store,
            query="coffee meeting",
            embed_func=embed_func,
            limit=5,
        )

        assert len(results) >= 1
        # Coffee memory should be first or high-ranked
        descriptions = [r[0].description for r in results[:2]]
        assert any("coffee" in d.lower() for d in descriptions)

    def test_owner_filtered_search(self, populated_store, embed_func) -> None:
        """Test search filtered by owner."""
        results = search_memories(
            store=populated_store,
            query="any activity",
            embed_func=embed_func,
            limit=10,
            owner_id="user1",
        )

        assert all(r[0].owner_id == "user1" for r in results)

    def test_trust_gated_search(self, populated_store, embed_func) -> None:
        """Test trust-gated search filters properly."""
        # Low trust - should not see private memory
        results_low = search_memories(
            store=populated_store,
            query="fear public speaking",
            embed_func=embed_func,
            limit=5,
            trust_level=0.5,
        )

        # High trust - should see private memory
        results_high = search_memories(
            store=populated_store,
            query="fear public speaking",
            embed_func=embed_func,
            limit=5,
            trust_level=0.9,
        )

        # Private memory should only appear in high-trust results
        private_in_low = any(
            isinstance(r[0], PrivateMemory) and "fear" in r[0].description
            for r in results_low
        )
        private_in_high = any(
            isinstance(r[0], PrivateMemory) and "fear" in r[0].description
            for r in results_high
        )

        assert not private_in_low
        assert private_in_high
