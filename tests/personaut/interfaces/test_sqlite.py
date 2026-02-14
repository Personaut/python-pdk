"""Tests for SQLiteStorage implementation."""

from __future__ import annotations

import pytest

from personaut.interfaces.sqlite import SQLiteStorage


class TestSQLiteStorageInit:
    """Tests for SQLiteStorage initialization."""

    def test_create_in_memory(self) -> None:
        """Verify in-memory database can be created."""
        storage = SQLiteStorage(":memory:")
        assert storage.db_path == ":memory:"
        storage.close()

    def test_connection_created(self) -> None:
        """Verify connection is created on access."""
        storage = SQLiteStorage(":memory:")
        conn = storage.connection
        assert conn is not None
        storage.close()

    def test_context_manager(self) -> None:
        """Verify context manager closes connection."""
        with SQLiteStorage(":memory:") as storage:
            _ = storage.connection
        assert storage._conn is None


class TestSQLiteIndividuals:
    """Tests for individual operations."""

    @pytest.fixture
    def storage(self) -> SQLiteStorage:
        """Create an in-memory storage for testing."""
        return SQLiteStorage(":memory:")

    def test_save_individual_generates_id(self, storage: SQLiteStorage) -> None:
        """Verify saving generates an ID."""
        ind_id = storage.save_individual({"name": "Alice", "individual_type": "simulated"})
        assert ind_id.startswith("ind_")

    def test_save_individual_preserves_id(self, storage: SQLiteStorage) -> None:
        """Verify provided ID is preserved."""
        ind_id = storage.save_individual({"id": "custom_id", "name": "Bob", "individual_type": "human"})
        assert ind_id == "custom_id"

    def test_get_individual_found(self, storage: SQLiteStorage) -> None:
        """Verify retrieving an existing individual."""
        ind_id = storage.save_individual({"name": "Charlie", "individual_type": "simulated"})
        result = storage.get_individual(ind_id)
        assert result is not None
        assert result["name"] == "Charlie"

    def test_get_individual_not_found(self, storage: SQLiteStorage) -> None:
        """Verify None returned for missing individual."""
        result = storage.get_individual("nonexistent")
        assert result is None

    def test_list_individuals_empty(self, storage: SQLiteStorage) -> None:
        """Verify empty list for no individuals."""
        result = storage.list_individuals()
        assert result == []

    def test_list_individuals_with_data(self, storage: SQLiteStorage) -> None:
        """Verify listing returns all individuals."""
        storage.save_individual({"name": "A", "individual_type": "simulated"})
        storage.save_individual({"name": "B", "individual_type": "human"})
        result = storage.list_individuals()
        assert len(result) == 2

    def test_list_individuals_with_filter(self, storage: SQLiteStorage) -> None:
        """Verify filtering by type."""
        storage.save_individual({"name": "A", "individual_type": "simulated"})
        storage.save_individual({"name": "B", "individual_type": "human"})
        result = storage.list_individuals(individual_type="human")
        assert len(result) == 1
        assert result[0]["name"] == "B"

    def test_list_individuals_pagination(self, storage: SQLiteStorage) -> None:
        """Verify pagination works."""
        for i in range(5):
            storage.save_individual({"name": f"Ind{i}", "individual_type": "simulated"})
        result = storage.list_individuals(limit=2, offset=1)
        assert len(result) == 2

    def test_update_individual(self, storage: SQLiteStorage) -> None:
        """Verify updating an individual."""
        ind_id = storage.save_individual({"name": "Old", "individual_type": "simulated"})
        result = storage.update_individual(ind_id, {"name": "New"})
        assert result is not None
        assert result["name"] == "New"

    def test_update_individual_not_found(self, storage: SQLiteStorage) -> None:
        """Verify None returned for missing individual."""
        result = storage.update_individual("nonexistent", {"name": "X"})
        assert result is None

    def test_delete_individual(self, storage: SQLiteStorage) -> None:
        """Verify deleting an individual."""
        ind_id = storage.save_individual({"name": "ToDelete", "individual_type": "simulated"})
        result = storage.delete_individual(ind_id)
        assert result is True
        assert storage.get_individual(ind_id) is None

    def test_delete_individual_not_found(self, storage: SQLiteStorage) -> None:
        """Verify False returned for missing individual."""
        result = storage.delete_individual("nonexistent")
        assert result is False


class TestSQLiteRelationships:
    """Tests for relationship operations."""

    @pytest.fixture
    def storage(self) -> SQLiteStorage:
        """Create storage with test individuals."""
        s = SQLiteStorage(":memory:")
        s.save_individual({"id": "ind_a", "name": "A", "individual_type": "simulated"})
        s.save_individual({"id": "ind_b", "name": "B", "individual_type": "simulated"})
        return s

    def test_save_relationship(self, storage: SQLiteStorage) -> None:
        """Verify saving a relationship."""
        rel_id = storage.save_relationship({"individual_a": "ind_a", "individual_b": "ind_b"})
        assert rel_id.startswith("rel_")

    def test_get_relationship(self, storage: SQLiteStorage) -> None:
        """Verify retrieving a relationship."""
        rel_id = storage.save_relationship(
            {"individual_a": "ind_a", "individual_b": "ind_b", "relationship_type": "friend"}
        )
        result = storage.get_relationship(rel_id)
        assert result is not None
        assert result["relationship_type"] == "friend"

    def test_list_relationships_by_individual(self, storage: SQLiteStorage) -> None:
        """Verify filtering relationships by individual."""
        storage.save_relationship({"individual_a": "ind_a", "individual_b": "ind_b"})
        result = storage.list_relationships(individual_id="ind_a")
        assert len(result) == 1


class TestSQLiteSituations:
    """Tests for situation operations."""

    @pytest.fixture
    def storage(self) -> SQLiteStorage:
        return SQLiteStorage(":memory:")

    def test_save_situation(self, storage: SQLiteStorage) -> None:
        """Verify saving a situation."""
        sit_id = storage.save_situation({"description": "Test situation"})
        assert sit_id.startswith("sit_")

    def test_get_situation(self, storage: SQLiteStorage) -> None:
        """Verify retrieving a situation."""
        sit_id = storage.save_situation({"description": "Coffee shop", "modality": "in_person", "location": "Downtown"})
        result = storage.get_situation(sit_id)
        assert result is not None
        assert result["location"] == "Downtown"


class TestSQLiteSessions:
    """Tests for session operations."""

    @pytest.fixture
    def storage(self) -> SQLiteStorage:
        s = SQLiteStorage(":memory:")
        s.save_individual({"id": "ind_1", "name": "Test", "individual_type": "simulated"})
        return s

    def test_save_session(self, storage: SQLiteStorage) -> None:
        """Verify saving a session."""
        sess_id = storage.save_session({"individual_id": "ind_1"})
        assert sess_id.startswith("sess_")

    def test_get_session(self, storage: SQLiteStorage) -> None:
        """Verify retrieving a session."""
        sess_id = storage.save_session({"individual_id": "ind_1"})
        result = storage.get_session(sess_id)
        assert result is not None
        assert result["active"] is True

    def test_end_session(self, storage: SQLiteStorage) -> None:
        """Verify ending a session."""
        sess_id = storage.save_session({"individual_id": "ind_1"})
        result = storage.end_session(sess_id)
        assert result is True
        session = storage.get_session(sess_id)
        assert session is not None
        assert session["active"] is False

    def test_list_active_sessions(self, storage: SQLiteStorage) -> None:
        """Verify listing active sessions."""
        storage.save_session({"individual_id": "ind_1"})
        sess2 = storage.save_session({"individual_id": "ind_1"})
        storage.end_session(sess2)
        result = storage.list_sessions(active_only=True)
        assert len(result) == 1


class TestSQLiteMessages:
    """Tests for message operations."""

    @pytest.fixture
    def storage(self) -> SQLiteStorage:
        s = SQLiteStorage(":memory:")
        s.save_individual({"id": "ind_1", "name": "Test", "individual_type": "simulated"})
        s.save_session({"id": "sess_1", "individual_id": "ind_1"})
        return s

    def test_save_message(self, storage: SQLiteStorage) -> None:
        """Verify saving a message."""
        msg_id = storage.save_message("sess_1", {"sender": "user", "content": "Hello"})
        assert msg_id.startswith("msg_")

    def test_list_messages(self, storage: SQLiteStorage) -> None:
        """Verify listing messages."""
        storage.save_message("sess_1", {"sender": "user", "content": "Hi"})
        storage.save_message("sess_1", {"sender": "assistant", "content": "Hello!"})
        result = storage.list_messages("sess_1")
        assert len(result) == 2


class TestSQLiteMemories:
    """Tests for memory operations."""

    @pytest.fixture
    def storage(self) -> SQLiteStorage:
        s = SQLiteStorage(":memory:")
        s.save_individual({"id": "ind_1", "name": "Test", "individual_type": "simulated"})
        return s

    def test_save_memory(self, storage: SQLiteStorage) -> None:
        """Verify saving a memory."""
        mem_id = storage.save_memory("ind_1", {"content": "Important event"})
        assert mem_id.startswith("mem_")

    def test_list_memories(self, storage: SQLiteStorage) -> None:
        """Verify listing memories."""
        storage.save_memory("ind_1", {"content": "Event 1", "importance": 0.8})
        storage.save_memory("ind_1", {"content": "Event 2", "importance": 0.5})
        result = storage.list_memories("ind_1")
        assert len(result) == 2
        # Should be sorted by importance
        assert result[0]["importance"] == 0.8

    def test_list_memories_by_type(self, storage: SQLiteStorage) -> None:
        """Verify filtering by memory type."""
        storage.save_memory("ind_1", {"content": "E1", "memory_type": "event"})
        storage.save_memory("ind_1", {"content": "E2", "memory_type": "conversation"})
        result = storage.list_memories("ind_1", memory_type="event")
        assert len(result) == 1

    def test_delete_memory(self, storage: SQLiteStorage) -> None:
        """Verify deleting a memory."""
        mem_id = storage.save_memory("ind_1", {"content": "ToDelete"})
        result = storage.delete_memory(mem_id)
        assert result is True
        memories = storage.list_memories("ind_1")
        assert len(memories) == 0
