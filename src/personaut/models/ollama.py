"""Ollama local LLM provider for Personaut PDK.

This module provides Ollama integration for local LLM text generation.
Ollama allows running models like Llama, Mistral, and others locally.

Example:
    >>> from personaut.models import OllamaModel
    >>>
    >>> model = OllamaModel()  # Connects to localhost:11434
    >>> result = model.generate("Explain gravity")
    >>> print(result.text)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar

from personaut.models.model import (
    GenerationResult,
    InvalidRequestError,
    Model,
    ModelConfig,
    ModelError,
)


if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default Ollama settings
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2"


@dataclass
class OllamaModel(Model):
    """Ollama local model implementation.

    This class provides access to locally-running models via Ollama.
    It auto-detects the Ollama server and supports streaming responses.

    Attributes:
        model: Ollama model name (e.g., "llama3.2", "mistral").
        host: Ollama server URL.
        config: Model configuration.

    Example:
        >>> model = OllamaModel()
        >>> result = model.generate("What is the meaning of life?")
        >>> print(result.text)

        >>> # Use a specific model
        >>> model = OllamaModel(model="mistral")
    """

    model: str = DEFAULT_OLLAMA_MODEL
    host: str = DEFAULT_OLLAMA_HOST
    config: ModelConfig = field(default_factory=lambda: ModelConfig(model_name=DEFAULT_OLLAMA_MODEL))

    # Private fields
    _available: bool | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize configuration."""
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
        return "ollama"

    def is_available(self) -> bool:
        """Check if Ollama server is available.

        Returns:
            True if the server is reachable.
        """
        if self._available is not None:
            return self._available

        try:
            import httpx

            response = httpx.get(f"{self.host}/api/version", timeout=5.0)
            self._available = response.status_code == 200
        except Exception:
            self._available = False

        return self._available

    def list_models(self) -> list[str]:
        """List available models on the Ollama server.

        Returns:
            List of model names.

        Raises:
            ModelError: If the request fails.
        """
        try:
            import httpx
        except ImportError as e:
            msg = "httpx is required for Ollama. Install with: pip install httpx"
            raise ModelError(msg, provider="ollama", cause=e) from e

        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            msg = f"Failed to list Ollama models: {e}"
            raise ModelError(msg, provider="ollama", cause=e) from e

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
        try:
            import httpx
        except ImportError as e:
            msg = "httpx is required for Ollama. Install with: pip install httpx"
            raise ModelError(msg, provider="ollama", cause=e) from e

        # Build request body
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
            },
        }

        if max_tokens or self.config.max_tokens:
            body["options"]["num_predict"] = max_tokens or self.config.max_tokens
        if stop_sequences or self.config.stop_sequences:
            body["options"]["stop"] = stop_sequences or self.config.stop_sequences

        # Handle system message
        system = kwargs.pop("system", None)
        if system:
            body["system"] = system

        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json=body,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            data = response.json()

            return GenerationResult(
                text=data.get("response", ""),
                finish_reason="stop" if data.get("done") else "length",
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                },
                model=self.model,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            self._handle_error(e)
        except Exception as e:
            msg = f"Ollama request failed: {e}"
            raise ModelError(msg, provider="ollama", model=self.model, cause=e) from e

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
            raise InvalidRequestError(msg, provider="ollama", model=self.model, cause=e) from e

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
        try:
            import httpx
        except ImportError as e:
            msg = "httpx is required for Ollama. Install with: pip install httpx"
            raise ModelError(msg, provider="ollama", cause=e) from e

        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature or self.config.temperature,
            },
        }

        if max_tokens or self.config.max_tokens:
            body["options"]["num_predict"] = max_tokens or self.config.max_tokens

        system = kwargs.pop("system", None)
        if system:
            body["system"] = system

        try:
            with httpx.stream(
                "POST",
                f"{self.host}/api/generate",
                json=body,
                timeout=self.config.timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if text := data.get("response"):
                            yield text
                        if data.get("done"):
                            break

        except Exception as e:
            msg = f"Ollama streaming failed: {e}"
            raise ModelError(msg, provider="ollama", model=self.model, cause=e) from e

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
        """Convert Ollama exceptions to ModelError types."""
        error_str = str(e).lower()

        if "not found" in error_str or "404" in error_str:
            msg = f"Model '{self.model}' not found. Run: ollama pull {self.model}"
            raise InvalidRequestError(msg, provider="ollama", model=self.model, cause=e) from e
        else:
            raise ModelError(str(e), provider="ollama", model=self.model, cause=e) from e


def create_ollama_model(
    model: str = DEFAULT_OLLAMA_MODEL,
    host: str = DEFAULT_OLLAMA_HOST,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> OllamaModel:
    """Create an Ollama model with configuration.

    Args:
        model: Ollama model name.
        host: Ollama server URL.
        temperature: Generation temperature.
        max_tokens: Maximum tokens to generate.

    Returns:
        Configured OllamaModel instance.

    Example:
        >>> model = create_ollama_model()
        >>> model = create_ollama_model("mistral", temperature=0.9)
    """
    config = ModelConfig(
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return OllamaModel(
        model=model,
        host=host,
        config=config,
    )


__all__ = [
    "DEFAULT_OLLAMA_HOST",
    "DEFAULT_OLLAMA_MODEL",
    "OllamaModel",
    "create_ollama_model",
]
