"""Local embedding model implementation for Personaut PDK.

This module provides local embedding generation using sentence-transformers
or compatible models. This is the default embedding strategy for the PDK.

Example:
    >>> from personaut.models import LocalEmbedding
    >>>
    >>> # Use default lightweight model
    >>> embed = LocalEmbedding()
    >>> vector = embed.embed("Hello, world!")
    >>>
    >>> # Use a specific model
    >>> embed = LocalEmbedding("BAAI/bge-large-en-v1.5")
    >>> vectors = embed.embed_batch(["Text 1", "Text 2"])
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

from personaut.models.embeddings import (
    DEFAULT_MODEL_SMALL,
    EMBEDDING_MODELS,
    EmbeddingError,
    EmbeddingModel,
    ModelLoadError,
)


logger = logging.getLogger(__name__)


def _detect_device() -> str:
    """Detect the best available device for inference.

    Returns:
        Device string: "cuda", "mps", or "cpu".
    """
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def _hash_text(text: str) -> str:
    """Create a hash key for caching embeddings."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


@dataclass
class LocalEmbedding(EmbeddingModel):
    """Local embedding model using sentence-transformers.

    This class provides embedding generation using locally-running models.
    It supports lazy loading, caching, and automatic device selection.

    Attributes:
        model_path: HuggingFace model identifier or local path.
        device: Device for inference ("cpu", "cuda", "mps", "auto").
        batch_size: Maximum batch size for embedding.
        normalize: Whether to L2-normalize embeddings.
        cache_size: Number of embeddings to cache (0 to disable).

    Example:
        >>> embed = LocalEmbedding()
        >>> vector = embed.embed("Meeting at coffee shop")
        >>> len(vector)
        384

        >>> embed = LocalEmbedding("BAAI/bge-large-en-v1.5")
        >>> len(embed.embed("Hello"))
        1024
    """

    model_path: str = DEFAULT_MODEL_SMALL
    device: str = "auto"
    batch_size: int = 32
    normalize: bool = True
    cache_size: int = 1000

    # Private fields
    _model: Any = field(default=None, repr=False, compare=False)
    _dimension: int = field(default=0, repr=False, compare=False)
    _cache: dict[str, list[float]] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize the embedding model."""
        # Resolve device
        if self.device == "auto":
            self.device = _detect_device()

        # Get expected dimension from registry
        if self.model_path in EMBEDDING_MODELS:
            self._dimension = EMBEDDING_MODELS[self.model_path]

    @property
    def dimension(self) -> int:
        """The dimensionality of the embedding vectors."""
        if self._dimension == 0:
            # Need to load model to get dimension
            self._ensure_loaded()
        return self._dimension

    @property
    def model_name(self) -> str:
        """The name/identifier of the embedding model."""
        return self.model_path

    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._model is not None

    def _ensure_loaded(self) -> None:
        """Ensure the model is loaded (lazy loading)."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            msg = (
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install sentence-transformers"
            )
            raise ModelLoadError(msg, model=self.model_path, cause=e) from e

        logger.info(f"Loading embedding model: {self.model_path}")
        try:
            self._model = SentenceTransformer(
                self.model_path,
                device=self.device,
            )
            # Get actual dimension from model
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Loaded {self.model_path} ({self._dimension}d) on {self.device}")
        except Exception as e:
            msg = f"Failed to load embedding model: {self.model_path}"
            raise ModelLoadError(msg, model=self.model_path, cause=e) from e

    def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        # Check cache
        if self.cache_size > 0:
            cache_key = _hash_text(text)
            if cache_key in self._cache:
                return self._cache[cache_key]

        self._ensure_loaded()

        try:
            embedding = self._model.encode(
                text,
                normalize_embeddings=self.normalize,
                convert_to_numpy=True,
            )
            result: list[float] = list(embedding.tolist())

            # Update cache
            if self.cache_size > 0:
                self._update_cache(cache_key, result)

            return result

        except Exception as e:
            msg = "Failed to generate embedding for text"
            raise EmbeddingError(msg, model=self.model_path, cause=e) from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one per input text.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not texts:
            return []

        # Check cache for existing embeddings
        results: list[list[float] | None] = [None] * len(texts)
        texts_to_embed: list[tuple[int, str]] = []

        if self.cache_size > 0:
            for i, text in enumerate(texts):
                cache_key = _hash_text(text)
                if cache_key in self._cache:
                    results[i] = self._cache[cache_key]
                else:
                    texts_to_embed.append((i, text))
        else:
            texts_to_embed = list(enumerate(texts))

        # Embed texts not in cache
        if texts_to_embed:
            self._ensure_loaded()

            try:
                uncached_texts = [t for _, t in texts_to_embed]
                embeddings = self._model.encode(
                    uncached_texts,
                    normalize_embeddings=self.normalize,
                    convert_to_numpy=True,
                    batch_size=self.batch_size,
                    show_progress_bar=len(uncached_texts) > 100,
                )

                for j, (i, text) in enumerate(texts_to_embed):
                    embedding = embeddings[j].tolist()
                    results[i] = embedding

                    # Update cache
                    if self.cache_size > 0:
                        cache_key = _hash_text(text)
                        self._update_cache(cache_key, embedding)

            except Exception as e:
                msg = "Failed to generate batch embeddings"
                raise EmbeddingError(msg, model=self.model_path, cause=e) from e

        # Type narrowing - all results should be populated now
        return [r for r in results if r is not None]

    def _update_cache(self, key: str, embedding: list[float]) -> None:
        """Update the embedding cache with LRU eviction."""
        if len(self._cache) >= self.cache_size:
            # Simple FIFO eviction (not true LRU but good enough)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = embedding

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    def unload(self) -> None:
        """Unload the model to free memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._cache.clear()
            logger.info(f"Unloaded embedding model: {self.model_path}")


def create_local_embedding(
    model: str | None = None,
    device: str = "auto",
    batch_size: int = 32,
    normalize: bool = True,
    cache_size: int = 1000,
) -> LocalEmbedding:
    """Create a local embedding model.

    Args:
        model: Model identifier. Defaults to a lightweight model.
        device: Device for inference ("cpu", "cuda", "mps", "auto").
        batch_size: Maximum batch size for embedding.
        normalize: Whether to L2-normalize embeddings.
        cache_size: Number of embeddings to cache.

    Returns:
        Configured LocalEmbedding instance.

    Example:
        >>> embed = create_local_embedding()
        >>> embed = create_local_embedding("BAAI/bge-large-en-v1.5", device="cuda")
    """
    return LocalEmbedding(
        model_path=model or DEFAULT_MODEL_SMALL,
        device=device,
        batch_size=batch_size,
        normalize=normalize,
        cache_size=cache_size,
    )


__all__ = [
    "LocalEmbedding",
    "create_local_embedding",
]
