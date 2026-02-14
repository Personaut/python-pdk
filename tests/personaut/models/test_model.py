"""Tests for the model base interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar

from personaut.models.model import (
    AuthenticationError,
    GenerationResult,
    InvalidRequestError,
    Model,
    ModelConfig,
    ModelError,
    RateLimitError,
)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ModelConfig(model_name="test-model")
        assert config.model_name == "test-model"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.top_p == 0.95
        assert config.top_k == 40
        assert config.stop_sequences == []
        assert config.timeout == 30.0
        assert config.extra == {}

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = ModelConfig(
            model_name="custom-model",
            temperature=0.9,
            max_tokens=4096,
            top_p=0.8,
            stop_sequences=["END"],
            timeout=60.0,
            extra={"custom_key": "value"},
        )
        assert config.model_name == "custom-model"
        assert config.temperature == 0.9
        assert config.max_tokens == 4096
        assert config.top_p == 0.8
        assert config.stop_sequences == ["END"]
        assert config.timeout == 60.0
        assert config.extra == {"custom_key": "value"}


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_default_result(self) -> None:
        """Test default result values."""
        result = GenerationResult(text="Hello, world!")
        assert result.text == "Hello, world!"
        assert result.finish_reason == "stop"
        assert result.usage == {}
        assert result.model == ""
        assert result.raw_response is None

    def test_result_with_usage(self) -> None:
        """Test result with usage information."""
        usage = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }
        result = GenerationResult(
            text="Generated text",
            finish_reason="max_tokens",
            usage=usage,
            model="test-model",
        )
        assert result.text == "Generated text"
        assert result.finish_reason == "max_tokens"
        assert result.usage == usage
        assert result.model == "test-model"


class TestModelErrors:
    """Tests for model error classes."""

    def test_model_error(self) -> None:
        """Test basic ModelError."""
        error = ModelError(
            "Test error",
            provider="test",
            model="test-model",
        )
        assert str(error) == "Test error"
        assert error.provider == "test"
        assert error.model == "test-model"
        assert error.cause is None

    def test_rate_limit_error(self) -> None:
        """Test RateLimitError is a ModelError."""
        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, ModelError)
        assert str(error) == "Rate limit exceeded"

    def test_authentication_error(self) -> None:
        """Test AuthenticationError is a ModelError."""
        error = AuthenticationError("Invalid API key")
        assert isinstance(error, ModelError)
        assert str(error) == "Invalid API key"

    def test_invalid_request_error(self) -> None:
        """Test InvalidRequestError is a ModelError."""
        error = InvalidRequestError("Bad request")
        assert isinstance(error, ModelError)
        assert str(error) == "Bad request"

    def test_error_with_cause(self) -> None:
        """Test error with wrapped cause."""
        cause = ValueError("Original error")
        error = ModelError("Wrapped error", cause=cause)
        assert error.cause is cause


T = TypeVar("T")


class MockModel(Model):
    """Mock model implementation for testing."""

    def __init__(self, response_text: str = "Mock response"):
        self._response_text = response_text

    @property
    def model_name(self) -> str:
        return "mock-model"

    @property
    def provider(self) -> str:
        return "mock"

    def generate(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        return GenerationResult(
            text=self._response_text,
            model=self.model_name,
        )

    def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> T:
        # Simple mock that creates schema with default values
        return schema()  # type: ignore


class TestModelProtocol:
    """Tests for Model protocol implementation."""

    def test_mock_model_properties(self) -> None:
        """Test Model properties."""
        model = MockModel()
        assert model.model_name == "mock-model"
        assert model.provider == "mock"

    def test_mock_model_generate(self) -> None:
        """Test Model.generate method."""
        model = MockModel(response_text="Test output")
        result = model.generate("Test prompt")
        assert result.text == "Test output"
        assert result.model == "mock-model"

    def test_mock_model_generate_stream(self) -> None:
        """Test Model.generate_stream default implementation."""
        model = MockModel(response_text="Streaming output")
        chunks = list(model.generate_stream("Test prompt"))
        assert chunks == ["Streaming output"]

    def test_mock_model_generate_structured(self) -> None:
        """Test Model.generate_structured method."""

        @dataclass
        class TestSchema:
            name: str = "default"
            value: int = 0

        model = MockModel()
        result = model.generate_structured("Test prompt", TestSchema)
        assert isinstance(result, TestSchema)
        assert result.name == "default"
        assert result.value == 0
