"""Tests for LLM provider modules — targeting init, error handling, and factories."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from personaut.models.model import (
    AuthenticationError,
    InvalidRequestError,
    ModelConfig,
    ModelError,
    RateLimitError,
)


# ── Gemini ──────────────────────────────────────────────────────────


class TestGeminiModel:
    """Tests for GeminiModel."""

    def test_init_with_api_key(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="test-key")
        assert model.api_key == "test-key"
        assert model.model_name == "gemini-2.0-flash"
        assert model.provider == "gemini"

    def test_init_from_env(self) -> None:
        from personaut.models.gemini import GeminiModel

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key"}):
            model = GeminiModel()
            assert model.api_key == "env-key"

    def test_init_no_key_raises(self) -> None:
        from personaut.models.gemini import GeminiModel

        env = {k: v for k, v in os.environ.items() if k != "GOOGLE_API_KEY"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(AuthenticationError, match="API key"):
            GeminiModel()

    def test_custom_model(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="key", model="gemini-1.5-pro")
        assert model.model_name == "gemini-1.5-pro"
        assert model.config.model_name == "gemini-1.5-pro"

    def test_ensure_client_caches(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="key")
        mock_client = MagicMock()
        model._client = mock_client
        assert model._ensure_client() is mock_client

    def test_handle_error_rate_limit(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="key")
        with pytest.raises(RateLimitError):
            model._handle_error(Exception("Rate limit exceeded"))

    def test_handle_error_auth(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="key")
        with pytest.raises(AuthenticationError):
            model._handle_error(Exception("API key invalid"))

    def test_handle_error_invalid_request(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="key")
        with pytest.raises(InvalidRequestError):
            model._handle_error(Exception("Bad request"))

    def test_handle_error_generic(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="key")
        with pytest.raises(ModelError):
            model._handle_error(Exception("Something went wrong"))

    def test_schema_to_json_schema_dataclass(self) -> None:
        from personaut.models.gemini import GeminiModel

        @dataclass
        class TestSchema:
            name: str
            age: int

        model = GeminiModel(api_key="key")
        result = model._schema_to_json_schema(TestSchema)
        data = json.loads(result)
        assert "name" in data
        assert "age" in data

    def test_schema_to_json_schema_pydantic(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="key")

        class MockPydantic:
            @staticmethod
            def model_json_schema() -> dict:
                return {"type": "object", "properties": {"name": {"type": "string"}}}

        result = model._schema_to_json_schema(MockPydantic)
        assert "name" in result

    def test_schema_to_json_schema_fallback(self) -> None:
        from personaut.models.gemini import GeminiModel

        model = GeminiModel(api_key="key")
        result = model._schema_to_json_schema(str)
        assert isinstance(result, str)

    def test_create_gemini_model_factory(self) -> None:
        from personaut.models.gemini import create_gemini_model

        model = create_gemini_model(api_key="key", temperature=0.9, max_tokens=4096)
        assert model.model == "gemini-2.0-flash"
        assert model.config.temperature == 0.9
        assert model.config.max_tokens == 4096


# ── OpenAI ──────────────────────────────────────────────────────────


class TestOpenAIModel:
    """Tests for OpenAIModel."""

    def test_init_with_api_key(self) -> None:
        from personaut.models.openai import OpenAIModel

        model = OpenAIModel(api_key="test-key")
        assert model.api_key == "test-key"
        assert model.provider == "openai"

    def test_init_from_env(self) -> None:
        from personaut.models.openai import OpenAIModel

        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            model = OpenAIModel()
            assert model.api_key == "env-key"

    def test_init_no_key_raises(self) -> None:
        from personaut.models.openai import OpenAIModel

        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(AuthenticationError, match="API key"):
            OpenAIModel()

    def test_handle_error_rate_limit(self) -> None:
        from personaut.models.openai import OpenAIModel

        model = OpenAIModel(api_key="key")
        with pytest.raises(RateLimitError):
            model._handle_error(Exception("Rate limit"))

    def test_handle_error_auth(self) -> None:
        from personaut.models.openai import OpenAIModel

        model = OpenAIModel(api_key="key")
        with pytest.raises(AuthenticationError):
            model._handle_error(Exception("Unauthorized access"))

    def test_handle_error_invalid(self) -> None:
        from personaut.models.openai import OpenAIModel

        model = OpenAIModel(api_key="key")
        with pytest.raises(InvalidRequestError):
            model._handle_error(Exception("Invalid input"))

    def test_handle_error_generic(self) -> None:
        from personaut.models.openai import OpenAIModel

        model = OpenAIModel(api_key="key")
        with pytest.raises(ModelError):
            model._handle_error(Exception("Unknown"))

    def test_ensure_client_caches(self) -> None:
        from personaut.models.openai import OpenAIModel

        model = OpenAIModel(api_key="key")
        mock_client = MagicMock()
        model._client = mock_client
        assert model._ensure_client() is mock_client

    def test_create_openai_model_factory(self) -> None:
        from personaut.models.openai import create_openai_model

        model = create_openai_model(api_key="key", temperature=0.5)
        assert model.config.temperature == 0.5


# ── Ollama ──────────────────────────────────────────────────────────


class TestOllamaModel:
    """Tests for OllamaModel."""

    def test_init_defaults(self) -> None:
        from personaut.models.ollama import OllamaModel

        model = OllamaModel()
        assert model.provider == "ollama"
        assert model.host == "http://localhost:11434"
        assert model.model_name == "llama3.2"

    def test_init_custom_host(self) -> None:
        from personaut.models.ollama import OllamaModel

        model = OllamaModel(host="http://custom:1234")
        assert model.host == "http://custom:1234"

    def test_handle_error_not_found(self) -> None:
        from personaut.models.ollama import OllamaModel

        model = OllamaModel()
        with pytest.raises(InvalidRequestError, match="not found"):
            model._handle_error(Exception("404 not found"))

    def test_handle_error_generic(self) -> None:
        from personaut.models.ollama import OllamaModel

        model = OllamaModel()
        with pytest.raises(ModelError):
            model._handle_error(Exception("Connection refused"))

    def test_custom_model_config(self) -> None:
        from personaut.models.ollama import OllamaModel

        model = OllamaModel(
            model="mistral",
            config=ModelConfig(model_name="mistral", temperature=0.5),
        )
        assert model.model_name == "mistral"
        assert model.config.temperature == 0.5

    def test_create_ollama_model_factory(self) -> None:
        from personaut.models.ollama import create_ollama_model

        model = create_ollama_model(model="llama3", temperature=0.8)
        assert model.model == "llama3"
        assert model.config.temperature == 0.8


# ── Bedrock ─────────────────────────────────────────────────────────


class TestBedrockModel:
    """Tests for BedrockModel."""

    def test_init_defaults(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel()
        assert model.provider == "bedrock"
        assert model.region == "us-east-1"

    def test_init_custom_model(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="claude-3-opus")
        assert "claude-3-opus" in model.model_name

    def test_init_full_model_id(self) -> None:
        from personaut.models.bedrock import BedrockModel

        full_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        model = BedrockModel(model=full_id)
        assert model.model_name == full_id

    def test_handle_error_throttle(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel()
        with pytest.raises(RateLimitError):
            model._handle_error(Exception("Throttling exception"))

    def test_handle_error_access_denied(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel()
        with pytest.raises(AuthenticationError):
            model._handle_error(Exception("Access denied"))

    def test_handle_error_validation(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel()
        with pytest.raises(InvalidRequestError):
            model._handle_error(Exception("Validation error"))

    def test_handle_error_generic(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel()
        with pytest.raises(ModelError):
            model._handle_error(Exception("Something else"))

    def test_ensure_client_caches(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel()
        mock_client = MagicMock()
        model._client = mock_client
        assert model._ensure_client() is mock_client

    def test_build_request_body_claude(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="claude-3-5-haiku")
        body = model._build_request_body("Hello", 0.7, 1024)
        assert "anthropic_version" in body
        assert body["messages"][0]["content"] == "Hello"

    def test_build_request_body_claude_stop_seqs(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="claude-3-5-haiku")
        body = model._build_request_body("Hello", 0.7, 1024, stop_sequences=["END"])
        assert body["stop_sequences"] == ["END"]

    def test_build_request_body_llama(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="llama-3-2-90b")
        body = model._build_request_body("Hello", 0.7, 1024)
        assert "prompt" in body
        assert "max_gen_len" in body

    def test_build_request_body_mistral(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="mistral-large")
        body = model._build_request_body("Hello", 0.7, 1024)
        assert "[INST]" in body["prompt"]

    def test_build_request_body_generic(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="unknown.model.v1.0:0")
        body = model._build_request_body("Hello", 0.7, 1024)
        assert "inputText" in body

    def test_parse_response_claude(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="claude-3-5-haiku")
        resp = {
            "content": [{"text": "Hello!"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "stop_reason": "end_turn",
        }
        result = model._parse_response(resp)
        assert result.text == "Hello!"
        assert result.usage["prompt_tokens"] == 10

    def test_parse_response_claude_empty(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="claude-3-5-haiku")
        result = model._parse_response({"content": []})
        assert result.text == ""

    def test_parse_response_llama(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="llama-3-2-90b")
        resp = {"generation": "Output text"}
        result = model._parse_response(resp)
        assert result.text == "Output text"

    def test_parse_response_mistral(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="mistral-large")
        resp = {"outputs": [{"text": "Mistral output", "stop_reason": "stop"}]}
        result = model._parse_response(resp)
        assert result.text == "Mistral output"

    def test_parse_response_mistral_empty(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="mistral-large")
        result = model._parse_response({"outputs": []})
        assert result.text == ""

    def test_parse_response_generic(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="unknown.model.v1.0:0")
        resp = {"results": [{"outputText": "Generic output"}]}
        result = model._parse_response(resp)
        assert result.text == "Generic output"

    def test_extract_stream_text_claude(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="claude-3-5-haiku")
        chunk = {"type": "content_block_delta", "delta": {"text": "Hello"}}
        assert model._extract_stream_text(chunk) == "Hello"

    def test_extract_stream_text_claude_non_delta(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="claude-3-5-haiku")
        chunk = {"type": "other_type"}
        assert model._extract_stream_text(chunk) == ""

    def test_extract_stream_text_llama(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="llama-3-2-90b")
        chunk = {"generation": "text"}
        assert model._extract_stream_text(chunk) == "text"

    def test_extract_stream_text_mistral(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="mistral-large")
        chunk = {"outputs": [{"text": "chunk"}]}
        assert model._extract_stream_text(chunk) == "chunk"

    def test_extract_stream_text_unknown(self) -> None:
        from personaut.models.bedrock import BedrockModel

        model = BedrockModel(model="unknown.model.v1.0:0")
        assert model._extract_stream_text({}) == ""

    def test_create_bedrock_model_factory(self) -> None:
        from personaut.models.bedrock import create_bedrock_model

        model = create_bedrock_model(temperature=0.6, max_tokens=4096)
        assert model.config.temperature == 0.6
        assert model.config.max_tokens == 4096

    def test_get_model_id_shorthand(self) -> None:
        from personaut.models.bedrock import _get_model_id

        result = _get_model_id("claude-3-5-sonnet")
        assert "anthropic" in result and "sonnet" in result

    def test_get_model_id_full(self) -> None:
        from personaut.models.bedrock import _get_model_id

        full_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert _get_model_id(full_id) == full_id

    def test_get_model_id_unknown(self) -> None:
        from personaut.models.bedrock import DEFAULT_BEDROCK_MODEL, _get_model_id

        assert _get_model_id("nonexistent") == DEFAULT_BEDROCK_MODEL
