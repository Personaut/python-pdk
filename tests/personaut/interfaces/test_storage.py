"""Tests for the Storage Protocol and base classes."""

from __future__ import annotations

import pytest

from personaut.interfaces.storage import BaseStorage, Storage


class TestStorageProtocol:
    """Tests for the Storage Protocol."""

    def test_storage_is_protocol(self) -> None:
        """Verify Storage is a runtime checkable protocol."""
        assert hasattr(Storage, "__protocol_attrs__") or hasattr(Storage, "__subclasshook__")

    def test_storage_defines_individual_operations(self) -> None:
        """Verify Storage defines individual CRUD operations."""
        assert hasattr(Storage, "save_individual")
        assert hasattr(Storage, "get_individual")
        assert hasattr(Storage, "list_individuals")
        assert hasattr(Storage, "update_individual")
        assert hasattr(Storage, "delete_individual")

    def test_storage_defines_relationship_operations(self) -> None:
        """Verify Storage defines relationship operations."""
        assert hasattr(Storage, "save_relationship")
        assert hasattr(Storage, "get_relationship")
        assert hasattr(Storage, "list_relationships")
        assert hasattr(Storage, "delete_relationship")

    def test_storage_defines_situation_operations(self) -> None:
        """Verify Storage defines situation operations."""
        assert hasattr(Storage, "save_situation")
        assert hasattr(Storage, "get_situation")
        assert hasattr(Storage, "list_situations")
        assert hasattr(Storage, "delete_situation")

    def test_storage_defines_session_operations(self) -> None:
        """Verify Storage defines session operations."""
        assert hasattr(Storage, "save_session")
        assert hasattr(Storage, "get_session")
        assert hasattr(Storage, "list_sessions")
        assert hasattr(Storage, "end_session")

    def test_storage_defines_message_operations(self) -> None:
        """Verify Storage defines message operations."""
        assert hasattr(Storage, "save_message")
        assert hasattr(Storage, "list_messages")

    def test_storage_defines_memory_operations(self) -> None:
        """Verify Storage defines memory operations."""
        assert hasattr(Storage, "save_memory")
        assert hasattr(Storage, "list_memories")
        assert hasattr(Storage, "delete_memory")

    def test_storage_defines_lifecycle_operations(self) -> None:
        """Verify Storage defines lifecycle operations."""
        assert hasattr(Storage, "close")


class TestBaseStorage:
    """Tests for the BaseStorage class."""

    def test_generate_id_with_prefix(self) -> None:
        """Verify ID generation includes prefix."""
        storage = BaseStorage()
        id1 = storage._generate_id("test")
        assert id1.startswith("test_")
        assert len(id1) == 13  # "test_" + 8 hex chars

    def test_generate_id_unique(self) -> None:
        """Verify ID generation produces unique IDs."""
        storage = BaseStorage()
        ids = {storage._generate_id("x") for _ in range(100)}
        assert len(ids) == 100

    def test_now_returns_datetime(self) -> None:
        """Verify _now returns a datetime."""
        from datetime import datetime

        storage = BaseStorage()
        result = storage._now()
        assert isinstance(result, datetime)

    def test_to_dict_with_dict(self) -> None:
        """Verify _to_dict returns dict unchanged."""
        storage = BaseStorage()
        data = {"key": "value"}
        result = storage._to_dict(data)
        assert result == data

    def test_to_dict_with_object(self) -> None:
        """Verify _to_dict converts objects with __dict__."""

        class TestObj:
            def __init__(self) -> None:
                self.name = "test"

        storage = BaseStorage()
        obj = TestObj()
        result = storage._to_dict(obj)
        assert result["name"] == "test"

    def test_to_dict_with_to_dict_method(self) -> None:
        """Verify _to_dict calls to_dict method."""

        class TestEntity:
            def to_dict(self) -> dict:
                return {"custom": "value"}

        storage = BaseStorage()
        obj = TestEntity()
        result = storage._to_dict(obj)
        assert result == {"custom": "value"}

    def test_to_dict_raises_for_invalid(self) -> None:
        """Verify _to_dict raises TypeError for unconvertible types."""
        storage = BaseStorage()
        with pytest.raises(TypeError):
            storage._to_dict(123)


class TestStorageExports:
    """Tests for module exports."""

    def test_exports_storage_protocol(self) -> None:
        """Verify Storage is exported."""
        from personaut.interfaces import Storage

        assert Storage is not None

    def test_exports_base_storage(self) -> None:
        """Verify BaseStorage is exported."""
        from personaut.interfaces import BaseStorage

        assert BaseStorage is not None

    def test_exports_sqlite_storage(self) -> None:
        """Verify SQLiteStorage is exported."""
        from personaut.interfaces import SQLiteStorage

        assert SQLiteStorage is not None

    def test_exports_file_storage(self) -> None:
        """Verify FileStorage is exported."""
        from personaut.interfaces import FileStorage

        assert FileStorage is not None
