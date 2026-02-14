"""Base model interfaces for Personaut PDK.

This module defines the core protocols/ABCs for LLM text generation models.

Example:
    >>> from personaut.models import Model
    >>>
    >>> class MyModel(Model):
    ...     def generate(self, prompt: str, **kwargs) -> str:
    ...         return "Response"
    ...
    ...     def generate_structured(self, prompt: str, schema: type, **kwargs):
    ...         return schema(**parsed_data)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator


T = TypeVar("T")


@dataclass
class ModelConfig:
    """Configuration for an LLM model.

    Attributes:
        model_name: The model identifier (e.g., "gemini-2.0-flash").
        temperature: Controls randomness (0.0-2.0).
        max_tokens: Maximum tokens to generate.
        top_p: Nucleus sampling parameter.
        top_k: Top-k sampling parameter.
        stop_sequences: Sequences that stop generation.
        timeout: Request timeout in seconds.
        extra: Additional provider-specific options.

    Example:
        >>> config = ModelConfig(
        ...     model_name="gemini-2.0-flash",
        ...     temperature=0.7,
        ...     max_tokens=1024,
        ... )
    """

    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95
    top_k: int = 40
    stop_sequences: list[str] = field(default_factory=list)
    timeout: float = 30.0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result from a model generation.

    Attributes:
        text: The generated text.
        finish_reason: Why generation stopped (e.g., "stop", "max_tokens").
        usage: Token usage statistics.
        model: The model that generated this result.
        raw_response: The raw response from the provider.

    Example:
        >>> result = model.generate("Hello")
        >>> print(result.text)
        >>> print(result.usage)
    """

    text: str
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    raw_response: Any = None


class Model(ABC):
    """Abstract base class for LLM text generation models.

    Implementations should provide text generation capabilities for
    a specific provider (Gemini, Bedrock, OpenAI, Ollama, etc.).

    Example:
        >>> model = GeminiModel(api_key="...")
        >>> response = model.generate("Explain quantum computing")
        >>> print(response.text)
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The name/identifier of the model."""
        ...

    @property
    @abstractmethod
    def provider(self) -> str:
        """The provider name (e.g., 'gemini', 'bedrock', 'openai')."""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            stop_sequences: Sequences that stop generation.
            **kwargs: Additional provider-specific options.

        Returns:
            GenerationResult with the generated text.

        Raises:
            ModelError: If generation fails.
        """
        ...

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured output matching a schema.

        Args:
            prompt: The input prompt.
            schema: A dataclass or Pydantic model to parse into.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            **kwargs: Additional provider-specific options.

        Returns:
            An instance of the schema type.

        Raises:
            ModelError: If generation or parsing fails.
        """
        ...

    def generate_stream(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Generate text with streaming.

        Default implementation falls back to non-streaming.
        Override in subclasses that support streaming.

        Args:
            prompt: The input prompt.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            **kwargs: Additional provider-specific options.

        Yields:
            Text chunks as they are generated.
        """
        result = self.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        yield result.text


class AsyncModel(ABC):
    """Abstract base class for async LLM text generation models.

    Use this for providers that support async operations.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The name/identifier of the model."""
        ...

    @property
    @abstractmethod
    def provider(self) -> str:
        """The provider name."""
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text from a prompt asynchronously."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured output asynchronously."""
        ...

    async def generate_stream(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate text with async streaming."""
        result = await self.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        yield result.text


class ModelError(Exception):
    """Base exception for model-related errors."""

    def __init__(
        self,
        message: str,
        provider: str = "",
        model: str = "",
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.cause = cause


class RateLimitError(ModelError):
    """Raised when rate limits are exceeded."""

    pass


class AuthenticationError(ModelError):
    """Raised when authentication fails."""

    pass


class InvalidRequestError(ModelError):
    """Raised when the request is invalid."""

    pass


__all__ = [
    # Base classes
    "Model",
    "AsyncModel",
    # Config and results
    "ModelConfig",
    "GenerationResult",
    # Exceptions
    "ModelError",
    "RateLimitError",
    "AuthenticationError",
    "InvalidRequestError",
]
