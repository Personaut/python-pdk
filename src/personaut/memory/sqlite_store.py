"""SQLite vector store for Personaut PDK.

This module provides a persistent vector store implementation
using SQLite with the sqlite-vec extension for vector similarity search.

Example:
    >>> from personaut.memory import SQLiteVectorStore
    >>>
    >>> store = SQLiteVectorStore("memories.db", dimensions=384)
    >>> store.store(memory, embedding)
    >>> results = store.search(query_embedding, limit=10)
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from personaut.memory.individual import IndividualMemory
from personaut.memory.memory import Memory
from personaut.memory.private import PrivateMemory
from personaut.memory.shared import SharedMemory


class SQLiteVectorStore:
    """Persistent vector store using SQLite and sqlite-vec.

    This implementation stores memories in SQLite and uses the
    sqlite-vec extension for efficient vector similarity search.

    Attributes:
        db_path: Path to the SQLite database file.
        dimensions: Dimensionality of embedding vectors.

    Example:
        >>> store = SQLiteVectorStore("data/memories.db", dimensions=384)
        >>> store.store(memory, [0.1, 0.2, ...])
        >>> results = store.search([0.1, 0.2, ...], limit=5)
        >>> store.close()
    """

    def __init__(
        self,
        db_path: str | Path,
        dimensions: int = 384,
        auto_create: bool = True,
    ) -> None:
        """Initialize the SQLite vector store.

        Args:
            db_path: Path to the SQLite database file.
            dimensions: Dimensionality of embedding vectors.
            auto_create: Whether to create tables automatically.
        """
        self.db_path = Path(db_path)
        self.dimensions = dimensions
        self._conn: sqlite3.Connection | None = None

        if auto_create:
            self._ensure_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create the database connection."""
        if self._conn is None:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row

            # Try to load sqlite-vec extension
            try:
                import sqlite_vec

                self._conn.enable_load_extension(True)
                sqlite_vec.load(self._conn)
                self._conn.enable_load_extension(False)
                self._vec_enabled = True
            except (ImportError, Exception):
                # Fall back to non-vector mode
                self._vec_enabled = False

        return self._conn

    def _ensure_tables(self) -> None:
        """Create database tables if they don't exist."""
        conn = self._get_connection()

        # Main memories table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                owner_id TEXT,
                created_at TEXT NOT NULL,
                data TEXT NOT NULL,
                embedding_blob BLOB
            )
        """)

        # Index for owner_id lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_owner
            ON memories(owner_id)
        """)

        # Index for memory_type lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_type
            ON memories(memory_type)
        """)

        # Virtual table for vector search (if sqlite-vec is available)
        if getattr(self, "_vec_enabled", False):
            try:
                conn.execute(f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memory_embeddings
                    USING vec0(
                        memory_id TEXT PRIMARY KEY,
                        embedding FLOAT[{self.dimensions}]
                    )
                """)
            except sqlite3.OperationalError:
                # Virtual table may already exist with different dimensions
                pass

        conn.commit()

    def store(self, memory: Memory, embedding: list[float]) -> None:
        """Store a memory with its embedding."""
        conn = self._get_connection()

        # Determine owner_id for indexed lookup
        owner_id = None
        if hasattr(memory, "owner_id"):
            owner_id = memory.owner_id

        # Serialize memory data
        data = memory.to_dict()
        data_json = json.dumps(data)

        # Serialize embedding as blob
        import struct

        embedding_blob = struct.pack(f"{len(embedding)}f", *embedding)

        # Insert or replace memory
        conn.execute(
            """
            INSERT OR REPLACE INTO memories
            (id, description, memory_type, owner_id, created_at, data, embedding_blob)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory.id,
                memory.description,
                memory.memory_type.value,
                owner_id,
                memory.created_at.isoformat(),
                data_json,
                embedding_blob,
            ),
        )

        # Store in vector index if available
        if self._vec_enabled:
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO memory_embeddings (memory_id, embedding)
                    VALUES (?, ?)
                    """,
                    (memory.id, json.dumps(embedding)),
                )
            except sqlite3.OperationalError:
                pass  # Vector table may not exist

        conn.commit()

        # Also store embedding in memory object
        memory.embedding = embedding

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        owner_id: str | None = None,
    ) -> list[tuple[Memory, float]]:
        """Search for similar memories."""
        conn = self._get_connection()

        # Try vector search first
        if self._vec_enabled:
            try:
                return self._vector_search(conn, query_embedding, limit, owner_id)
            except sqlite3.OperationalError:
                pass

        # Fall back to brute force
        return self._brute_force_search(conn, query_embedding, limit, owner_id)

    def _vector_search(
        self,
        conn: sqlite3.Connection,
        query_embedding: list[float],
        limit: int,
        owner_id: str | None,
    ) -> list[tuple[Memory, float]]:
        """Perform vector search using sqlite-vec."""
        query_json = json.dumps(query_embedding)

        if owner_id:
            # Filter by owner
            rows = conn.execute(
                """
                SELECT m.data, v.distance
                FROM memory_embeddings v
                JOIN memories m ON m.id = v.memory_id
                WHERE m.owner_id = ?
                ORDER BY v.embedding <-> ?
                LIMIT ?
                """,
                (owner_id, query_json, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT m.data, v.distance
                FROM memory_embeddings v
                JOIN memories m ON m.id = v.memory_id
                ORDER BY v.embedding <-> ?
                LIMIT ?
                """,
                (query_json, limit),
            ).fetchall()

        results: list[tuple[Memory, float]] = []
        for row in rows:
            data = json.loads(row["data"])
            memory = self._memory_from_dict(data)
            # Convert distance to similarity (1 - distance for L2, or use cosine)
            similarity = max(0.0, 1.0 - row["distance"])
            results.append((memory, similarity))

        return results

    def _brute_force_search(
        self,
        conn: sqlite3.Connection,
        query_embedding: list[float],
        limit: int,
        owner_id: str | None,
    ) -> list[tuple[Memory, float]]:
        """Perform brute force similarity search."""
        import struct

        if owner_id:
            rows = conn.execute(
                "SELECT data, embedding_blob FROM memories WHERE owner_id = ?",
                (owner_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT data, embedding_blob FROM memories").fetchall()

        results: list[tuple[Memory, float]] = []
        for row in rows:
            if row["embedding_blob"] is None:
                continue

            # Deserialize embedding
            blob = row["embedding_blob"]
            n_floats = len(blob) // 4
            stored_embedding = list(struct.unpack(f"{n_floats}f", blob))

            # Compute similarity
            similarity = self._cosine_similarity(query_embedding, stored_embedding)

            # Deserialize memory
            data = json.loads(row["data"])
            memory = self._memory_from_dict(data)

            results.append((memory, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:limit]

    def get(self, memory_id: str) -> Memory | None:
        """Retrieve a memory by ID."""
        conn = self._get_connection()

        row = conn.execute(
            "SELECT data FROM memories WHERE id = ?",
            (memory_id,),
        ).fetchone()

        if row is None:
            return None

        data = json.loads(row["data"])
        return self._memory_from_dict(data)

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        conn = self._get_connection()

        cursor = conn.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,),
        )

        if self._vec_enabled:
            try:
                conn.execute(
                    "DELETE FROM memory_embeddings WHERE memory_id = ?",
                    (memory_id,),
                )
            except sqlite3.OperationalError:
                pass

        conn.commit()

        return cursor.rowcount > 0

    def update_embedding(self, memory_id: str, embedding: list[float]) -> bool:
        """Update a memory's embedding."""
        conn = self._get_connection()
        import struct

        embedding_blob = struct.pack(f"{len(embedding)}f", *embedding)

        cursor = conn.execute(
            "UPDATE memories SET embedding_blob = ? WHERE id = ?",
            (embedding_blob, memory_id),
        )

        if self._vec_enabled:
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO memory_embeddings (memory_id, embedding)
                    VALUES (?, ?)
                    """,
                    (memory_id, json.dumps(embedding)),
                )
            except sqlite3.OperationalError:
                pass

        conn.commit()

        return cursor.rowcount > 0

    def count(self, owner_id: str | None = None) -> int:
        """Count memories in the store."""
        conn = self._get_connection()

        if owner_id:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM memories WHERE owner_id = ?",
                (owner_id,),
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()

        return row["cnt"] if row else 0

    def get_by_owner(self, owner_id: str, limit: int = 100) -> list[Memory]:
        """Get all memories for a specific owner.

        Args:
            owner_id: The owner ID to filter by.
            limit: Maximum number of results.

        Returns:
            List of memories belonging to the owner.
        """
        conn = self._get_connection()

        rows = conn.execute(
            """
            SELECT data FROM memories
            WHERE owner_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (owner_id, limit),
        ).fetchall()

        return [self._memory_from_dict(json.loads(row["data"])) for row in rows]

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> SQLiteVectorStore:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    @staticmethod
    def _memory_from_dict(data: dict[str, Any]) -> Memory:
        """Create the appropriate Memory subclass from dictionary."""
        memory_type = data.get("memory_type", "individual")

        if memory_type == "individual":
            return IndividualMemory.from_dict(data)
        elif memory_type == "shared":
            return SharedMemory.from_dict(data)
        elif memory_type == "private":
            return PrivateMemory.from_dict(data)
        else:
            return Memory.from_dict(data)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))


__all__ = [
    "SQLiteVectorStore",
]
