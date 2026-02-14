"""Vector store interface for Personaut PDK.

This module defines the protocol for vector stores that handle
memory storage and similarity-based retrieval.

Example:
    >>> class MyVectorStore(VectorStore):
    ...     def store(self, memory, embedding):
    ...         # Store in your database
    ...         pass
    ...
    ...     def search(self, query_embedding, limit):
    ...         # Return similar memories
    ...         return [(memory, 0.95), ...]
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from personaut.memory.memory import Memory


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector-based memory storage.

    Implementations should handle:
    - Storing memories with their embeddings
    - Similarity search using query embeddings
    - Basic CRUD operations

    The Protocol pattern allows for multiple implementations
    (SQLite, PostgreSQL, in-memory, cloud services, etc.)
    """

    @abstractmethod
    def store(self, memory: Memory, embedding: list[float]) -> None:
        """Store a memory with its embedding vector.

        Args:
            memory: The memory to store.
            embedding: The embedding vector for similarity search.

        Example:
            >>> store.store(memory, [0.1, 0.2, 0.3, ...])
        """
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        owner_id: str | None = None,
    ) -> list[tuple[Memory, float]]:
        """Search for similar memories.

        Args:
            query_embedding: The query embedding vector.
            limit: Maximum number of results to return.
            owner_id: Optional filter by owner ID.

        Returns:
            List of (memory, similarity_score) tuples, sorted by
            similarity in descending order.

        Example:
            >>> results = store.search([0.1, 0.2, 0.3, ...], limit=5)
            >>> for memory, score in results:
            ...     print(f"{memory.description}: {score:.2f}")
        """
        ...

    @abstractmethod
    def get(self, memory_id: str) -> Memory | None:
        """Retrieve a memory by its ID.

        Args:
            memory_id: The unique memory identifier.

        Returns:
            The memory if found, None otherwise.

        Example:
            >>> memory = store.get("mem_abc123")
            >>> if memory:
            ...     print(memory.description)
        """
        ...

    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """Delete a memory by its ID.

        Args:
            memory_id: The unique memory identifier.

        Returns:
            True if deleted, False if not found.

        Example:
            >>> if store.delete("mem_abc123"):
            ...     print("Memory deleted")
        """
        ...

    @abstractmethod
    def update_embedding(self, memory_id: str, embedding: list[float]) -> bool:
        """Update a memory's embedding vector.

        Args:
            memory_id: The unique memory identifier.
            embedding: The new embedding vector.

        Returns:
            True if updated, False if not found.
        """
        ...

    @abstractmethod
    def count(self, owner_id: str | None = None) -> int:
        """Count memories in the store.

        Args:
            owner_id: Optional filter by owner ID.

        Returns:
            The number of memories.
        """
        ...


class InMemoryVectorStore:
    """Simple in-memory vector store for testing and development.

    This implementation stores memories in a dictionary and
    performs brute-force similarity search.

    Not recommended for production with large datasets.

    Example:
        >>> store = InMemoryVectorStore()
        >>> store.store(memory, [0.1, 0.2, 0.3])
        >>> results = store.search([0.1, 0.2, 0.3], limit=5)
    """

    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._memories: dict[str, Memory] = {}
        self._embeddings: dict[str, list[float]] = {}

    def store(self, memory: Memory, embedding: list[float]) -> None:
        """Store a memory with its embedding."""
        self._memories[memory.id] = memory
        self._embeddings[memory.id] = embedding
        # Also store embedding in the memory itself
        memory.embedding = embedding

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        owner_id: str | None = None,
    ) -> list[tuple[Memory, float]]:
        """Search for similar memories using cosine similarity."""
        results: list[tuple[Memory, float]] = []

        for memory_id, memory in self._memories.items():
            # Filter by owner if specified
            if owner_id is not None and hasattr(memory, "owner_id") and memory.owner_id != owner_id:
                continue

            embedding = self._embeddings.get(memory_id)
            if embedding is None:
                continue

            similarity = self._cosine_similarity(query_embedding, embedding)
            results.append((memory, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:limit]

    def get(self, memory_id: str) -> Memory | None:
        """Retrieve a memory by ID."""
        return self._memories.get(memory_id)

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        if memory_id in self._memories:
            del self._memories[memory_id]
            self._embeddings.pop(memory_id, None)
            return True
        return False

    def update_embedding(self, memory_id: str, embedding: list[float]) -> bool:
        """Update a memory's embedding."""
        if memory_id in self._memories:
            self._embeddings[memory_id] = embedding
            self._memories[memory_id].embedding = embedding
            return True
        return False

    def count(self, owner_id: str | None = None) -> int:
        """Count memories in the store."""
        if owner_id is None:
            return len(self._memories)

        count = 0
        for memory in self._memories.values():
            if hasattr(memory, "owner_id") and memory.owner_id == owner_id:
                count += 1
        return count

    def clear(self) -> None:
        """Clear all memories from the store."""
        self._memories.clear()
        self._embeddings.clear()

    def get_all(self) -> list[Memory]:
        """Get all memories in the store."""
        return list(self._memories.values())

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
    "InMemoryVectorStore",
    "VectorStore",
]
