"""SQLite storage implementation for Personaut PDK.

This module provides a SQLite-based storage backend for persisting
individuals, relationships, situations, sessions, and memories.

Example:
    >>> from personaut.interfaces.sqlite import SQLiteStorage
    >>> storage = SQLiteStorage("personaut.db")
    >>> storage.save_individual({"name": "Alice", "individual_type": "simulated"})
    'ind_a1b2c3d4'
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from personaut.interfaces.storage import BaseStorage


class SQLiteStorage(BaseStorage):
    """SQLite-based storage implementation.

    Provides persistent storage for all Personaut entities using SQLite.
    Supports automatic schema creation and migrations.

    Attributes:
        db_path: Path to the SQLite database file.
    """

    SCHEMA_VERSION = 1

    def __init__(
        self,
        db_path: str | Path = "personaut.db",
        *,
        create_tables: bool = True,
    ) -> None:
        """Initialize SQLite storage.

        Args:
            db_path: Path to the database file. Use ":memory:" for in-memory DB.
            create_tables: Whether to create tables if they don't exist.
        """
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

        if create_tables:
            self._create_schema()

    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create database connection.

        Uses ``check_same_thread=False`` because the LiveInteractionServer
        runs both the FastAPI and Flask servers in a single process.  All
        DB-mutating writes are routed through the FastAPI thread, but
        occasional reads may come from the Flask thread (e.g. hydration).
        """
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    @contextmanager
    def _transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager for database transactions."""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def _create_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        with self._transaction() as cursor:
            # Schema version tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)

            # Individuals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS individuals (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    individual_type TEXT NOT NULL DEFAULT 'simulated',
                    description TEXT,
                    trait_profile TEXT,  -- JSON
                    emotional_state TEXT,  -- JSON
                    triggers TEXT,  -- JSON
                    masks TEXT,  -- JSON
                    metadata TEXT,  -- JSON
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)

            # Relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    individual_a TEXT NOT NULL,
                    individual_b TEXT NOT NULL,
                    relationship_type TEXT,
                    trust_levels TEXT,  -- JSON
                    shared_memories TEXT,  -- JSON
                    metadata TEXT,  -- JSON
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (individual_a) REFERENCES individuals(id),
                    FOREIGN KEY (individual_b) REFERENCES individuals(id)
                )
            """)

            # Situations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS situations (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    modality TEXT DEFAULT 'text_message',
                    location TEXT,
                    context TEXT,  -- JSON
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    individual_id TEXT NOT NULL,
                    situation_id TEXT,
                    active INTEGER DEFAULT 1,
                    metadata TEXT,  -- JSON
                    created_at TEXT NOT NULL,
                    ended_at TEXT,
                    FOREIGN KEY (individual_id) REFERENCES individuals(id),
                    FOREIGN KEY (situation_id) REFERENCES situations(id)
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,  -- JSON
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)

            # Memories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    individual_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    memory_type TEXT DEFAULT 'general',
                    importance REAL DEFAULT 0.5,
                    embedding TEXT,  -- JSON array
                    metadata TEXT,  -- JSON
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (individual_id) REFERENCES individuals(id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationships_individual_a
                ON relationships(individual_a)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationships_individual_b
                ON relationships(individual_b)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_individual
                ON sessions(individual_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_individual
                ON memories(individual_id)
            """)

            # Set schema version
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (self.SCHEMA_VERSION,),
            )

    def _row_to_dict(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        """Convert a database row to a dictionary."""
        if row is None:
            return None

        result = dict(row)

        # Parse JSON fields
        json_fields = [
            "trait_profile",
            "emotional_state",
            "triggers",
            "masks",
            "trust_levels",
            "shared_memories",
            "context",
            "metadata",
            "embedding",
        ]
        for field in json_fields:
            if field in result and result[field] is not None:
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    pass

        return result

    def _prepare_json_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert dict/list fields to JSON strings for storage."""
        result = data.copy()
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                result[key] = json.dumps(value)
        return result

    # ========================
    # Individual Operations
    # ========================

    def save_individual(self, individual: dict[str, Any]) -> str:
        """Save an individual to the database."""
        ind_id = individual.get("id") or self._generate_id("ind")
        now = self._now().isoformat()

        data = self._prepare_json_fields(individual)

        with self._transaction() as cursor:
            cursor.execute(
                """
                INSERT OR REPLACE INTO individuals
                (id, name, individual_type, description, trait_profile,
                 emotional_state, triggers, masks, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ind_id,
                    data.get("name", "Unknown"),
                    data.get("individual_type", "simulated"),
                    data.get("description"),
                    data.get("trait_profile"),
                    data.get("emotional_state"),
                    data.get("triggers"),
                    data.get("masks"),
                    data.get("metadata"),
                    data.get("created_at", now),
                    now,
                ),
            )

        return ind_id

    def get_individual(self, individual_id: str) -> dict[str, Any] | None:
        """Retrieve an individual by ID."""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT * FROM individuals WHERE id = ?",
                (individual_id,),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row)

    def list_individuals(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """List individuals with optional filtering."""
        query = "SELECT * FROM individuals"
        params: list[Any] = []

        if filters:
            conditions = []
            for key, value in filters.items():
                if key in ("name", "individual_type"):
                    conditions.append(f"{key} = ?")
                    params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._transaction() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [r for r in (self._row_to_dict(row) for row in rows) if r is not None]

    def update_individual(
        self,
        individual_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update an existing individual."""
        existing = self.get_individual(individual_id)
        if not existing:
            return None

        # Merge updates
        existing.update(updates)
        existing["updated_at"] = self._now().isoformat()

        self.save_individual(existing)
        return self.get_individual(individual_id)

    def delete_individual(self, individual_id: str) -> bool:
        """Delete an individual."""
        with self._transaction() as cursor:
            cursor.execute(
                "DELETE FROM individuals WHERE id = ?",
                (individual_id,),
            )
            return cursor.rowcount > 0

    # ========================
    # Relationship Operations
    # ========================

    def save_relationship(self, relationship: dict[str, Any]) -> str:
        """Save a relationship to the database."""
        rel_id = relationship.get("id") or self._generate_id("rel")
        now = self._now().isoformat()

        data = self._prepare_json_fields(relationship)

        with self._transaction() as cursor:
            cursor.execute(
                """
                INSERT OR REPLACE INTO relationships
                (id, individual_a, individual_b, relationship_type,
                 trust_levels, shared_memories, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rel_id,
                    data.get("individual_a"),
                    data.get("individual_b"),
                    data.get("relationship_type"),
                    data.get("trust_levels"),
                    data.get("shared_memories"),
                    data.get("metadata"),
                    data.get("created_at", now),
                    now,
                ),
            )

        return rel_id

    def get_relationship(self, relationship_id: str) -> dict[str, Any] | None:
        """Retrieve a relationship by ID."""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT * FROM relationships WHERE id = ?",
                (relationship_id,),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row)

    def list_relationships(
        self,
        individual_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List relationships."""
        query = "SELECT * FROM relationships"
        params: list[Any] = []

        if individual_id:
            query += " WHERE individual_a = ? OR individual_b = ?"
            params.extend([individual_id, individual_id])

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._transaction() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [r for r in (self._row_to_dict(row) for row in rows) if r is not None]

    def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        with self._transaction() as cursor:
            cursor.execute(
                "DELETE FROM relationships WHERE id = ?",
                (relationship_id,),
            )
            return cursor.rowcount > 0

    # ========================
    # Situation Operations
    # ========================

    def save_situation(self, situation: dict[str, Any]) -> str:
        """Save a situation to the database."""
        sit_id = situation.get("id") or self._generate_id("sit")
        now = self._now().isoformat()

        data = self._prepare_json_fields(situation)

        with self._transaction() as cursor:
            cursor.execute(
                """
                INSERT OR REPLACE INTO situations
                (id, description, modality, location, context, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sit_id,
                    data.get("description", ""),
                    data.get("modality", "text_message"),
                    data.get("location"),
                    data.get("context"),
                    data.get("created_at", now),
                    now,
                ),
            )

        return sit_id

    def get_situation(self, situation_id: str) -> dict[str, Any] | None:
        """Retrieve a situation by ID."""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT * FROM situations WHERE id = ?",
                (situation_id,),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row)

    def list_situations(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List situations."""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT * FROM situations ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = cursor.fetchall()
            return [r for r in (self._row_to_dict(row) for row in rows) if r is not None]

    def delete_situation(self, situation_id: str) -> bool:
        """Delete a situation."""
        with self._transaction() as cursor:
            cursor.execute(
                "DELETE FROM situations WHERE id = ?",
                (situation_id,),
            )
            return cursor.rowcount > 0

    # ========================
    # Session Operations
    # ========================

    def save_session(self, session: dict[str, Any]) -> str:
        """Save a session to the database."""
        sess_id = session.get("id") or self._generate_id("sess")
        now = self._now().isoformat()

        data = self._prepare_json_fields(session)

        with self._transaction() as cursor:
            cursor.execute(
                """
                INSERT OR REPLACE INTO sessions
                (id, individual_id, situation_id, active, metadata, created_at, ended_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sess_id,
                    data.get("individual_id"),
                    data.get("situation_id"),
                    1 if data.get("active", True) else 0,
                    data.get("metadata"),
                    data.get("created_at", now),
                    data.get("ended_at"),
                ),
            )

        return sess_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve a session by ID."""
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            result = self._row_to_dict(row)
            if result:
                result["active"] = bool(result.get("active", 0))
            return result

    def list_sessions(
        self,
        individual_id: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List sessions."""
        query = "SELECT * FROM sessions"
        params: list[Any] = []
        conditions: list[str] = []

        if individual_id:
            conditions.append("individual_id = ?")
            params.append(individual_id)

        if active_only:
            conditions.append("active = 1")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._transaction() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results: list[dict[str, Any]] = [r for r in (self._row_to_dict(row) for row in rows) if r is not None]
            for r in results:
                r["active"] = bool(r.get("active", 0))
            return results

    def end_session(self, session_id: str) -> bool:
        """Mark a session as ended."""
        now = self._now().isoformat()
        with self._transaction() as cursor:
            cursor.execute(
                "UPDATE sessions SET active = 0, ended_at = ? WHERE id = ?",
                (now, session_id),
            )
            return cursor.rowcount > 0

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

        data = self._prepare_json_fields(message)

        with self._transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO messages
                (id, session_id, sender, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    msg_id,
                    session_id,
                    data.get("sender", "unknown"),
                    data.get("content", ""),
                    data.get("metadata"),
                    data.get("created_at", now),
                ),
            )

        return msg_id

    def list_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List messages for a session."""
        with self._transaction() as cursor:
            cursor.execute(
                """
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ? OFFSET ?
                """,
                (session_id, limit, offset),
            )
            rows = cursor.fetchall()
            return [r for r in (self._row_to_dict(row) for row in rows) if r is not None]

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

        data = self._prepare_json_fields(memory)

        with self._transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO memories
                (id, individual_id, content, memory_type, importance,
                 embedding, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mem_id,
                    individual_id,
                    data.get("content", ""),
                    data.get("memory_type", "general"),
                    data.get("importance", 0.5),
                    data.get("embedding"),
                    data.get("metadata"),
                    data.get("created_at", now),
                ),
            )

        return mem_id

    def list_memories(
        self,
        individual_id: str,
        memory_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List memories for an individual."""
        query = "SELECT * FROM memories WHERE individual_id = ?"
        params: list[Any] = [individual_id]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY importance DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._transaction() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [r for r in (self._row_to_dict(row) for row in rows) if r is not None]

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        with self._transaction() as cursor:
            cursor.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )
            return cursor.rowcount > 0

    # ========================
    # Lifecycle Operations
    # ========================

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> SQLiteStorage:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


__all__ = ["SQLiteStorage"]
