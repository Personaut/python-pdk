"""Memory system for Personaut PDK.

This module provides memory storage and retrieval with semantic
similarity search, trust-gated access, and situational grounding.

Example:
    >>> from personaut.memory import (
    ...     Memory,
    ...     IndividualMemory,
    ...     SharedMemory,
    ...     PrivateMemory,
    ...     create_individual_memory,
    ...     InMemoryVectorStore,
    ... )
    >>> from personaut.emotions import EmotionalState
    >>> from personaut.facts import create_coffee_shop_context
    >>>
    >>> # Create a memory with emotional and situational context
    >>> memory = create_individual_memory(
    ...     owner_id="sarah_123",
    ...     description="Great coffee date with Mike",
    ...     emotional_state=EmotionalState({"happy": 0.8}),
    ...     context=create_coffee_shop_context(city="Miami, FL"),
    ... )
    >>>
    >>> # Store in vector store
    >>> store = InMemoryVectorStore()
    >>> store.store(memory, embedding_model.embed(memory.to_embedding_text()))
    >>>
    >>> # Search for similar memories
    >>> results = store.search(query_embedding, limit=5)

Classes:
    Memory: Base class for all memory types.
    MemoryType: Enum of memory types (individual, shared, private).
    IndividualMemory: Personal memory for a single individual.
    SharedMemory: Memory shared between multiple individuals.
    PrivateMemory: Trust-gated memory with access control.
    VectorStore: Protocol for vector storage implementations.
    InMemoryVectorStore: Simple in-memory vector store.
    SQLiteVectorStore: Persistent SQLite-based vector store.

Functions:
    create_memory: Factory function for base Memory.
    create_individual_memory: Factory for IndividualMemory.
    create_shared_memory: Factory for SharedMemory.
    create_private_memory: Factory for PrivateMemory.
    generate_memory_emotional_state: LLM + trait-modulated emotion inference.
    search_memories: Search memories by text query.
    get_relevant_memories: Get memories relevant to a situation.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from personaut.memory.individual import (
    IndividualMemory,
    create_individual_memory,
    generate_memory_emotional_state,
)
from personaut.memory.memory import (
    Memory,
    MemoryType,
    create_memory,
)
from personaut.memory.private import (
    PrivateMemory,
    create_private_memory,
)
from personaut.memory.shared import (
    SharedMemory,
    create_shared_memory,
)
from personaut.memory.sqlite_store import (
    SQLiteVectorStore,
)
from personaut.memory.vector_store import (
    InMemoryVectorStore,
    VectorStore,
)


if TYPE_CHECKING:
    from personaut.facts.context import SituationalContext


# Type alias for embedding functions
EmbeddingFunc = Callable[[str], list[float]]


def search_memories(
    store: VectorStore,
    query: str,
    embed_func: EmbeddingFunc,
    limit: int = 10,
    owner_id: str | None = None,
    trust_level: float = 1.0,
) -> list[tuple[Memory, float]]:
    """Search memories by text query.

    This function embeds the query text and searches the store
    for similar memories, filtering by owner and trust level.

    Args:
        store: The vector store to search.
        query: The text query to search for.
        embed_func: Function that converts text to embedding.
        limit: Maximum number of results.
        owner_id: Optional filter by owner ID.
        trust_level: Trust level for accessing private memories.

    Returns:
        List of (memory, similarity_score) tuples.

    Example:
        >>> results = search_memories(
        ...     store=my_store,
        ...     query="coffee shop meetings",
        ...     embed_func=my_embedding_model.embed,
        ...     limit=5,
        ... )
        >>> for memory, score in results:
        ...     print(f"{score:.2f}: {memory.description}")
    """
    # Embed the query
    query_embedding = embed_func(query)

    # Search the store
    results = store.search(query_embedding, limit=limit * 2, owner_id=owner_id)

    # Filter by trust level for private memories
    filtered_results: list[tuple[Memory, float]] = []
    for memory, score in results:
        if isinstance(memory, PrivateMemory) and not memory.can_access(trust_level):
            continue
        filtered_results.append((memory, score))

        if len(filtered_results) >= limit:
            break

    return filtered_results


def get_relevant_memories(
    store: VectorStore,
    context: SituationalContext,
    embed_func: EmbeddingFunc,
    limit: int = 10,
    owner_id: str | None = None,
    trust_level: float = 1.0,
) -> list[tuple[Memory, float]]:
    """Get memories relevant to a situational context.

    Uses the context's embedding text for similarity search,
    weighting results by category relevance.

    Args:
        store: The vector store to search.
        context: The situational context to match.
        embed_func: Function that converts text to embedding.
        limit: Maximum number of results.
        owner_id: Optional filter by owner ID.
        trust_level: Trust level for accessing private memories.

    Returns:
        List of (memory, similarity_score) tuples.

    Example:
        >>> from personaut.facts import create_coffee_shop_context
        >>>
        >>> context = create_coffee_shop_context(
        ...     city="Miami, FL",
        ...     venue_type="coffee shop",
        ... )
        >>> results = get_relevant_memories(
        ...     store=my_store,
        ...     context=context,
        ...     embed_func=my_embedding_model.embed,
        ... )
    """
    # Generate embedding text from context
    context_text = context.to_embedding_text()

    if not context_text:
        return []

    return search_memories(
        store=store,
        query=context_text,
        embed_func=embed_func,
        limit=limit,
        owner_id=owner_id,
        trust_level=trust_level,
    )


def extract_and_search(
    store: VectorStore,
    text: str,
    embed_func: EmbeddingFunc,
    limit: int = 10,
    owner_id: str | None = None,
    trust_level: float = 1.0,
) -> list[tuple[Memory, float]]:
    """Extract context from text and search for relevant memories.

    This function uses the FactExtractor to extract situational
    context from natural language, then searches for matching memories.

    Args:
        store: The vector store to search.
        text: Natural language describing a situation.
        embed_func: Function that converts text to embedding.
        limit: Maximum number of results.
        owner_id: Optional filter by owner ID.
        trust_level: Trust level for accessing private memories.

    Returns:
        List of (memory, similarity_score) tuples.

    Example:
        >>> results = extract_and_search(
        ...     store=my_store,
        ...     text="We met at a busy coffee shop in downtown Miami",
        ...     embed_func=my_embedding_model.embed,
        ... )
    """
    from personaut.facts import FactExtractor

    # Extract context from text
    extractor = FactExtractor()
    context = extractor.extract(text)

    # If context was extracted, use context search
    if len(context) > 0:
        return get_relevant_memories(
            store=store,
            context=context,
            embed_func=embed_func,
            limit=limit,
            owner_id=owner_id,
            trust_level=trust_level,
        )

    # Fall back to direct text search
    return search_memories(
        store=store,
        query=text,
        embed_func=embed_func,
        limit=limit,
        owner_id=owner_id,
        trust_level=trust_level,
    )


def filter_accessible_memories(
    memories: list[Memory],
    trust_level: float,
) -> list[Memory]:
    """Filter a list of memories by trust level.

    Args:
        memories: List of memories to filter.
        trust_level: The trust level to check against.

    Returns:
        List of accessible memories.
    """
    accessible: list[Memory] = []
    for memory in memories:
        if isinstance(memory, PrivateMemory):
            if memory.can_access(trust_level):
                accessible.append(memory)
        else:
            accessible.append(memory)
    return accessible


__all__ = [
    # Base classes
    "Memory",
    "MemoryType",
    # Memory types
    "IndividualMemory",
    "SharedMemory",
    "PrivateMemory",
    # Factory functions
    "create_memory",
    "create_individual_memory",
    "create_shared_memory",
    "create_private_memory",
    # LLM-powered generation
    "generate_memory_emotional_state",
    # Vector stores
    "VectorStore",
    "InMemoryVectorStore",
    "SQLiteVectorStore",
    # Search functions
    "search_memories",
    "get_relevant_memories",
    "extract_and_search",
    "filter_accessible_memories",
    # Types
    "EmbeddingFunc",
]
