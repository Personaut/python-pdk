"""Tests for FileStorage implementation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from personaut.interfaces.file import FileStorage


class TestFileStorageInit:
    """Tests for FileStorage initialization."""

    def test_create_with_temp_dir(self) -> None:
        """Verify storage creates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "test_data"
            storage = FileStorage(data_dir)
            assert data_dir.exists()
            storage.close()

    def test_creates_json_files(self) -> None:
        """Verify JSON files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            assert (Path(tmpdir) / "individuals.json").exists()
            assert (Path(tmpdir) / "relationships.json").exists()
            assert (Path(tmpdir) / "situations.json").exists()
            storage.close()

    def test_context_manager(self) -> None:
        """Verify context manager works."""
        with tempfile.TemporaryDirectory() as tmpdir, FileStorage(tmpdir) as storage:
            storage.save_individual({"name": "Test", "individual_type": "simulated"})


class TestFileStorageIndividuals:
    """Tests for individual operations."""

    @pytest.fixture
    def storage(self) -> FileStorage:
        """Create a temporary storage for testing."""
        tmpdir = tempfile.mkdtemp()
        return FileStorage(tmpdir)

    def test_save_individual_generates_id(self, storage: FileStorage) -> None:
        """Verify saving generates an ID."""
        ind_id = storage.save_individual({"name": "Alice", "individual_type": "simulated"})
        assert ind_id.startswith("ind_")

    def test_save_and_get_individual(self, storage: FileStorage) -> None:
        """Verify roundtrip save and get."""
        ind_id = storage.save_individual({"name": "Bob", "individual_type": "human", "description": "Test person"})
        result = storage.get_individual(ind_id)
        assert result is not None
        assert result["name"] == "Bob"
        assert result["description"] == "Test person"

    def test_get_individual_not_found(self, storage: FileStorage) -> None:
        """Verify None returned for missing individual."""
        result = storage.get_individual("nonexistent")
        assert result is None

    def test_list_individuals(self, storage: FileStorage) -> None:
        """Verify listing individuals."""
        storage.save_individual({"name": "A", "individual_type": "simulated"})
        storage.save_individual({"name": "B", "individual_type": "human"})
        result = storage.list_individuals()
        assert len(result) == 2

    def test_list_individuals_with_filter(self, storage: FileStorage) -> None:
        """Verify filtering individuals."""
        storage.save_individual({"name": "A", "individual_type": "simulated"})
        storage.save_individual({"name": "B", "individual_type": "human"})
        result = storage.list_individuals(individual_type="simulated")
        assert len(result) == 1
        assert result[0]["name"] == "A"

    def test_list_individuals_pagination(self, storage: FileStorage) -> None:
        """Verify pagination."""
        for i in range(5):
            storage.save_individual({"name": f"Ind{i}", "individual_type": "simulated"})
        result = storage.list_individuals(limit=2)
        assert len(result) == 2

    def test_update_individual(self, storage: FileStorage) -> None:
        """Verify updating individual."""
        ind_id = storage.save_individual({"name": "Old", "individual_type": "simulated"})
        result = storage.update_individual(ind_id, {"name": "New"})
        assert result is not None
        assert result["name"] == "New"

    def test_delete_individual(self, storage: FileStorage) -> None:
        """Verify deleting individual."""
        ind_id = storage.save_individual({"name": "ToDelete", "individual_type": "simulated"})
        result = storage.delete_individual(ind_id)
        assert result is True
        assert storage.get_individual(ind_id) is None


class TestFileStorageRelationships:
    """Tests for relationship operations."""

    @pytest.fixture
    def storage(self) -> FileStorage:
        tmpdir = tempfile.mkdtemp()
        s = FileStorage(tmpdir)
        s.save_individual({"id": "ind_a", "name": "A", "individual_type": "simulated"})
        s.save_individual({"id": "ind_b", "name": "B", "individual_type": "simulated"})
        return s

    def test_save_relationship(self, storage: FileStorage) -> None:
        """Verify saving relationship."""
        rel_id = storage.save_relationship({"individual_a": "ind_a", "individual_b": "ind_b"})
        assert rel_id.startswith("rel_")

    def test_get_relationship(self, storage: FileStorage) -> None:
        """Verify getting relationship."""
        rel_id = storage.save_relationship(
            {"individual_a": "ind_a", "individual_b": "ind_b", "relationship_type": "friend"}
        )
        result = storage.get_relationship(rel_id)
        assert result is not None
        assert result["relationship_type"] == "friend"

    def test_list_relationships_by_individual(self, storage: FileStorage) -> None:
        """Verify filtering by individual."""
        storage.save_relationship({"individual_a": "ind_a", "individual_b": "ind_b"})
        result = storage.list_relationships(individual_id="ind_a")
        assert len(result) == 1


class TestFileStorageSituations:
    """Tests for situation operations."""

    @pytest.fixture
    def storage(self) -> FileStorage:
        return FileStorage(tempfile.mkdtemp())

    def test_save_situation(self, storage: FileStorage) -> None:
        """Verify saving situation."""
        sit_id = storage.save_situation({"description": "Test scenario"})
        assert sit_id.startswith("sit_")

    def test_get_situation(self, storage: FileStorage) -> None:
        """Verify getting situation."""
        sit_id = storage.save_situation({"description": "Meeting", "modality": "video_call", "location": "Remote"})
        result = storage.get_situation(sit_id)
        assert result is not None
        assert result["modality"] == "video_call"


class TestFileStorageSessions:
    """Tests for session operations."""

    @pytest.fixture
    def storage(self) -> FileStorage:
        s = FileStorage(tempfile.mkdtemp())
        s.save_individual({"id": "ind_1", "name": "Test", "individual_type": "simulated"})
        return s

    def test_save_session(self, storage: FileStorage) -> None:
        """Verify saving session."""
        sess_id = storage.save_session({"individual_id": "ind_1"})
        assert sess_id.startswith("sess_")

    def test_get_session(self, storage: FileStorage) -> None:
        """Verify getting session."""
        sess_id = storage.save_session({"individual_id": "ind_1"})
        result = storage.get_session(sess_id)
        assert result is not None
        assert result["active"] is True

    def test_end_session(self, storage: FileStorage) -> None:
        """Verify ending session."""
        sess_id = storage.save_session({"individual_id": "ind_1"})
        result = storage.end_session(sess_id)
        assert result is True
        session = storage.get_session(sess_id)
        assert session is not None
        assert session["active"] is False


class TestFileStorageMessages:
    """Tests for message operations."""

    @pytest.fixture
    def storage(self) -> FileStorage:
        s = FileStorage(tempfile.mkdtemp())
        s.save_individual({"id": "ind_1", "name": "Test", "individual_type": "simulated"})
        s.save_session({"id": "sess_1", "individual_id": "ind_1"})
        return s

    def test_save_message(self, storage: FileStorage) -> None:
        """Verify saving message."""
        msg_id = storage.save_message("sess_1", {"sender": "user", "content": "Hello"})
        assert msg_id.startswith("msg_")

    def test_list_messages(self, storage: FileStorage) -> None:
        """Verify listing messages."""
        storage.save_message("sess_1", {"sender": "user", "content": "Hi"})
        storage.save_message("sess_1", {"sender": "assistant", "content": "Hello!"})
        result = storage.list_messages("sess_1")
        assert len(result) == 2


class TestFileStorageMemories:
    """Tests for memory operations."""

    @pytest.fixture
    def storage(self) -> FileStorage:
        s = FileStorage(tempfile.mkdtemp())
        s.save_individual({"id": "ind_1", "name": "Test", "individual_type": "simulated"})
        return s

    def test_save_memory(self, storage: FileStorage) -> None:
        """Verify saving memory."""
        mem_id = storage.save_memory("ind_1", {"content": "Important event"})
        assert mem_id.startswith("mem_")

    def test_list_memories(self, storage: FileStorage) -> None:
        """Verify listing memories."""
        storage.save_memory("ind_1", {"content": "Event 1", "importance": 0.8})
        storage.save_memory("ind_1", {"content": "Event 2", "importance": 0.5})
        result = storage.list_memories("ind_1")
        assert len(result) == 2

    def test_list_memories_by_type(self, storage: FileStorage) -> None:
        """Verify filtering by type."""
        storage.save_memory("ind_1", {"content": "E1", "memory_type": "event"})
        storage.save_memory("ind_1", {"content": "E2", "memory_type": "conversation"})
        result = storage.list_memories("ind_1", memory_type="event")
        assert len(result) == 1

    def test_delete_memory(self, storage: FileStorage) -> None:
        """Verify deleting memory."""
        mem_id = storage.save_memory("ind_1", {"content": "ToDelete"})
        result = storage.delete_memory(mem_id)
        assert result is True
        memories = storage.list_memories("ind_1")
        assert len(memories) == 0


class TestFileStorageClearAll:
    """Tests for clear_all operation."""

    def test_clear_all(self) -> None:
        """Verify clearing all data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            storage.save_individual({"name": "Test", "individual_type": "simulated"})
            storage.clear_all()
            assert storage.list_individuals() == []
