"""Model registry for Personaut PDK.

This module provides a centralized registry for managing LLM and embedding
model providers. It implements a local-first embedding strategy where
embeddings are always generated locally for consistency.

Example:
    >>> from personaut.models import get_llm, get_embedding
    >>>
    >>> # Get default LLM (from environment or config)
    >>> model = get_llm()
    >>> result = model.generate("Hello!")
    >>>
    >>> # Get embedding model (always local)
    >>> embed = get_embedding()
    >>> vector = embed.embed("Hello!")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from personaut.models.embeddings import EmbeddingModel
from personaut.models.model import Model, ModelError


logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """Supported LLM providers."""

    GEMINI = "gemini"
    BEDROCK = "bedrock"
    OPENAI = "openai"
    OLLAMA = "ollama"


# Environment variable names for configuration
ENV_LLM_PROVIDER = "PERSONAUT_LLM_PROVIDER"
ENV_LLM_MODEL = "PERSONAUT_LLM_MODEL"
ENV_EMBEDDING_MODEL = "PERSONAUT_EMBEDDING_MODEL"

# Default provider priority (checked in order)
DEFAULT_PROVIDER_PRIORITY = [
    Provider.GEMINI,
    Provider.OPENAI,
    Provider.BEDROCK,
    Provider.OLLAMA,
]


@dataclass
class ModelRegistry:
    """Central registry for managing model providers.

    The registry provides a unified interface for obtaining LLM and
    embedding models, with automatic provider detection and fallbacks.

    The embedding model is always local (sentence-transformers) to ensure
    consistent vector representations across all LLM providers.

    Attributes:
        default_provider: Preferred LLM provider.
        embedding_model: Embedding model name/path.
        models: Cache of initialized models.

    Example:
        >>> registry = ModelRegistry()
        >>> llm = registry.get_llm()
        >>> embed = registry.get_embedding()
    """

    default_provider: Provider | str | None = None
    embedding_model: str | None = None

    # Cached models
    _embedding: EmbeddingModel | None = field(default=None, repr=False)
    _llms: dict[str, Model] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """Initialize from environment variables."""
        # Get provider from environment
        if self.default_provider is None:
            env_provider = os.environ.get(ENV_LLM_PROVIDER)
            if env_provider:
                try:
                    self.default_provider = Provider(env_provider.lower())
                except ValueError:
                    logger.warning(f"Unknown provider: {env_provider}")

        # Get embedding model from environment
        if self.embedding_model is None:
            self.embedding_model = os.environ.get(ENV_EMBEDDING_MODEL)

    def get_llm(
        self,
        provider: Provider | str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> Model:
        """Get an LLM model.

        Args:
            provider: Provider to use (or detect automatically).
            model: Specific model name (optional).
            **kwargs: Additional provider-specific options.

        Returns:
            Configured Model instance.

        Raises:
            ModelError: If no provider is available.

        Example:
            >>> llm = registry.get_llm()  # Auto-detect
            >>> llm = registry.get_llm(Provider.GEMINI)
            >>> llm = registry.get_llm("openai", model="gpt-4o")
        """
        # Determine provider
        if provider is None:
            provider = self.default_provider or self._detect_provider()

        if isinstance(provider, str):
            provider = Provider(provider.lower())

        # Check cache
        cache_key = f"{provider.value}:{model or 'default'}"
        if cache_key in self._llms and not kwargs:
            return self._llms[cache_key]

        # Get model from environment if not specified
        if model is None:
            model = os.environ.get(ENV_LLM_MODEL)

        # Create model
        llm = self._create_llm(provider, model, **kwargs)
        self._llms[cache_key] = llm
        return llm

    def get_embedding(
        self,
        model: str | None = None,
        **kwargs: Any,
    ) -> EmbeddingModel:
        """Get the embedding model.

        The embedding model is always local (sentence-transformers) to
        ensure consistent vector representations.

        Args:
            model: Specific model name (optional).
            **kwargs: Additional options.

        Returns:
            Configured EmbeddingModel instance.

        Example:
            >>> embed = registry.get_embedding()
            >>> vector = embed.embed("Hello, world!")
        """
        # Return cached if model matches
        if self._embedding is not None and model is None and not kwargs:
            return self._embedding

        from personaut.models.local_embedding import LocalEmbedding

        embed = LocalEmbedding(
            model_path=model or self.embedding_model or "sentence-transformers/all-MiniLM-L6-v2",
            **kwargs,
        )

        if model is None and not kwargs:
            self._embedding = embed

        return embed

    def _detect_provider(self) -> Provider:
        """Detect available provider based on credentials.

        Returns:
            The first available provider.

        Raises:
            ModelError: If no provider is available.
        """
        for provider in DEFAULT_PROVIDER_PRIORITY:
            if self._check_provider_available(provider):
                logger.info(f"Auto-detected provider: {provider.value}")
                return provider

        msg = "No LLM provider available. Set one of: GOOGLE_API_KEY, OPENAI_API_KEY, or configure AWS credentials"
        raise ModelError(msg, provider="registry")

    def _check_provider_available(self, provider: Provider) -> bool:
        """Check if a provider is available."""
        if provider == Provider.GEMINI:
            return bool(os.environ.get("GOOGLE_API_KEY"))
        elif provider == Provider.OPENAI:
            return bool(os.environ.get("OPENAI_API_KEY"))
        elif provider == Provider.BEDROCK:
            # Check for AWS credentials
            return bool(
                os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE") or os.environ.get("AWS_ROLE_ARN")
            )
        elif provider == Provider.OLLAMA:
            # Check if Ollama is running
            try:
                from personaut.models.ollama import OllamaModel

                return OllamaModel().is_available()
            except Exception:
                return False
        return False

    def _create_llm(
        self,
        provider: Provider,
        model: str | None = None,
        **kwargs: Any,
    ) -> Model:
        """Create an LLM model for the given provider."""
        if provider == Provider.GEMINI:
            from personaut.models.gemini import DEFAULT_GEMINI_MODEL, GeminiModel

            return GeminiModel(
                model=model or DEFAULT_GEMINI_MODEL,
                **kwargs,
            )
        elif provider == Provider.OPENAI:
            from personaut.models.openai import DEFAULT_OPENAI_MODEL, OpenAIModel

            return OpenAIModel(
                model=model or DEFAULT_OPENAI_MODEL,
                **kwargs,
            )
        elif provider == Provider.BEDROCK:
            from personaut.models.bedrock import DEFAULT_BEDROCK_MODEL, BedrockModel

            return BedrockModel(
                model=model or DEFAULT_BEDROCK_MODEL,
                **kwargs,
            )
        elif provider == Provider.OLLAMA:
            from personaut.models.ollama import DEFAULT_OLLAMA_MODEL, OllamaModel

            return OllamaModel(
                model=model or DEFAULT_OLLAMA_MODEL,
                **kwargs,
            )
        else:
            msg = f"Unknown provider: {provider}"
            raise ModelError(msg, provider=str(provider))

    def list_providers(self) -> list[tuple[Provider, bool]]:
        """List all providers and their availability.

        Returns:
            List of (provider, is_available) tuples.
        """
        return [(provider, self._check_provider_available(provider)) for provider in Provider]


# Global registry instance
_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Get the global model registry.

    Returns:
        The global ModelRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def get_llm(
    provider: Provider | str | None = None,
    model: str | None = None,
    **kwargs: Any,
) -> Model:
    """Get an LLM model from the global registry.

    Args:
        provider: Provider to use (or auto-detect).
        model: Specific model name.
        **kwargs: Additional options.

    Returns:
        Configured Model instance.

    Example:
        >>> llm = get_llm()
        >>> result = llm.generate("Hello!")
    """
    return get_registry().get_llm(provider, model, **kwargs)


def get_embedding(
    model: str | None = None,
    **kwargs: Any,
) -> EmbeddingModel:
    """Get the embedding model from the global registry.

    The embedding model is always local for consistency.

    Args:
        model: Specific model name.
        **kwargs: Additional options.

    Returns:
        Configured EmbeddingModel instance.

    Example:
        >>> embed = get_embedding()
        >>> vector = embed.embed("Hello!")
    """
    return get_registry().get_embedding(model, **kwargs)


__all__ = [
    # Registry
    "ModelRegistry",
    "get_registry",
    # Convenience functions
    "get_llm",
    "get_embedding",
    # Constants
    "Provider",
    "ENV_LLM_PROVIDER",
    "ENV_LLM_MODEL",
    "ENV_EMBEDDING_MODEL",
]
