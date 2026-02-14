"""Gemini model provider for Personaut PDK.

This module provides Google Gemini integration for LLM text generation.
Note: Embeddings are handled by the local embedding model for consistency.

Example:
    >>> from personaut.models import GeminiModel
    >>>
    >>> model = GeminiModel()  # Uses GOOGLE_API_KEY env var
    >>> result = model.generate("Explain quantum computing")
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

# Default Gemini models
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
AVAILABLE_GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]


@dataclass
class GeminiModel(Model):
    """Google Gemini model implementation.

    This class provides access to Gemini models for text generation.
    Authentication is via the GOOGLE_API_KEY environment variable or
    explicit api_key parameter.

    Attributes:
        api_key: Google API key. If None, uses GOOGLE_API_KEY env var.
        model: Gemini model name.
        config: Model configuration.

    Example:
        >>> model = GeminiModel()
        >>> result = model.generate("Write a haiku about AI")
        >>> print(result.text)

        >>> # With custom config
        >>> model = GeminiModel(
        ...     model="gemini-1.5-pro",
        ...     config=ModelConfig(temperature=0.9, max_tokens=4096),
        ... )
    """

    api_key: str | None = None
    model: str = DEFAULT_GEMINI_MODEL
    config: ModelConfig = field(default_factory=lambda: ModelConfig(model_name=DEFAULT_GEMINI_MODEL))

    # Private fields
    _client: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize the Gemini client."""
        # Get API key from environment if not provided
        if self.api_key is None:
            self.api_key = os.environ.get("GOOGLE_API_KEY")

        if not self.api_key:
            msg = "Google API key required. Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            raise AuthenticationError(msg, provider="gemini")

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
        return "gemini"

    def _ensure_client(self) -> Any:
        """Ensure the Gemini client is initialized."""
        if self._client is not None:
            return self._client

        try:
            from google import genai
        except ImportError as e:
            msg = "google-genai is required for Gemini models. Install with: pip install google-genai"
            raise ModelError(msg, provider="gemini", cause=e) from e

        self._client = genai.Client(api_key=self.api_key)
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
        from google.genai import types

        client = self._ensure_client()

        # Build generation config
        gen_config = types.GenerateContentConfig(
            temperature=temperature or self.config.temperature,
            max_output_tokens=max_tokens or self.config.max_tokens,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            stop_sequences=stop_sequences or self.config.stop_sequences or None,
        )

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=gen_config,
            )

            # Extract text and metadata
            text = response.text if hasattr(response, "text") else ""

            # Get usage if available
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }

            # Get finish reason
            finish_reason = "stop"
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    finish_reason = str(candidate.finish_reason).lower()

            return GenerationResult(
                text=text,
                finish_reason=finish_reason,
                usage=usage,
                model=self.model,
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
        # Build a prompt asking for JSON output
        schema_prompt = f"""
{prompt}

Respond ONLY with valid JSON matching this schema:
{self._schema_to_json_schema(schema)}

Output JSON only, no other text.
"""

        result = self.generate(
            schema_prompt,
            temperature=temperature or 0.3,  # Lower temp for structured output
            max_tokens=max_tokens,
            **kwargs,
        )

        # Parse the response
        try:
            # Clean up the response (remove markdown code blocks if present)
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
            raise InvalidRequestError(msg, provider="gemini", model=self.model, cause=e) from e

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
        from google.genai import types

        client = self._ensure_client()

        gen_config = types.GenerateContentConfig(
            temperature=temperature or self.config.temperature,
            max_output_tokens=max_tokens or self.config.max_tokens,
        )

        try:
            for chunk in client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=gen_config,
            ):
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

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

        # Try Pydantic
        if hasattr(schema, "model_json_schema"):
            return json.dumps(schema.model_json_schema(), indent=2)

        # Fallback
        return str(schema)

    def _handle_error(self, e: Exception) -> NoReturn:
        """Convert Gemini exceptions to ModelError types."""
        error_str = str(e).lower()

        if "rate" in error_str or "quota" in error_str:
            raise RateLimitError(str(e), provider="gemini", model=self.model, cause=e) from e
        elif "api key" in error_str or "unauthorized" in error_str:
            raise AuthenticationError(str(e), provider="gemini", model=self.model, cause=e) from e
        elif "invalid" in error_str or "bad request" in error_str:
            raise InvalidRequestError(str(e), provider="gemini", model=self.model, cause=e) from e
        else:
            raise ModelError(str(e), provider="gemini", model=self.model, cause=e) from e


def create_gemini_model(
    model: str = DEFAULT_GEMINI_MODEL,
    api_key: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> GeminiModel:
    """Create a Gemini model with configuration.

    Args:
        model: Gemini model name.
        api_key: Google API key (or use GOOGLE_API_KEY env var).
        temperature: Generation temperature.
        max_tokens: Maximum tokens to generate.

    Returns:
        Configured GeminiModel instance.

    Example:
        >>> model = create_gemini_model()
        >>> model = create_gemini_model("gemini-1.5-pro", temperature=0.9)
    """
    config = ModelConfig(
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return GeminiModel(
        api_key=api_key,
        model=model,
        config=config,
    )


__all__ = [
    "AVAILABLE_GEMINI_MODELS",
    "DEFAULT_GEMINI_MODEL",
    "GeminiModel",
    "create_gemini_model",
]
