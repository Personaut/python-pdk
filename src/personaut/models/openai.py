"""OpenAI model provider for Personaut PDK.

This module provides OpenAI integration for LLM text generation.
Note: Embeddings are handled by the local embedding model for consistency.

Example:
    >>> from personaut.models import OpenAIModel
    >>>
    >>> model = OpenAIModel()  # Uses OPENAI_API_KEY env var
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

# Default OpenAI models
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
AVAILABLE_OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "o1",
    "o1-mini",
    "o1-preview",
]


@dataclass
class OpenAIModel(Model):
    """OpenAI model implementation.

    This class provides access to OpenAI models including GPT-4, GPT-4o,
    and o1 models. Authentication is via the OPENAI_API_KEY environment
    variable or explicit api_key parameter.

    Attributes:
        api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        model: OpenAI model name.
        config: Model configuration.
        organization: Optional OpenAI organization ID.

    Example:
        >>> model = OpenAIModel()
        >>> result = model.generate("Explain neural networks")
        >>> print(result.text)

        >>> # With custom config
        >>> model = OpenAIModel(
        ...     model="gpt-4o",
        ...     config=ModelConfig(temperature=0.9, max_tokens=4096),
        ... )
    """

    api_key: str | None = None
    model: str = DEFAULT_OPENAI_MODEL
    config: ModelConfig = field(default_factory=lambda: ModelConfig(model_name=DEFAULT_OPENAI_MODEL))
    organization: str | None = None

    # Private fields
    _client: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize the OpenAI client."""
        # Get API key from environment if not provided
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            msg = "OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            raise AuthenticationError(msg, provider="openai")

        # Get organization from environment if not provided
        if self.organization is None:
            self.organization = os.environ.get("OPENAI_ORGANIZATION")

        # Update config model name
        self.config = ModelConfig(
            model_name=self.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
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
        return "openai"

    def _ensure_client(self) -> Any:
        """Ensure the OpenAI client is initialized."""
        if self._client is not None:
            return self._client

        try:
            from openai import OpenAI
        except ImportError as e:
            msg = "openai is required for OpenAI models. Install with: pip install openai"
            raise ModelError(msg, provider="openai", cause=e) from e

        self._client = OpenAI(
            api_key=self.api_key,
            organization=self.organization,
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

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Handle system message if provided
        system = kwargs.pop("system", None)
        if system:
            messages.insert(0, {"role": "system", "content": system})

        # Build generation parameters
        gen_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        # o1 models don't support temperature or max_tokens the same way
        if not self.model.startswith("o1"):
            gen_kwargs["temperature"] = temperature or self.config.temperature
            if max_tokens or self.config.max_tokens:
                gen_kwargs["max_tokens"] = max_tokens or self.config.max_tokens
            if stop_sequences or self.config.stop_sequences:
                gen_kwargs["stop"] = stop_sequences or self.config.stop_sequences
        else:
            # o1 models use max_completion_tokens
            if max_tokens or self.config.max_tokens:
                gen_kwargs["max_completion_tokens"] = max_tokens or self.config.max_tokens

        try:
            response = client.chat.completions.create(**gen_kwargs)

            # Extract text and metadata
            choice = response.choices[0]
            text = choice.message.content or ""

            # Get usage
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return GenerationResult(
                text=text,
                finish_reason=choice.finish_reason or "stop",
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
        # Try to use OpenAI's native structured output if available
        client = self._ensure_client()

        # Check if schema is a Pydantic model (OpenAI supports these natively)
        if hasattr(schema, "model_json_schema") and not self.model.startswith("o1"):
            try:
                response = client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format=schema,
                    temperature=temperature or 0.3,
                )
                # Cast to T since OpenAI's parse returns the correct type
                parsed = response.choices[0].message.parsed
                if parsed is not None:
                    return parsed  # type: ignore[no-any-return]
            except Exception:
                pass  # Fall back to manual parsing

        # Manual JSON parsing
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
            raise InvalidRequestError(msg, provider="openai", model=self.model, cause=e) from e

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

        messages = [{"role": "user", "content": prompt}]
        system = kwargs.pop("system", None)
        if system:
            messages.insert(0, {"role": "system", "content": system})

        gen_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        if not self.model.startswith("o1"):
            gen_kwargs["temperature"] = temperature or self.config.temperature
            if max_tokens or self.config.max_tokens:
                gen_kwargs["max_tokens"] = max_tokens or self.config.max_tokens

        try:
            stream = client.chat.completions.create(**gen_kwargs)
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

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
        """Convert OpenAI exceptions to ModelError types."""
        error_str = str(e).lower()
        error_type = type(e).__name__.lower()

        if "rate" in error_str or "ratelimit" in error_type:
            raise RateLimitError(str(e), provider="openai", model=self.model, cause=e) from e
        elif "auth" in error_str or "api key" in error_str:
            raise AuthenticationError(str(e), provider="openai", model=self.model, cause=e) from e
        elif "invalid" in error_str or "bad request" in error_type:
            raise InvalidRequestError(str(e), provider="openai", model=self.model, cause=e) from e
        else:
            raise ModelError(str(e), provider="openai", model=self.model, cause=e) from e


def create_openai_model(
    model: str = DEFAULT_OPENAI_MODEL,
    api_key: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> OpenAIModel:
    """Create an OpenAI model with configuration.

    Args:
        model: OpenAI model name.
        api_key: OpenAI API key (or use OPENAI_API_KEY env var).
        temperature: Generation temperature.
        max_tokens: Maximum tokens to generate.

    Returns:
        Configured OpenAIModel instance.

    Example:
        >>> model = create_openai_model()
        >>> model = create_openai_model("gpt-4o", temperature=0.9)
    """
    config = ModelConfig(
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return OpenAIModel(
        api_key=api_key,
        model=model,
        config=config,
    )


__all__ = [
    "AVAILABLE_OPENAI_MODELS",
    "DEFAULT_OPENAI_MODEL",
    "OpenAIModel",
    "create_openai_model",
]
