"""Anthropic (Claude) model provider for Personaut PDK.

This module provides Anthropic integration for LLM text generation using Claude models.
Note: Embeddings are handled by the local embedding model for consistency.

Example:
    >>> from personaut.models import AnthropicModel
    >>>
    >>> model = AnthropicModel()  # Uses ANTHROPIC_API_KEY env var
    >>> result = model.generate("Write a story about robots")
    >>> print(result.text)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar

from personaut.models.model import (
    AuthenticationError,
    GenerationResult,
    InvalidRequestError,
    Model,
    ModelConfig,
    ModelError,
    RateLimitError,
)


if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default Anthropic models
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"
AVAILABLE_ANTHROPIC_MODELS = [
    "claude-opus-4-6",
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
]


@dataclass
class AnthropicModel(Model):
    """Anthropic (Claude) model implementation.

    This class provides access to Claude models including Claude 4.6 Opus,
    Claude 4.5 Sonnet, and Claude 4.5 Haiku. Authentication is via the
    ANTHROPIC_API_KEY environment variable or explicit api_key parameter.

    Attributes:
        api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
        model: Anthropic model name.
        config: Model configuration.

    Example:
        >>> model = AnthropicModel()
        >>> result = model.generate("Explain neural networks")
        >>> print(result.text)

        >>> # With custom config
        >>> model = AnthropicModel(
        ...     model="claude-opus-4-6",
        ...     config=ModelConfig(temperature=0.9, max_tokens=4096),
        ... )
    """

    api_key: str | None = None
    model: str = DEFAULT_ANTHROPIC_MODEL
    config: ModelConfig = field(default_factory=lambda: ModelConfig(model_name=DEFAULT_ANTHROPIC_MODEL))

    # Private fields
    _client: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize the Anthropic client."""
        # Get API key from environment if not provided
        if self.api_key is None:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            msg = "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            raise AuthenticationError(msg, provider="anthropic")

        # Update config model name
        self.config = ModelConfig(
            model_name=self.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            stop_sequences=self.config.stop_sequences,
            timeout=self.config.timeout,
            extra=self.config.extra,
        )

    @property
    def model_name(self) -> str:
        """The name/identifier of the model."""
        return self.model

    @property
    def provider(self) -> str:
        """The provider name."""
        return "anthropic"

    def _ensure_client(self) -> Any:
        """Ensure the Anthropic client is initialized."""
        if self._client is not None:
            return self._client

        try:
            from anthropic import Anthropic
        except ImportError as e:
            msg = "anthropic is required for Anthropic models. Install with: pip install anthropic"
            raise ModelError(msg, provider="anthropic", cause=e) from e

        self._client = Anthropic(
            api_key=self.api_key,
            timeout=self.config.timeout,
        )
        return self._client

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
            **kwargs: Additional options.

        Returns:
            GenerationResult with the generated text.

        Raises:
            ModelError: If generation fails.
        """
        client = self._ensure_client()

        # Handle system message if provided
        system = kwargs.pop("system", None)

        # Build generation parameters
        gen_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or self.config.max_tokens or 2048,
        }

        if system:
            gen_kwargs["system"] = system

        gen_kwargs["temperature"] = temperature if temperature is not None else self.config.temperature

        if self.config.top_p and self.config.top_p != 0.95:
            gen_kwargs["top_p"] = self.config.top_p

        if self.config.top_k and self.config.top_k != 40:
            gen_kwargs["top_k"] = self.config.top_k

        if stop_sequences or self.config.stop_sequences:
            gen_kwargs["stop_sequences"] = stop_sequences or self.config.stop_sequences

        try:
            response = client.messages.create(**gen_kwargs)

            # Extract text from content blocks
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text

            # Get usage
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                }

            return GenerationResult(
                text=text,
                finish_reason=response.stop_reason or "stop",
                usage=usage,
                model=response.model,
                raw_response=response,
            )

        except Exception as e:
            self._handle_error(e)

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
            **kwargs: Additional options.

        Returns:
            An instance of the schema type.

        Raises:
            ModelError: If generation or parsing fails.
        """
        # Manual JSON parsing (Claude API doesn't have native structured output like OpenAI)
        schema_prompt = f"""
{prompt}

Respond ONLY with valid JSON matching this schema:
{self._schema_to_json_schema(schema)}

Output JSON only, no other text.
"""

        result = self.generate(
            schema_prompt,
            temperature=temperature or 0.3,
            max_tokens=max_tokens,
            **kwargs,
        )

        try:
            text = result.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            data = json.loads(text)
            return schema(**data)

        except (json.JSONDecodeError, TypeError) as e:
            msg = f"Failed to parse response as {schema.__name__}: {result.text[:100]}"
            raise InvalidRequestError(msg, provider="anthropic", model=self.model, cause=e) from e

    def generate_stream(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Generate text with streaming.

        Args:
            prompt: The input prompt.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            **kwargs: Additional options.

        Yields:
            Text chunks as they are generated.
        """
        client = self._ensure_client()

        system = kwargs.pop("system", None)

        gen_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or self.config.max_tokens or 2048,
        }

        if system:
            gen_kwargs["system"] = system

        gen_kwargs["temperature"] = temperature if temperature is not None else self.config.temperature

        try:
            with client.messages.stream(**gen_kwargs) as stream:
                yield from stream.text_stream

        except Exception as e:
            self._handle_error(e)

    def _schema_to_json_schema(self, schema: type) -> str:
        """Convert a dataclass or Pydantic model to JSON schema description."""
        import dataclasses

        if dataclasses.is_dataclass(schema):
            fields = {}
            for f in dataclasses.fields(schema):
                field_type = str(f.type).replace("typing.", "")
                fields[f.name] = field_type
            return json.dumps(fields, indent=2)

        if hasattr(schema, "model_json_schema"):
            return json.dumps(schema.model_json_schema(), indent=2)

        return str(schema)

    def _handle_error(self, e: Exception) -> NoReturn:
        """Convert Anthropic exceptions to ModelError types."""
        error_str = str(e).lower()
        error_type = type(e).__name__.lower()

        if "rate" in error_str or "ratelimit" in error_type or "429" in error_str:
            raise RateLimitError(str(e), provider="anthropic", model=self.model, cause=e) from e
        elif "auth" in error_str or "api key" in error_str or "401" in error_str:
            raise AuthenticationError(str(e), provider="anthropic", model=self.model, cause=e) from e
        elif "invalid" in error_str or "bad request" in error_type or "400" in error_str:
            raise InvalidRequestError(str(e), provider="anthropic", model=self.model, cause=e) from e
        else:
            raise ModelError(str(e), provider="anthropic", model=self.model, cause=e) from e


def create_anthropic_model(
    model: str = DEFAULT_ANTHROPIC_MODEL,
    api_key: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AnthropicModel:
    """Create an Anthropic model with configuration.

    Args:
        model: Anthropic model name.
        api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var).
        temperature: Generation temperature.
        max_tokens: Maximum tokens to generate.

    Returns:
        Configured AnthropicModel instance.

    Example:
        >>> model = create_anthropic_model()
        >>> model = create_anthropic_model("claude-opus-4-6", temperature=0.9)
    """
    config = ModelConfig(
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return AnthropicModel(
        api_key=api_key,
        model=model,
        config=config,
    )


__all__ = [
    "AVAILABLE_ANTHROPIC_MODELS",
    "DEFAULT_ANTHROPIC_MODEL",
    "AnthropicModel",
    "create_anthropic_model",
]
