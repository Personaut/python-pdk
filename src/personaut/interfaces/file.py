"""File-based JSON storage implementation for Personaut PDK.

This module provides a file-based storage backend using JSON files for
persisting individuals, relationships, situations, sessions, and memories.

Example:
    >>> from personaut.interfaces.file import FileStorage
    >>> storage = FileStorage("./data")
    >>> storage.save_individual({"name": "Alice", "individual_type": "simulated"})
    'ind_a1b2c3d4'
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from personaut.interfaces.storage import BaseStorage


class FileStorage(BaseStorage):
    """File-based JSON storage implementation.

    Stores each entity type in a separate JSON file within a data directory.
    Suitable for development, small-scale use, and human-readable data inspection.

    Directory structure:
        data_dir/
            individuals.json
            relationships.json
            situations.json
            sessions.json
            messages.json
            memories.json

    Attributes:
        data_dir: Path to the storage directory.
    """

    def __init__(
        self,
        data_dir: str | Path = "./personaut_data",
        *,
        create_dir: bool = True,
    ) -> None:
        """Initialize file storage.

        Args:
            data_dir: Directory path for storing JSON files.
            create_dir: Whether to create the directory if it doesn't exist.
        """
        self.data_dir = Path(data_dir)

        if create_dir:
            self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize data files
        self._files = {
            "individuals": self.data_dir / "individuals.json",
            "relationships": self.data_dir / "relationships.json",
            "situations": self.data_dir / "situations.json",
            "sessions": self.data_dir / "sessions.json",
            "messages": self.data_dir / "messages.json",
            "memories": self.data_dir / "memories.json",
        }

        # Initialize empty files if they don't exist
        for file_path in self._files.values():
            if not file_path.exists():
                self._write_file(file_path, {})

    def _read_file(self, path: Path) -> dict[str, Any]:
        """Read and parse a JSON file."""
        try:
            with open(path, encoding="utf-8") as f:
                result: dict[str, Any] = json.load(f)
                return result
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_file(self, path: Path, data: dict[str, Any]) -> None:
        """Write data to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _load(self, entity_type: str) -> dict[str, Any]:
        """Load all entities of a type."""
        return self._read_file(self._files[entity_type])

    def _save(self, entity_type: str, data: dict[str, Any]) -> None:
        """Save all entities of a type."""
        self._write_file(self._files[entity_type], data)

    # ========================
    # Individual Operations
    # ========================

    def save_individual(self, individual: dict[str, Any]) -> str:
        """Save an individual to storage."""
        ind_id = individual.get("id") or self._generate_id("ind")
        now = self._now().isoformat()

        data = self._load("individuals")

        entity = individual.copy()
        entity["id"] = ind_id
        entity.setdefault("created_at", now)
        entity["updated_at"] = now

        data[ind_id] = entity
        self._save("individuals", data)

        return ind_id

    def get_individual(self, individual_id: str) -> dict[str, Any] | None:
        """Retrieve an individual by ID."""
        data = self._load("individuals")
        return data.get(individual_id)

    def list_individuals(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """List individuals with optional filtering."""
        data = self._load("individuals")
        items = list(data.values())

        # Apply filters
        for key, value in filters.items():
            items = [i for i in items if i.get(key) == value]

        # Sort by created_at descending
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Apply pagination
        return items[offset : offset + limit]

    def update_individual(
        self,
        individual_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update an existing individual."""
        data = self._load("individuals")

        if individual_id not in data:
            return None

        data[individual_id].update(updates)
        data[individual_id]["updated_at"] = self._now().isoformat()

        self._save("individuals", data)
        result: dict[str, Any] = data[individual_id]
        return result

    def delete_individual(self, individual_id: str) -> bool:
        """Delete an individual."""
        data = self._load("individuals")

        if individual_id not in data:
            return False

        del data[individual_id]
        self._save("individuals", data)
        return True

    # ========================
    # Relationship Operations
    # ========================

    def save_relationship(self, relationship: dict[str, Any]) -> str:
        """Save a relationship to storage."""
        rel_id = relationship.get("id") or self._generate_id("rel")
        now = self._now().isoformat()

        data = self._load("relationships")

        entity = relationship.copy()
        entity["id"] = rel_id
        entity.setdefault("created_at", now)
        entity["updated_at"] = now

        data[rel_id] = entity
        self._save("relationships", data)

        return rel_id

    def get_relationship(self, relationship_id: str) -> dict[str, Any] | None:
        """Retrieve a relationship by ID."""
        data = self._load("relationships")
        return data.get(relationship_id)

    def list_relationships(
        self,
        individual_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List relationships."""
        data = self._load("relationships")
        items = list(data.values())

        if individual_id:
            items = [
                r for r in items if r.get("individual_a") == individual_id or r.get("individual_b") == individual_id
            ]

        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items[offset : offset + limit]

    def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        data = self._load("relationships")

        if relationship_id not in data:
            return False

        del data[relationship_id]
        self._save("relationships", data)
        return True

    # ========================
    # Situation Operations
    # ========================

    def save_situation(self, situation: dict[str, Any]) -> str:
        """Save a situation to storage."""
        sit_id = situation.get("id") or self._generate_id("sit")
        now = self._now().isoformat()

        data = self._load("situations")

        entity = situation.copy()
        entity["id"] = sit_id
        entity.setdefault("created_at", now)
        entity["updated_at"] = now

        data[sit_id] = entity
        self._save("situations", data)

        return sit_id

    def get_situation(self, situation_id: str) -> dict[str, Any] | None:
        """Retrieve a situation by ID."""
        data = self._load("situations")
        return data.get(situation_id)

    def list_situations(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List situations."""
        data = self._load("situations")
        items = list(data.values())
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items[offset : offset + limit]

    def delete_situation(self, situation_id: str) -> bool:
        """Delete a situation."""
        data = self._load("situations")

        if situation_id not in data:
            return False

        del data[situation_id]
        self._save("situations", data)
        return True

    # ========================
    # Session Operations
    # ========================

    def save_session(self, session: dict[str, Any]) -> str:
        """Save a session to storage."""
        sess_id = session.get("id") or self._generate_id("sess")
        now = self._now().isoformat()

        data = self._load("sessions")

        entity = session.copy()
        entity["id"] = sess_id
        entity.setdefault("active", True)
        entity.setdefault("created_at", now)

        data[sess_id] = entity
        self._save("sessions", data)

        return sess_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve a session by ID."""
        data = self._load("sessions")
        return data.get(session_id)

    def list_sessions(
        self,
        individual_id: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List sessions."""
        data = self._load("sessions")
        items = list(data.values())

        if individual_id:
            items = [s for s in items if s.get("individual_id") == individual_id]

        if active_only:
            items = [s for s in items if s.get("active", True)]

        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items[offset : offset + limit]

    def end_session(self, session_id: str) -> bool:
        """Mark a session as ended."""
        data = self._load("sessions")

        if session_id not in data:
            return False

        data[session_id]["active"] = False
        data[session_id]["ended_at"] = self._now().isoformat()

        self._save("sessions", data)
        return True

    # ========================
    # Message Operations
    # ========================

    def save_message(
        self,
        session_id: str,
        message: dict[str, Any],
    ) -> str:
        """Save a message to a session."""
        msg_id = message.get("id") or self._generate_id("msg")
        now = self._now().isoformat()

        data = self._load("messages")

        # Initialize session message list if needed
        if session_id not in data:
            data[session_id] = []

        entity = message.copy()
        entity["id"] = msg_id
        entity["session_id"] = session_id
        entity.setdefault("created_at", now)

        data[session_id].append(entity)
        self._save("messages", data)

        return msg_id

    def list_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List messages for a session."""
        data = self._load("messages")
        messages: list[dict[str, Any]] = data.get(session_id, [])

        # Sort by created_at ascending (oldest first)
        messages.sort(key=lambda x: x.get("created_at", ""))

        return list(messages[offset : offset + limit])

    # ========================
    # Memory Operations
    # ========================

    def save_memory(
        self,
        individual_id: str,
        memory: dict[str, Any],
    ) -> str:
        """Save a memory for an individual."""
        mem_id = memory.get("id") or self._generate_id("mem")
        now = self._now().isoformat()

        data = self._load("memories")

        # Initialize individual memory list if needed
        if individual_id not in data:
            data[individual_id] = []

        entity = memory.copy()
        entity["id"] = mem_id
        entity["individual_id"] = individual_id
        entity.setdefault("memory_type", "general")
        entity.setdefault("importance", 0.5)
        entity.setdefault("created_at", now)

        data[individual_id].append(entity)
        self._save("memories", data)

        return mem_id

    def list_memories(
        self,
        individual_id: str,
        memory_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List memories for an individual."""
        data = self._load("memories")
        memories: list[dict[str, Any]] = data.get(individual_id, [])

        if memory_type:
            memories = [m for m in memories if m.get("memory_type") == memory_type]

        # Sort by importance (high first), then by created_at (newest first)
        memories.sort(
            key=lambda x: (-x.get("importance", 0.5), x.get("created_at", "")),
        )

        return list(memories[offset : offset + limit])

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        data = self._load("memories")

        for individual_id, memories in data.items():
            for i, memory in enumerate(memories):
                if memory.get("id") == memory_id:
                    del data[individual_id][i]
                    self._save("memories", data)
                    return True

        return False

    # ========================
    # Lifecycle Operations
    # ========================

    def close(self) -> None:
        """Close storage (no-op for file storage)."""
        pass

    def clear_all(self) -> None:
        """Clear all stored data. Use with caution!"""
        for file_path in self._files.values():
            self._write_file(file_path, {})

    def __enter__(self) -> FileStorage:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


__all__ = ["FileStorage"]
