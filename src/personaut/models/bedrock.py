"""AWS Bedrock model provider for Personaut PDK.

This module provides AWS Bedrock integration for LLM text generation,
supporting Claude, Llama, and Mistral models.
Note: Embeddings are handled by the local embedding model for consistency.

Example:
    >>> from personaut.models import BedrockModel
    >>>
    >>> model = BedrockModel()  # Uses default AWS credentials
    >>> result = model.generate("Explain machine learning")
    >>> print(result.text)
"""

from __future__ import annotations

import json
import logging
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

# Default Bedrock models
DEFAULT_BEDROCK_MODEL = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

# Available Bedrock models by provider
BEDROCK_MODELS = {
    # Claude models (cross-region inference)
    "claude-3-5-sonnet": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "claude-3-5-haiku": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "claude-3-opus": "us.anthropic.claude-3-opus-20240229-v1:0",
    "claude-3-sonnet": "us.anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3-haiku": "us.anthropic.claude-3-haiku-20240307-v1:0",
    # Llama models
    "llama-3-2-90b": "us.meta.llama3-2-90b-instruct-v1:0",
    "llama-3-2-11b": "us.meta.llama3-2-11b-instruct-v1:0",
    "llama-3-2-3b": "us.meta.llama3-2-3b-instruct-v1:0",
    "llama-3-2-1b": "us.meta.llama3-2-1b-instruct-v1:0",
    # Mistral models
    "mistral-large": "mistral.mistral-large-2407-v1:0",
    "mistral-small": "mistral.mistral-small-2402-v1:0",
    "mixtral-8x7b": "mistral.mixtral-8x7b-instruct-v0:1",
}


def _get_model_id(model: str) -> str:
    """Resolve model name to full Bedrock model ID."""
    # If it's already a full model ID, use it
    if "." in model and ":" in model:
        return model
    # Look up in our mapping
    return BEDROCK_MODELS.get(model, DEFAULT_BEDROCK_MODEL)


@dataclass
class BedrockModel(Model):
    """AWS Bedrock model implementation.

    This class provides access to Bedrock models including Claude, Llama,
    and Mistral. Authentication uses standard AWS credentials (environment
    variables, IAM roles, or explicit credentials).

    Attributes:
        model: Bedrock model name or shorthand.
        region: AWS region for Bedrock.
        config: Model configuration.

    Example:
        >>> model = BedrockModel()
        >>> result = model.generate("Write a poem about clouds")
        >>> print(result.text)

        >>> # Use a specific model
        >>> model = BedrockModel(model="claude-3-opus")
    """

    model: str = DEFAULT_BEDROCK_MODEL
    region: str = "us-east-1"
    config: ModelConfig = field(default_factory=lambda: ModelConfig(model_name=DEFAULT_BEDROCK_MODEL))

    # Private fields
    _client: Any = field(default=None, repr=False, compare=False)
    _model_id: str = field(default="", repr=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize the Bedrock client."""
        # Resolve model ID
        self._model_id = _get_model_id(self.model)

        # Update config
        self.config = ModelConfig(
            model_name=self._model_id,
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
        return self._model_id

    @property
    def provider(self) -> str:
        """The provider name."""
        return "bedrock"

    def _ensure_client(self) -> Any:
        """Ensure the Bedrock client is initialized."""
        if self._client is not None:
            return self._client

        try:
            import boto3
        except ImportError as e:
            msg = "boto3 is required for Bedrock models. Install with: pip install personaut[bedrock]"
            raise ModelError(msg, provider="bedrock", cause=e) from e

        try:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
            )
            return self._client
        except Exception as e:
            msg = f"Failed to initialize Bedrock client: {e}"
            raise AuthenticationError(msg, provider="bedrock", model=self._model_id, cause=e) from e

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

        # Build request body based on model type
        body = self._build_request_body(
            prompt=prompt,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            stop_sequences=stop_sequences or self.config.stop_sequences,
        )

        try:
            response = client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            # Parse response based on model type
            response_body = json.loads(response["body"].read())
            return self._parse_response(response_body)

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
            temperature=temperature or 0.3,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Parse the response
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
            raise InvalidRequestError(msg, provider="bedrock", model=self._model_id, cause=e) from e

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

        body = self._build_request_body(
            prompt=prompt,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )

        try:
            response = client.invoke_model_with_response_stream(
                modelId=self._model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            stream = response.get("body")
            if stream:
                for event in stream:
                    chunk = event.get("chunk")
                    if chunk:
                        chunk_data = json.loads(chunk.get("bytes"))
                        text = self._extract_stream_text(chunk_data)
                        if text:
                            yield text

        except Exception as e:
            self._handle_error(e)

    def _build_request_body(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop_sequences: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build request body based on model provider."""
        model_lower = self._model_id.lower()

        if "anthropic" in model_lower or "claude" in model_lower:
            # Claude format
            body: dict[str, Any] = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if stop_sequences:
                body["stop_sequences"] = stop_sequences
            return body

        elif "meta" in model_lower or "llama" in model_lower:
            # Llama format
            return {
                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>",
                "max_gen_len": max_tokens,
                "temperature": temperature,
            }

        elif "mistral" in model_lower:
            # Mistral format
            return {
                "prompt": f"<s>[INST] {prompt} [/INST]",
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

        else:
            # Generic format
            return {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                },
            }

    def _parse_response(self, response: dict[str, Any]) -> GenerationResult:
        """Parse response based on model provider."""
        model_lower = self._model_id.lower()

        if "anthropic" in model_lower or "claude" in model_lower:
            # Claude response
            content = response.get("content", [])
            text = content[0].get("text", "") if content else ""
            usage = {
                "prompt_tokens": response.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response.get("usage", {}).get("output_tokens", 0),
            }
            return GenerationResult(
                text=text,
                finish_reason=response.get("stop_reason", "stop"),
                usage=usage,
                model=self._model_id,
                raw_response=response,
            )

        elif "meta" in model_lower or "llama" in model_lower:
            # Llama response
            return GenerationResult(
                text=response.get("generation", ""),
                finish_reason=response.get("stop_reason", "stop"),
                model=self._model_id,
                raw_response=response,
            )

        elif "mistral" in model_lower:
            # Mistral response
            outputs = response.get("outputs", [])
            text = outputs[0].get("text", "") if outputs else ""
            return GenerationResult(
                text=text,
                finish_reason=outputs[0].get("stop_reason", "stop") if outputs else "stop",
                model=self._model_id,
                raw_response=response,
            )

        else:
            # Generic response
            results = response.get("results", [{}])
            return GenerationResult(
                text=results[0].get("outputText", ""),
                model=self._model_id,
                raw_response=response,
            )

    def _extract_stream_text(self, chunk: dict[str, Any]) -> str:
        """Extract text from streaming chunk."""
        model_lower = self._model_id.lower()

        if "anthropic" in model_lower or "claude" in model_lower:
            if chunk.get("type") == "content_block_delta":
                return str(chunk.get("delta", {}).get("text", ""))
        elif "meta" in model_lower or "llama" in model_lower:
            return str(chunk.get("generation", ""))
        elif "mistral" in model_lower:
            outputs = chunk.get("outputs", [])
            return str(outputs[0].get("text", "")) if outputs else ""
        return ""

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
        """Convert Bedrock exceptions to ModelError types."""
        error_str = str(e).lower()

        if "throttling" in error_str or "rate" in error_str:
            raise RateLimitError(str(e), provider="bedrock", model=self._model_id, cause=e) from e
        elif "access denied" in error_str or "unauthorized" in error_str:
            raise AuthenticationError(str(e), provider="bedrock", model=self._model_id, cause=e) from e
        elif "validation" in error_str or "invalid" in error_str:
            raise InvalidRequestError(str(e), provider="bedrock", model=self._model_id, cause=e) from e
        else:
            raise ModelError(str(e), provider="bedrock", model=self._model_id, cause=e) from e


def create_bedrock_model(
    model: str = "claude-3-5-haiku",
    region: str = "us-east-1",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> BedrockModel:
    """Create a Bedrock model with configuration.

    Args:
        model: Model name or shorthand (e.g., "claude-3-5-sonnet", "llama-3-2-90b").
        region: AWS region.
        temperature: Generation temperature.
        max_tokens: Maximum tokens to generate.

    Returns:
        Configured BedrockModel instance.

    Example:
        >>> model = create_bedrock_model()
        >>> model = create_bedrock_model("claude-3-opus", temperature=0.9)
    """
    config = ModelConfig(
        model_name=_get_model_id(model),
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return BedrockModel(
        model=model,
        region=region,
        config=config,
    )


__all__ = [
    "BEDROCK_MODELS",
    "DEFAULT_BEDROCK_MODEL",
    "BedrockModel",
    "create_bedrock_model",
]
