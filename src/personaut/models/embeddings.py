"""Embedding model interfaces for Personaut PDK.

This module defines the core protocols/ABCs for embedding models.
The PDK uses a **local-first embedding strategy** where embeddings
are generated locally for consistency across all LLM providers.

Default embedding model: Qwen3-Embedding-8B (4096 dimensions)

Example:
    >>> from personaut.models import get_embedding
    >>>
    >>> embed = get_embedding()  # Returns LocalEmbedding
    >>> vector = embed.embed("Hello, world!")
    >>> print(f"Dimensions: {embed.dimension}")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmbeddingConfig:
    """Configuration for an embedding model.

    Attributes:
        model_name: The model identifier.
        dimension: Output embedding dimensions.
        device: Device for inference ("cpu", "cuda", "mps", "auto").
        batch_size: Maximum batch size for embedding.
        normalize: Whether to L2-normalize embeddings.
        cache_embeddings: Whether to cache embeddings.
        max_length: Maximum token length for input text.

    Example:
        >>> config = EmbeddingConfig(
        ...     model_name="Qwen/Qwen3-Embedding-8B",
        ...     device="auto",
        ...     batch_size=32,
        ... )
    """

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    device: str = "auto"
    batch_size: int = 32
    normalize: bool = True
    cache_embeddings: bool = True
    max_length: int = 512


# Known embedding models with their dimensions
EMBEDDING_MODELS: dict[str, int] = {
    # High quality (large)
    "Qwen/Qwen3-Embedding-8B": 4096,
    "Alibaba-NLP/gte-Qwen2-7B-instruct": 3584,
    # Good balance
    "BAAI/bge-large-en-v1.5": 1024,
    "BAAI/bge-base-en-v1.5": 768,
    # Fast and lightweight
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
    # Long context
    "nomic-ai/nomic-embed-text-v1.5": 768,
}

# Default model for each size tier
DEFAULT_MODEL_LARGE = "BAAI/bge-large-en-v1.5"  # Good quality, ~1.3GB
DEFAULT_MODEL_SMALL = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, ~80MB


class EmbeddingModel(ABC):
    """Abstract base class for embedding models.

    Implementations generate vector embeddings from text input.
    The PDK uses local embedding models by default for consistency.

    Example:
        >>> embed = LocalEmbedding()
        >>> vector = embed.embed("Meeting at coffee shop")
        >>> vectors = embed.embed_batch(["Text 1", "Text 2"])
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """The dimensionality of the embedding vectors."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The name/identifier of the embedding model."""
        ...

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one per input text.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        ...

    def is_loaded(self) -> bool:
        """Check if the model is loaded and ready.

        Returns:
            True if the model is loaded, False otherwise.
        """
        return True  # Override in subclasses with lazy loading


class EmbeddingError(Exception):
    """Base exception for embedding-related errors."""

    def __init__(
        self,
        message: str,
        model: str = "",
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.model = model
        self.cause = cause


class ModelNotLoadedError(EmbeddingError):
    """Raised when trying to use an unloaded model."""

    pass


class ModelLoadError(EmbeddingError):
    """Raised when a model fails to load."""

    pass


class TextTooLongError(EmbeddingError):
    """Raised when input text exceeds max length."""

    def __init__(
        self,
        message: str,
        text_length: int,
        max_length: int,
        model: str = "",
    ) -> None:
        super().__init__(message, model)
        self.text_length = text_length
        self.max_length = max_length


__all__ = [
    # Base class
    "EmbeddingModel",
    # Config
    "EmbeddingConfig",
    # Constants
    "EMBEDDING_MODELS",
    "DEFAULT_MODEL_LARGE",
    "DEFAULT_MODEL_SMALL",
    # Exceptions
    "EmbeddingError",
    "ModelNotLoadedError",
    "ModelLoadError",
    "TextTooLongError",
]
