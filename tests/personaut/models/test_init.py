"""Tests for models package lazy loading and exports."""

from __future__ import annotations

import pytest

import personaut.models as models_pkg
from personaut.models import (
    DEFAULT_MODEL_LARGE,
    DEFAULT_MODEL_SMALL,
    EMBEDDING_MODELS,
    ENV_EMBEDDING_MODEL,
    ENV_LLM_MODEL,
    ENV_LLM_PROVIDER,
    AsyncModel,
    AuthenticationError,
    EmbeddingConfig,
    EmbeddingError,
    EmbeddingModel,
    GenerationResult,
    InvalidRequestError,
    LocalEmbedding,
    Model,
    ModelConfig,
    ModelError,
    ModelLoadError,
    ModelNotLoadedError,
    ModelRegistry,
    Provider,
    RateLimitError,
    TextTooLongError,
    create_local_embedding,
    get_embedding,
    get_llm,
    get_registry,
)


class TestDirectImports:
    """Tests for directly-imported (non-lazy) symbols."""

    def test_model_class(self) -> None:
        """Model base class should be importable."""
        assert Model is not None

    def test_async_model_class(self) -> None:
        """AsyncModel base class should be importable."""
        assert AsyncModel is not None

    def test_model_config_class(self) -> None:
        """ModelConfig should be importable."""
        assert ModelConfig is not None

    def test_generation_result_class(self) -> None:
        """GenerationResult should be importable."""
        assert GenerationResult is not None

    def test_model_errors(self) -> None:
        """Model error classes should be importable."""
        assert issubclass(ModelError, Exception)
        assert issubclass(RateLimitError, ModelError)
        assert issubclass(AuthenticationError, ModelError)
        assert issubclass(InvalidRequestError, ModelError)

    def test_embedding_classes(self) -> None:
        """Embedding classes should be importable."""
        assert EmbeddingModel is not None
        assert EmbeddingConfig is not None

    def test_embedding_errors(self) -> None:
        """Embedding error classes should be importable."""
        assert issubclass(EmbeddingError, Exception)
        assert issubclass(ModelLoadError, EmbeddingError)
        assert issubclass(ModelNotLoadedError, EmbeddingError)
        assert issubclass(TextTooLongError, EmbeddingError)

    def test_embedding_constants(self) -> None:
        """Embedding model constants should be importable."""
        assert isinstance(EMBEDDING_MODELS, dict)
        assert isinstance(DEFAULT_MODEL_LARGE, str)
        assert isinstance(DEFAULT_MODEL_SMALL, str)

    def test_local_embedding(self) -> None:
        """LocalEmbedding should be importable."""
        assert LocalEmbedding is not None
        assert callable(create_local_embedding)

    def test_registry(self) -> None:
        """Registry classes and functions should be importable."""
        assert ModelRegistry is not None
        assert Provider is not None
        assert callable(get_registry)
        assert callable(get_llm)
        assert callable(get_embedding)

    def test_env_constants(self) -> None:
        """Environment variable constants should be importable."""
        assert ENV_LLM_PROVIDER == "PERSONAUT_LLM_PROVIDER"
        assert ENV_LLM_MODEL == "PERSONAUT_LLM_MODEL"
        assert ENV_EMBEDDING_MODEL == "PERSONAUT_EMBEDDING_MODEL"


class TestLazyLoadingGemini:
    """Tests for lazy-loaded Gemini symbols."""

    def test_gemini_model_class(self) -> None:
        """GeminiModel should be lazy-loadable."""
        cls = models_pkg.GeminiModel
        assert cls is not None
        assert hasattr(cls, "__init__")

    def test_create_gemini_model_fn(self) -> None:
        """create_gemini_model should be lazy-loadable."""
        fn = models_pkg.create_gemini_model
        assert callable(fn)

    def test_default_gemini_model_constant(self) -> None:
        """DEFAULT_GEMINI_MODEL should be a string."""
        val = models_pkg.DEFAULT_GEMINI_MODEL
        assert isinstance(val, str)
        assert len(val) > 0

    def test_available_gemini_models_list(self) -> None:
        """AVAILABLE_GEMINI_MODELS should be a list."""
        val = models_pkg.AVAILABLE_GEMINI_MODELS
        assert isinstance(val, list)
        assert len(val) > 0


class TestLazyLoadingOpenAI:
    """Tests for lazy-loaded OpenAI symbols."""

    def test_openai_model_class(self) -> None:
        """OpenAIModel should be lazy-loadable."""
        cls = models_pkg.OpenAIModel
        assert cls is not None

    def test_create_openai_model_fn(self) -> None:
        """create_openai_model should be lazy-loadable."""
        fn = models_pkg.create_openai_model
        assert callable(fn)

    def test_default_openai_model_constant(self) -> None:
        """DEFAULT_OPENAI_MODEL should be a string."""
        val = models_pkg.DEFAULT_OPENAI_MODEL
        assert isinstance(val, str)
        assert len(val) > 0

    def test_available_openai_models_list(self) -> None:
        """AVAILABLE_OPENAI_MODELS should be a list."""
        val = models_pkg.AVAILABLE_OPENAI_MODELS
        assert isinstance(val, list)
        assert len(val) > 0


class TestLazyLoadingBedrock:
    """Tests for lazy-loaded Bedrock symbols."""

    def test_bedrock_model_class(self) -> None:
        """BedrockModel should be lazy-loadable."""
        cls = models_pkg.BedrockModel
        assert cls is not None

    def test_create_bedrock_model_fn(self) -> None:
        """create_bedrock_model should be lazy-loadable."""
        fn = models_pkg.create_bedrock_model
        assert callable(fn)

    def test_default_bedrock_model_constant(self) -> None:
        """DEFAULT_BEDROCK_MODEL should be a string."""
        val = models_pkg.DEFAULT_BEDROCK_MODEL
        assert isinstance(val, str)
        assert len(val) > 0

    def test_bedrock_models_dict(self) -> None:
        """BEDROCK_MODELS should be a dict."""
        val = models_pkg.BEDROCK_MODELS
        assert isinstance(val, dict)
        assert len(val) > 0


class TestLazyLoadingOllama:
    """Tests for lazy-loaded Ollama symbols."""

    def test_ollama_model_class(self) -> None:
        """OllamaModel should be lazy-loadable."""
        cls = models_pkg.OllamaModel
        assert cls is not None

    def test_create_ollama_model_fn(self) -> None:
        """create_ollama_model should be lazy-loadable."""
        fn = models_pkg.create_ollama_model
        assert callable(fn)

    def test_default_ollama_model_constant(self) -> None:
        """DEFAULT_OLLAMA_MODEL should be a string."""
        val = models_pkg.DEFAULT_OLLAMA_MODEL
        assert isinstance(val, str)
        assert len(val) > 0

    def test_default_ollama_host_constant(self) -> None:
        """DEFAULT_OLLAMA_HOST should be a string."""
        val = models_pkg.DEFAULT_OLLAMA_HOST
        assert isinstance(val, str)
        assert "localhost" in val or "127.0.0.1" in val


class TestLazyLoadingUnknownAttribute:
    """Tests for unknown attribute access."""

    def test_unknown_attribute_raises(self) -> None:
        """Accessing unknown attribute should raise AttributeError."""
        with pytest.raises(AttributeError, match="has no attribute"):
            models_pkg.NonExistentSymbol


class TestAllExports:
    """Tests for __all__ completeness."""

    def test_all_defined(self) -> None:
        """__all__ should be defined."""
        assert hasattr(models_pkg, "__all__")
        assert isinstance(models_pkg.__all__, list)

    def test_all_symbols_accessible(self) -> None:
        """All symbols in __all__ should be accessible."""
        for name in models_pkg.__all__:
            obj = getattr(models_pkg, name, None)
            assert obj is not None, f"__all__ contains inaccessible symbol: {name}"
