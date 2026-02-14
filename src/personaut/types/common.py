"""Common type definitions for Personaut PDK.

This module provides type aliases, TypeVars, and Protocol classes used
throughout the Personaut PDK for consistent typing and interface definitions.

Example:
    >>> from personaut.types.common import EmotionDict, TraitDict
    >>> emotions: EmotionDict = {"anxious": 0.6, "hopeful": 0.8}
    >>> traits: TraitDict = {"warmth": 0.9}
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar, runtime_checkable


# =============================================================================
# Type Aliases
# =============================================================================

EmotionDict = dict[str, float]
"""Dictionary mapping emotion names to their intensity values (0.0-1.0)."""

TraitDict = dict[str, float]
"""Dictionary mapping trait names to their values (0.0-1.0)."""

TrustDict = dict[str, float]
"""Dictionary mapping individual IDs to trust levels (0.0-1.0)."""

EmbeddingVector = list[float]
"""Vector representation of text for semantic similarity search."""

JsonDict = dict[str, Any]
"""Generic JSON-serializable dictionary."""


# =============================================================================
# TypeVars
# =============================================================================

T = TypeVar("T")
"""Generic type variable for parameterized types."""

T_co = TypeVar("T_co", covariant=True)
"""Covariant type variable for return types in generic interfaces."""

IndividualT = TypeVar("IndividualT", bound="IndividualProtocol")
"""Type variable bound to Individual-like objects."""

MemoryT = TypeVar("MemoryT", bound="MemoryProtocol")
"""Type variable bound to Memory-like objects."""


# =============================================================================
# Protocol Classes
# =============================================================================


@runtime_checkable
class IndividualProtocol(Protocol):
    """Protocol defining the interface for an Individual.

    This protocol defines the minimum interface that any Individual-like
    object must implement. Used for type checking without requiring
    inheritance from a specific base class.

    Attributes:
        id: Unique identifier for the individual.
        name: Display name of the individual.

    Example:
        >>> def greet(individual: IndividualProtocol) -> str:
        ...     return f"Hello, {individual.name}!"
    """

    @property
    def id(self) -> str:
        """Unique identifier for the individual."""
        ...

    @property
    def name(self) -> str:
        """Display name of the individual."""
        ...


@runtime_checkable
class EmotionalStateProtocol(Protocol):
    """Protocol defining the interface for an EmotionalState.

    This protocol defines the minimum interface for emotional state objects,
    allowing for different implementations while maintaining type safety.
    """

    def get_emotion(self, emotion: str) -> float:
        """Get the current value of an emotion.

        Args:
            emotion: Name of the emotion to query.

        Returns:
            Current value of the emotion (0.0-1.0).
        """
        ...

    def change_emotion(self, emotion: str, value: float) -> None:
        """Change the value of an emotion.

        Args:
            emotion: Name of the emotion to change.
            value: New value for the emotion (0.0-1.0).
        """
        ...

    def to_dict(self) -> EmotionDict:
        """Convert emotional state to a dictionary.

        Returns:
            Dictionary mapping emotion names to values.
        """
        ...


@runtime_checkable
class MemoryProtocol(Protocol):
    """Protocol defining the interface for a Memory.

    This protocol defines the minimum interface for memory objects,
    enabling different memory types to be used interchangeably.

    Attributes:
        id: Unique identifier for the memory.
        description: Text description of the memory.
    """

    @property
    def id(self) -> str:
        """Unique identifier for the memory."""
        ...

    @property
    def description(self) -> str:
        """Text description of the memory."""
        ...


@runtime_checkable
class ModelProtocol(Protocol):
    """Protocol defining the interface for an LLM Model.

    This protocol defines the minimum interface for language model
    implementations, allowing different providers to be used interchangeably.
    """

    def generate(self, prompt: str) -> str:
        """Generate text from a prompt.

        Args:
            prompt: Input prompt for generation.

        Returns:
            Generated text response.
        """
        ...


@runtime_checkable
class EmbeddingModelProtocol(Protocol):
    """Protocol defining the interface for an Embedding Model.

    This protocol defines the interface for text embedding models
    used in semantic memory search.
    """

    def embed(self, text: str) -> EmbeddingVector:
        """Generate an embedding vector for text.

        Args:
            text: Input text to embed.

        Returns:
            Embedding vector representation.
        """
        ...


@runtime_checkable
class VectorStoreProtocol(Protocol):
    """Protocol defining the interface for a Vector Store.

    This protocol defines the interface for vector storage backends
    used in the memory system.
    """

    def store(self, id: str, embedding: EmbeddingVector, metadata: JsonDict) -> None:
        """Store an embedding with metadata.

        Args:
            id: Unique identifier for the stored item.
            embedding: Vector representation to store.
            metadata: Additional metadata to store.
        """
        ...

    def search(
        self,
        query_embedding: EmbeddingVector,
        limit: int = 10,
    ) -> list[tuple[str, float, JsonDict]]:
        """Search for similar embeddings.

        Args:
            query_embedding: Query vector for similarity search.
            limit: Maximum number of results to return.

        Returns:
            List of (id, similarity_score, metadata) tuples.
        """
        ...


# =============================================================================
# Callback Types
# =============================================================================

OnTurnCallback = Callable[[int, str, str], None]
"""Callback invoked after each turn in a simulation.

Args:
    turn_number: The current turn number (1-indexed).
    speaker: ID of the individual who spoke.
    message: The message content.
"""

OnCompleteCallback = Callable[[JsonDict], None]
"""Callback invoked when a simulation completes.

Args:
    result: Dictionary containing simulation results.
"""

OnEmotionChangeCallback = Callable[[str, str, float, float], None]
"""Callback invoked when an emotion changes.

Args:
    individual_id: ID of the individual whose emotion changed.
    emotion: Name of the emotion that changed.
    old_value: Previous emotion value.
    new_value: New emotion value.
"""


__all__ = [
    # Protocols
    "EmbeddingModelProtocol",
    # Type aliases
    "EmbeddingVector",
    "EmotionDict",
    "EmotionalStateProtocol",
    "IndividualProtocol",
    # TypeVars
    "IndividualT",
    "JsonDict",
    "MemoryProtocol",
    "MemoryT",
    "ModelProtocol",
    # Callbacks
    "OnCompleteCallback",
    "OnEmotionChangeCallback",
    "OnTurnCallback",
    "T",
    "T_co",
    "TraitDict",
    "TrustDict",
    "VectorStoreProtocol",
]
