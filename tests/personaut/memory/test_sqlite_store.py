"""Extended tests for SQLiteVectorStore — targeting uncovered lines."""

from __future__ import annotations

from pathlib import Path

import pytest

from personaut.memory.individual import IndividualMemory
from personaut.memory.private import PrivateMemory
from personaut.memory.shared import SharedMemory
from personaut.memory.sqlite_store import SQLiteVectorStore


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Provide a temp database path."""
    return str(tmp_path / "test_store.db")


@pytest.fixture
def store(db_path: str) -> SQLiteVectorStore:
    """Create a fresh store for testing."""
    s = SQLiteVectorStore(db_path, dimensions=4)
    yield s
    s.close()


def _embedding(vals: list[float] | None = None) -> list[float]:
    """Create a small test embedding."""
    return vals or [0.1, 0.2, 0.3, 0.4]


def _individual_memory(
    owner_id: str = "owner_1",
    description: str = "Test memory",
    salience: float = 0.5,
) -> IndividualMemory:
    """Create a test individual memory."""
    return IndividualMemory(
        owner_id=owner_id,
        description=description,
        salience=salience,
    )


class TestSQLiteVectorStoreBasics:
    """Basic store operations."""

    def test_create_store(self, db_path: str) -> None:
        """Store should be created and tables initialized."""
        store = SQLiteVectorStore(db_path, dimensions=4)
        assert store.db_path == Path(db_path)
        assert store.dimensions == 4
        store.close()

    def test_auto_create_parent_dirs(self, tmp_path: Path) -> None:
        """Store should create parent directories if needed."""
        nested = tmp_path / "deep" / "nested" / "test.db"
        store = SQLiteVectorStore(str(nested), dimensions=4)
        assert nested.parent.exists()
        store.close()

    def test_context_manager(self, db_path: str) -> None:
        """Store should work as context manager."""
        with SQLiteVectorStore(db_path, dimensions=4) as store:
            mem = _individual_memory()
            store.store(mem, _embedding())
            assert store.count() == 1
        # After exiting, connection should be closed
        assert store._conn is None

    def test_close_idempotent(self, store: SQLiteVectorStore) -> None:
        """Closing multiple times should be safe."""
        store.close()
        store.close()  # Should not raise

    def test_auto_create_false(self, tmp_path: Path) -> None:
        """Store with auto_create=False should not create tables."""
        path = str(tmp_path / "no_auto.db")
        store = SQLiteVectorStore(path, dimensions=4, auto_create=False)
        # Connection not established yet, so no tables
        assert store._conn is None
        store.close()


class TestSQLiteVectorStoreStore:
    """Tests for the store() method."""

    def test_store_individual_memory(self, store: SQLiteVectorStore) -> None:
        """Should store an individual memory."""
        mem = _individual_memory()
        store.store(mem, _embedding())
        assert store.count() == 1

    def test_store_sets_embedding_on_memory(self, store: SQLiteVectorStore) -> None:
        """store() should set the embedding attribute on the memory object."""
        mem = _individual_memory()
        emb = _embedding()
        store.store(mem, emb)
        assert mem.embedding == emb

    def test_store_shared_memory(self, store: SQLiteVectorStore) -> None:
        """Should store a shared memory."""
        mem = SharedMemory(
            participant_ids=["p1", "p2"],
            description="Shared experience",
        )
        store.store(mem, _embedding())
        assert store.count() == 1

    def test_store_private_memory(self, store: SQLiteVectorStore) -> None:
        """Should store a private memory."""
        mem = PrivateMemory(
            owner_id="owner_1",
            description="Secret memory",
            trust_threshold=0.8,
        )
        store.store(mem, _embedding())
        assert store.count() == 1

    def test_store_replaces_existing(self, store: SQLiteVectorStore) -> None:
        """Storing a memory with same ID should replace it."""
        mem1 = _individual_memory(description="Version 1")
        store.store(mem1, _embedding())

        mem2 = IndividualMemory(
            id=mem1.id,
            owner_id="owner_1",
            description="Version 2",
        )
        store.store(mem2, _embedding())

        assert store.count() == 1
        retrieved = store.get(mem1.id)
        assert retrieved is not None
        assert retrieved.description == "Version 2"

    def test_store_multiple_memories(self, store: SQLiteVectorStore) -> None:
        """Should store multiple memories."""
        for i in range(5):
            mem = _individual_memory(description=f"Memory {i}")
            store.store(mem, _embedding())
        assert store.count() == 5


class TestSQLiteVectorStoreGet:
    """Tests for the get() method."""

    def test_get_existing(self, store: SQLiteVectorStore) -> None:
        """Should retrieve a stored memory by ID."""
        mem = _individual_memory(description="Findable")
        store.store(mem, _embedding())

        result = store.get(mem.id)
        assert result is not None
        assert result.description == "Findable"

    def test_get_nonexistent(self, store: SQLiteVectorStore) -> None:
        """Should return None for non-existent ID."""
        result = store.get("nonexistent_id")
        assert result is None

    def test_get_preserves_type(self, store: SQLiteVectorStore) -> None:
        """Retrieved memory should be the correct subclass."""
        mem = _individual_memory()
        store.store(mem, _embedding())
        result = store.get(mem.id)
        assert isinstance(result, IndividualMemory)


class TestSQLiteVectorStoreDelete:
    """Tests for the delete() method."""

    def test_delete_existing(self, store: SQLiteVectorStore) -> None:
        """Should delete an existing memory and return True."""
        mem = _individual_memory()
        store.store(mem, _embedding())
        assert store.delete(mem.id) is True
        assert store.count() == 0

    def test_delete_nonexistent(self, store: SQLiteVectorStore) -> None:
        """Should return False for non-existent ID."""
        assert store.delete("nonexistent") is False


class TestSQLiteVectorStoreUpdateEmbedding:
    """Tests for update_embedding() method."""

    def test_update_existing(self, store: SQLiteVectorStore) -> None:
        """Should update the embedding and return True."""
        mem = _individual_memory()
        store.store(mem, _embedding())

        new_emb = [0.5, 0.6, 0.7, 0.8]
        assert store.update_embedding(mem.id, new_emb) is True

    def test_update_nonexistent(self, store: SQLiteVectorStore) -> None:
        """Should return False for non-existent ID."""
        assert store.update_embedding("nonexistent", [0.1, 0.2, 0.3, 0.4]) is False


class TestSQLiteVectorStoreCount:
    """Tests for count() method."""

    def test_count_empty(self, store: SQLiteVectorStore) -> None:
        """Empty store should have count 0."""
        assert store.count() == 0

    def test_count_total(self, store: SQLiteVectorStore) -> None:
        """count() without owner_id should count all."""
        store.store(_individual_memory(owner_id="a"), _embedding())
        store.store(_individual_memory(owner_id="b"), _embedding())
        assert store.count() == 2

    def test_count_by_owner(self, store: SQLiteVectorStore) -> None:
        """count() with owner_id should filter."""
        store.store(_individual_memory(owner_id="a"), _embedding())
        store.store(_individual_memory(owner_id="a"), _embedding())
        store.store(_individual_memory(owner_id="b"), _embedding())
        assert store.count(owner_id="a") == 2
        assert store.count(owner_id="b") == 1
        assert store.count(owner_id="c") == 0


class TestSQLiteVectorStoreGetByOwner:
    """Tests for get_by_owner() method."""

    def test_get_by_owner_returns_owned(self, store: SQLiteVectorStore) -> None:
        """Should return only memories for the given owner."""
        store.store(_individual_memory(owner_id="a", description="A1"), _embedding())
        store.store(_individual_memory(owner_id="a", description="A2"), _embedding())
        store.store(_individual_memory(owner_id="b", description="B1"), _embedding())

        results = store.get_by_owner("a")
        assert len(results) == 2
        descriptions = {m.description for m in results}
        assert "A1" in descriptions
        assert "A2" in descriptions

    def test_get_by_owner_empty(self, store: SQLiteVectorStore) -> None:
        """Should return empty list for nonexistent owner."""
        results = store.get_by_owner("nonexistent")
        assert results == []

    def test_get_by_owner_limit(self, store: SQLiteVectorStore) -> None:
        """Should respect the limit parameter."""
        for i in range(5):
            store.store(
                _individual_memory(owner_id="a", description=f"Mem {i}"),
                _embedding(),
            )
        results = store.get_by_owner("a", limit=3)
        assert len(results) == 3


class TestSQLiteVectorStoreSearch:
    """Tests for search() and _brute_force_search()."""

    def test_search_empty_store(self, store: SQLiteVectorStore) -> None:
        """Searching empty store should return empty list."""
        results = store.search(_embedding())
        assert results == []

    def test_search_finds_similar(self, store: SQLiteVectorStore) -> None:
        """Search should find similar memories."""
        mem1 = _individual_memory(description="Close match")
        store.store(mem1, [1.0, 0.0, 0.0, 0.0])

        mem2 = _individual_memory(description="Far match")
        store.store(mem2, [0.0, 0.0, 0.0, 1.0])

        results = store.search([1.0, 0.0, 0.0, 0.0], limit=10)
        assert len(results) == 2
        # First result should be the close match (highest similarity)
        assert results[0][0].description == "Close match"
        # Similarity scores should be floats
        assert isinstance(results[0][1], float)

    def test_search_with_owner_filter(self, store: SQLiteVectorStore) -> None:
        """Search with owner_id should filter results."""
        store.store(
            _individual_memory(owner_id="a", description="A's memory"),
            [1.0, 0.0, 0.0, 0.0],
        )
        store.store(
            _individual_memory(owner_id="b", description="B's memory"),
            [1.0, 0.0, 0.0, 0.0],
        )

        results = store.search([1.0, 0.0, 0.0, 0.0], owner_id="a")
        assert len(results) == 1
        assert results[0][0].description == "A's memory"

    def test_search_limit(self, store: SQLiteVectorStore) -> None:
        """Search should respect limit parameter."""
        for i in range(5):
            store.store(_individual_memory(description=f"Mem {i}"), _embedding())
        results = store.search(_embedding(), limit=2)
        assert len(results) == 2

    def test_search_skips_null_embeddings(self, store: SQLiteVectorStore) -> None:
        """Brute force search should skip memories with null embeddings."""
        # Store a memory then manually null its embedding
        mem = _individual_memory()
        store.store(mem, _embedding())

        conn = store._get_connection()
        conn.execute(
            "UPDATE memories SET embedding_blob = NULL WHERE id = ?",
            (mem.id,),
        )
        conn.commit()

        results = store.search(_embedding())
        assert len(results) == 0


class TestSQLiteVectorStoreMemoryFromDict:
    """Tests for _memory_from_dict static method."""

    def test_individual_type(self) -> None:
        """Should create IndividualMemory for 'individual' type."""
        data = {
            "memory_type": "individual",
            "description": "Test",
            "owner_id": "o1",
        }
        result = SQLiteVectorStore._memory_from_dict(data)
        assert isinstance(result, IndividualMemory)

    def test_shared_type(self) -> None:
        """Should create SharedMemory for 'shared' type."""
        data = {
            "memory_type": "shared",
            "description": "Test",
            "participant_ids": ["p1", "p2"],
        }
        result = SQLiteVectorStore._memory_from_dict(data)
        assert isinstance(result, SharedMemory)

    def test_private_type(self) -> None:
        """Should create PrivateMemory for 'private' type."""
        data = {
            "memory_type": "private",
            "description": "Test",
            "owner_id": "o1",
            "trust_threshold": 0.8,
        }
        result = SQLiteVectorStore._memory_from_dict(data)
        assert isinstance(result, PrivateMemory)

    def test_missing_type_defaults_to_individual(self) -> None:
        """Missing memory_type should default to individual."""
        data = {
            "description": "Test",
            "owner_id": "o1",
        }
        result = SQLiteVectorStore._memory_from_dict(data)
        assert isinstance(result, IndividualMemory)


class TestSQLiteVectorStoreCosineSimilarity:
    """Tests for _cosine_similarity static method."""

    def test_identical_vectors(self) -> None:
        """Identical vectors should have similarity 1.0."""
        a = [1.0, 0.0, 0.0]
        assert SQLiteVectorStore._cosine_similarity(a, a) == pytest.approx(1.0)

    def test_orthogonal_vectors(self) -> None:
        """Orthogonal vectors should have similarity 0.0."""
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert SQLiteVectorStore._cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self) -> None:
        """Opposite vectors should have similarity -1.0."""
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        assert SQLiteVectorStore._cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector(self) -> None:
        """Zero vector should return 0."""
        a = [0.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert SQLiteVectorStore._cosine_similarity(a, b) == 0.0

    def test_different_lengths(self) -> None:
        """Different length vectors should return 0."""
        a = [1.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert SQLiteVectorStore._cosine_similarity(a, b) == 0.0
