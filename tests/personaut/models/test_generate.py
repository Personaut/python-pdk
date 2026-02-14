"""Tests for model generate / generate_structured / generate_stream methods.

These tests mock the actual API clients to avoid real LLM calls while
exercising the request-building, response-parsing, and error-handling logic.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from personaut.models.model import (
    GenerationResult,
    InvalidRequestError,
    ModelError,
    RateLimitError,
)


# ── Helpers ─────────────────────────────────────────────────────────


@dataclass
class _SampleSchema:
    name: str
    value: int


def _mock_openai_response(text="Hello", model="gpt-4o-mini", prompt_tokens=10, completion_tokens=5):
    """Build a mock OpenAI ChatCompletion response."""
    choice = SimpleNamespace(
        message=SimpleNamespace(content=text),
        finish_reason="stop",
    )
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    return SimpleNamespace(choices=[choice], usage=usage, model=model)


def _mock_gemini_response(text="Hello", prompt_tokens=10, completion_tokens=5):
    """Build a mock Gemini GenerateContent response."""
    usage = SimpleNamespace(
        prompt_token_count=prompt_tokens,
        candidates_token_count=completion_tokens,
        total_token_count=prompt_tokens + completion_tokens,
    )
    candidate = SimpleNamespace(finish_reason="stop")
    return SimpleNamespace(
        text=text,
        usage_metadata=usage,
        candidates=[candidate],
    )


# ── OpenAI generate ────────────────────────────────────────────────


class TestOpenAIGenerate:
    def _model(self):
        from personaut.models.openai import OpenAIModel

        m = OpenAIModel(api_key="test-key")
        m._client = MagicMock()
        return m

    def test_generate_basic(self) -> None:
        model = self._model()
        model._client.chat.completions.create.return_value = _mock_openai_response()
        result = model.generate("Hello")
        assert isinstance(result, GenerationResult)
        assert result.text == "Hello"
        assert result.usage["total_tokens"] == 15

    def test_generate_with_system(self) -> None:
        model = self._model()
        model._client.chat.completions.create.return_value = _mock_openai_response()
        model.generate("Hi", system="Be helpful")
        call_args = model._client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_generate_with_overrides(self) -> None:
        model = self._model()
        model._client.chat.completions.create.return_value = _mock_openai_response()
        model.generate("Hi", temperature=0.9, max_tokens=500, stop_sequences=["END"])
        call_args = model._client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.9
        assert call_args.kwargs["max_tokens"] == 500
        assert call_args.kwargs["stop"] == ["END"]

    def test_generate_o1_model(self) -> None:
        from personaut.models.openai import OpenAIModel

        model = OpenAIModel(api_key="key", model="o1-mini")
        model._client = MagicMock()
        model._client.chat.completions.create.return_value = _mock_openai_response(model="o1-mini")
        model.generate("Hello", max_tokens=1000)
        call_args = model._client.chat.completions.create.call_args
        assert "temperature" not in call_args.kwargs
        assert call_args.kwargs.get("max_completion_tokens") == 1000

    def test_generate_no_usage(self) -> None:
        model = self._model()
        resp = _mock_openai_response()
        resp.usage = None
        model._client.chat.completions.create.return_value = resp
        result = model.generate("Hi")
        assert result.usage == {}

    def test_generate_error(self) -> None:
        model = self._model()
        model._client.chat.completions.create.side_effect = Exception("Rate limit")
        with pytest.raises(RateLimitError):
            model.generate("Hi")

    def test_generate_structured_json(self) -> None:
        model = self._model()
        json_str = json.dumps({"name": "test", "value": 42})
        model._client.chat.completions.create.return_value = _mock_openai_response(text=json_str)
        result = model.generate_structured("make struct", _SampleSchema)
        assert result.name == "test"
        assert result.value == 42

    def test_generate_structured_json_fenced(self) -> None:
        model = self._model()
        json_str = f"```json\n{json.dumps({'name': 'x', 'value': 1})}\n```"
        model._client.chat.completions.create.return_value = _mock_openai_response(text=json_str)
        result = model.generate_structured("make struct", _SampleSchema)
        assert result.name == "x"

    def test_generate_structured_parse_fail(self) -> None:
        model = self._model()
        model._client.chat.completions.create.return_value = _mock_openai_response(text="not json")
        with pytest.raises(InvalidRequestError, match="parse"):
            model.generate_structured("make struct", _SampleSchema)

    def test_generate_stream(self) -> None:
        model = self._model()
        chunks = [
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hello"))]),
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=" world"))]),
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]),
        ]
        model._client.chat.completions.create.return_value = iter(chunks)
        result = list(model.generate_stream("Hi"))
        assert result == ["Hello", " world"]

    def test_generate_stream_with_system(self) -> None:
        model = self._model()
        model._client.chat.completions.create.return_value = iter([])
        list(model.generate_stream("Hi", system="Sys"))
        call_args = model._client.chat.completions.create.call_args
        assert call_args.kwargs["messages"][0]["role"] == "system"

    def test_organization_from_env(self) -> None:
        from personaut.models.openai import OpenAIModel

        with patch.dict(os.environ, {"OPENAI_API_KEY": "key", "OPENAI_ORGANIZATION": "org123"}):
            model = OpenAIModel()
            assert model.organization == "org123"

    def test_schema_to_json_schema_dataclass(self) -> None:
        model = self._model()
        result = model._schema_to_json_schema(_SampleSchema)
        data = json.loads(result)
        assert "name" in data
        assert "value" in data

    def test_schema_to_json_schema_pydantic(self) -> None:
        model = self._model()

        class Fake:
            @staticmethod
            def model_json_schema():
                return {"type": "object"}

        result = model._schema_to_json_schema(Fake)
        assert "object" in result

    def test_schema_to_json_schema_fallback(self) -> None:
        model = self._model()
        result = model._schema_to_json_schema(int)
        assert isinstance(result, str)


# ── Gemini generate ────────────────────────────────────────────────


class TestGeminiGenerate:
    def _model(self):
        from personaut.models.gemini import GeminiModel

        m = GeminiModel(api_key="test-key")
        m._client = MagicMock()
        return m

    def test_generate_basic(self) -> None:
        model = self._model()
        model._client.models.generate_content.return_value = _mock_gemini_response()
        # Patch the local import of types inside generate()
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            result = model.generate("Hello")
        assert isinstance(result, GenerationResult)
        assert result.text == "Hello"
        assert result.usage["total_tokens"] == 15

    def test_generate_no_usage(self) -> None:
        model = self._model()
        resp = SimpleNamespace(text="Hi", usage_metadata=None, candidates=[])
        model._client.models.generate_content.return_value = resp
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            result = model.generate("Hi")
        assert result.usage == {}
        assert result.finish_reason == "stop"

    def test_generate_no_text(self) -> None:
        model = self._model()
        resp = SimpleNamespace(usage_metadata=None, candidates=[])
        model._client.models.generate_content.return_value = resp
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            result = model.generate("Hi")
        assert result.text == ""

    def test_generate_error_handling(self) -> None:
        model = self._model()
        model._client.models.generate_content.side_effect = Exception("Rate limit exceeded")
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            with pytest.raises(RateLimitError):
                model.generate("Hi")

    def test_generate_structured(self) -> None:
        model = self._model()
        json_str = json.dumps({"name": "test", "value": 42})
        resp = _mock_gemini_response(text=json_str)
        model._client.models.generate_content.return_value = resp
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            result = model.generate_structured("make struct", _SampleSchema)
        assert result.name == "test"

    def test_generate_structured_fenced(self) -> None:
        model = self._model()
        json_str = f"```json\n{json.dumps({'name': 'x', 'value': 1})}\n```"
        resp = _mock_gemini_response(text=json_str)
        model._client.models.generate_content.return_value = resp
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            result = model.generate_structured("make", _SampleSchema)
        assert result.name == "x"

    def test_generate_structured_parse_fail(self) -> None:
        model = self._model()
        resp = _mock_gemini_response(text="not json")
        model._client.models.generate_content.return_value = resp
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            with pytest.raises(InvalidRequestError, match="parse"):
                model.generate_structured("make", _SampleSchema)

    def test_generate_stream(self) -> None:
        model = self._model()
        chunks = [
            SimpleNamespace(text="Hello"),
            SimpleNamespace(text=" world"),
        ]
        model._client.models.generate_content_stream.return_value = iter(chunks)
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            result = list(model.generate_stream("Hi"))
        assert result == ["Hello", " world"]

    def test_generate_stream_error(self) -> None:
        model = self._model()
        model._client.models.generate_content_stream.side_effect = Exception("fail")
        mock_types = MagicMock()
        with patch.dict(
            "sys.modules",
            {"google.genai.types": mock_types, "google.genai": MagicMock(types=mock_types), "google": MagicMock()},
        ):
            with pytest.raises(ModelError):
                list(model.generate_stream("Hi"))


# ── Ollama generate ────────────────────────────────────────────────


class TestOllamaGenerate:
    def _model(self):
        from personaut.models.ollama import OllamaModel

        return OllamaModel()

    def test_generate_basic(self) -> None:
        import httpx

        model = self._model()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": "Hello!",
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 5,
        }
        with patch.object(httpx, "post", return_value=mock_resp):
            result = model.generate("Hi")
        assert result.text == "Hello!"
        assert result.finish_reason == "stop"

    def test_generate_with_system(self) -> None:
        import httpx

        model = self._model()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Reply", "done": True}
        with patch.object(httpx, "post", return_value=mock_resp) as mock_post:
            model.generate("Hi", system="Be brief")
            body = mock_post.call_args.kwargs["json"]
            assert body["system"] == "Be brief"

    def test_generate_with_overrides(self) -> None:
        import httpx

        model = self._model()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "X", "done": True}
        with patch.object(httpx, "post", return_value=mock_resp) as mock_post:
            model.generate("Hi", max_tokens=500, stop_sequences=["END"])
            body = mock_post.call_args.kwargs["json"]
            assert body["options"]["num_predict"] == 500
            assert body["options"]["stop"] == ["END"]

    def test_generate_not_done(self) -> None:
        import httpx

        model = self._model()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "partial", "done": False}
        with patch.object(httpx, "post", return_value=mock_resp):
            result = model.generate("Hi")
        assert result.finish_reason == "length"

    def test_generate_http_error(self) -> None:
        import httpx

        model = self._model()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 not found", request=MagicMock(), response=MagicMock()
        )
        with patch.object(httpx, "post", return_value=mock_resp):
            with pytest.raises(InvalidRequestError, match="not found"):
                model.generate("Hi")

    def test_generate_generic_error(self) -> None:
        import httpx

        model = self._model()
        with patch.object(httpx, "post", side_effect=ConnectionError("refused")):
            with pytest.raises(ModelError, match="Ollama request failed"):
                model.generate("Hi")

    def test_generate_structured(self) -> None:
        import httpx

        model = self._model()
        json_str = json.dumps({"name": "test", "value": 42})
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": json_str, "done": True}
        with patch.object(httpx, "post", return_value=mock_resp):
            result = model.generate_structured("make", _SampleSchema)
        assert result.name == "test"

    def test_generate_structured_fenced(self) -> None:
        import httpx

        model = self._model()
        json_str = f"```json\n{json.dumps({'name': 'x', 'value': 1})}\n```"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": json_str, "done": True}
        with patch.object(httpx, "post", return_value=mock_resp):
            result = model.generate_structured("make", _SampleSchema)
        assert result.name == "x"

    def test_generate_structured_parse_fail(self) -> None:
        import httpx

        model = self._model()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "not json", "done": True}
        with patch.object(httpx, "post", return_value=mock_resp):
            with pytest.raises(InvalidRequestError, match="parse"):
                model.generate_structured("make", _SampleSchema)

    def test_is_available_success(self) -> None:
        import httpx

        model = self._model()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(httpx, "get", return_value=mock_resp):
            assert model.is_available() is True

    def test_is_available_cached(self) -> None:
        model = self._model()
        model._available = True
        assert model.is_available() is True

    def test_is_available_fail(self) -> None:
        import httpx

        model = self._model()
        with patch.object(httpx, "get", side_effect=ConnectionError("refused")):
            assert model.is_available() is False

    def test_list_models(self) -> None:
        import httpx

        model = self._model()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "llama3"}, {"name": "mistral"}]}
        with patch.object(httpx, "get", return_value=mock_resp):
            models = model.list_models()
        assert models == ["llama3", "mistral"]

    def test_list_models_error(self) -> None:
        import httpx

        model = self._model()
        with patch.object(httpx, "get", side_effect=Exception("connection failed")):
            with pytest.raises(ModelError, match="Failed to list"):
                model.list_models()

    def test_generate_stream(self) -> None:
        import httpx

        model = self._model()
        stream_resp = MagicMock()
        stream_resp.__enter__ = MagicMock(return_value=stream_resp)
        stream_resp.__exit__ = MagicMock(return_value=False)
        stream_resp.iter_lines.return_value = [
            json.dumps({"response": "Hello", "done": False}),
            json.dumps({"response": " world", "done": False}),
            json.dumps({"response": "", "done": True}),
        ]
        with patch.object(httpx, "stream", return_value=stream_resp):
            result = list(model.generate_stream("Hi"))
        assert result == ["Hello", " world"]

    def test_generate_stream_with_opts(self) -> None:
        import httpx

        model = self._model()
        stream_resp = MagicMock()
        stream_resp.__enter__ = MagicMock(return_value=stream_resp)
        stream_resp.__exit__ = MagicMock(return_value=False)
        stream_resp.iter_lines.return_value = [
            json.dumps({"response": "Hi", "done": True}),
        ]
        with patch.object(httpx, "stream", return_value=stream_resp) as mock_stream:
            list(model.generate_stream("Hi", max_tokens=100, system="Sys"))
            call_args = mock_stream.call_args
            body = call_args.kwargs["json"]
            assert body["options"]["num_predict"] == 100
            assert body["system"] == "Sys"


# ── Bedrock generate ───────────────────────────────────────────────


class TestBedrockGenerate:
    def _model(self, model_name="claude-3-5-haiku"):
        from personaut.models.bedrock import BedrockModel

        m = BedrockModel(model=model_name)
        m._client = MagicMock()
        return m

    def test_generate_basic(self) -> None:
        model = self._model()
        mock_resp = {
            "body": MagicMock(),
        }
        mock_resp["body"].read.return_value = json.dumps(
            {
                "content": [{"text": "Hello from Claude"}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
                "stop_reason": "end_turn",
            }
        ).encode()
        model._client.invoke_model.return_value = mock_resp
        result = model.generate("Hello")
        assert isinstance(result, GenerationResult)
        assert result.text == "Hello from Claude"

    def test_generate_error(self) -> None:
        model = self._model()
        model._client.invoke_model.side_effect = Exception("Throttling exception")
        with pytest.raises(RateLimitError):
            model.generate("Hi")

    def test_generate_structured(self) -> None:
        model = self._model()
        json_str = json.dumps({"name": "test", "value": 42})
        mock_resp = {"body": MagicMock()}
        mock_resp["body"].read.return_value = json.dumps(
            {
                "content": [{"text": json_str}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        ).encode()
        model._client.invoke_model.return_value = mock_resp
        result = model.generate_structured("make", _SampleSchema)
        assert result.name == "test"
