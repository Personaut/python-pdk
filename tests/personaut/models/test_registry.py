"""Extended tests for ModelRegistry — targeting uncovered branches."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from personaut.models.embeddings import EmbeddingModel
from personaut.models.model import Model, ModelError
from personaut.models.registry import (
    ENV_EMBEDDING_MODEL,
    ENV_LLM_MODEL,
    ENV_LLM_PROVIDER,
    ModelRegistry,
    Provider,
    get_embedding,
    get_llm,
    get_registry,
)


class TestProvider:
    """Tests for Provider enum."""

    def test_provider_values(self) -> None:
        """Test Provider enum values."""
        assert Provider.GEMINI.value == "gemini"
        assert Provider.BEDROCK.value == "bedrock"
        assert Provider.OPENAI.value == "openai"
        assert Provider.OLLAMA.value == "ollama"

    def test_provider_string_conversion(self) -> None:
        """Test Provider from string."""
        assert Provider("gemini") == Provider.GEMINI
        assert Provider("openai") == Provider.OPENAI

    def test_provider_invalid_raises(self) -> None:
        """Invalid provider string should raise ValueError."""
        with pytest.raises(ValueError):
            Provider("invalid_provider")


class TestModelRegistry:
    """Tests for ModelRegistry class."""

    def test_registry_creation(self) -> None:
        """Test registry can be created."""
        registry = ModelRegistry()
        assert registry.default_provider is None
        assert registry.embedding_model is None

    def test_registry_with_explicit_provider(self) -> None:
        """Test registry with explicit provider."""
        registry = ModelRegistry(default_provider=Provider.GEMINI)
        assert registry.default_provider == Provider.GEMINI

    def test_registry_list_providers(self) -> None:
        """Test listing all providers."""
        registry = ModelRegistry()
        providers = registry.list_providers()
        assert len(providers) == 4
        assert all(isinstance(p[0], Provider) for p in providers)
        assert all(isinstance(p[1], bool) for p in providers)

    @patch.dict(os.environ, {ENV_LLM_PROVIDER: "openai"})
    def test_registry_from_env_provider(self) -> None:
        """Test registry reads provider from environment."""
        registry = ModelRegistry()
        assert registry.default_provider == Provider.OPENAI

    @patch.dict(os.environ, {ENV_EMBEDDING_MODEL: "test-model"})
    def test_registry_from_env_embedding(self) -> None:
        """Test registry reads embedding model from environment."""
        registry = ModelRegistry()
        assert registry.embedding_model == "test-model"

    @patch.dict(os.environ, {ENV_LLM_PROVIDER: "invalid_provider_xyz"})
    def test_registry_with_invalid_env_provider(self) -> None:
        """Invalid provider in env should be warn-logged but not crash."""
        registry = ModelRegistry()
        # The invalid provider is logged and default_provider remains None
        assert registry.default_provider is None


class TestCheckProviderAvailable:
    """Tests for _check_provider_available."""

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=False)
    def test_gemini_available(self) -> None:
        """Gemini should be available with GOOGLE_API_KEY set."""
        registry = ModelRegistry()
        assert registry._check_provider_available(Provider.GEMINI) is True

    @patch.dict(os.environ, {}, clear=True)
    def test_gemini_unavailable(self) -> None:
        """Gemini should be unavailable without GOOGLE_API_KEY."""
        registry = ModelRegistry()
        assert registry._check_provider_available(Provider.GEMINI) is False

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False)
    def test_openai_available(self) -> None:
        """OpenAI should be available with OPENAI_API_KEY set."""
        registry = ModelRegistry()
        assert registry._check_provider_available(Provider.OPENAI) is True

    @patch.dict(os.environ, {}, clear=True)
    def test_openai_unavailable(self) -> None:
        """OpenAI should be unavailable without OPENAI_API_KEY."""
        registry = ModelRegistry()
        assert registry._check_provider_available(Provider.OPENAI) is False

    @patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "test-key"}, clear=False)
    def test_bedrock_available_with_access_key(self) -> None:
        """Bedrock should be available with AWS_ACCESS_KEY_ID."""
        registry = ModelRegistry()
        assert registry._check_provider_available(Provider.BEDROCK) is True

    @patch.dict(os.environ, {"AWS_PROFILE": "my-profile"}, clear=False)
    def test_bedrock_available_with_profile(self) -> None:
        """Bedrock should be available with AWS_PROFILE."""
        registry = ModelRegistry()
        assert registry._check_provider_available(Provider.BEDROCK) is True

    @patch.dict(os.environ, {"AWS_ROLE_ARN": "arn:aws:iam::role/test"}, clear=False)
    def test_bedrock_available_with_role_arn(self) -> None:
        """Bedrock should be available with AWS_ROLE_ARN."""
        registry = ModelRegistry()
        assert registry._check_provider_available(Provider.BEDROCK) is True

    @patch.dict(os.environ, {}, clear=True)
    def test_bedrock_unavailable(self) -> None:
        """Bedrock should be unavailable without AWS credentials."""
        registry = ModelRegistry()
        assert registry._check_provider_available(Provider.BEDROCK) is False


class TestDetectProvider:
    """Tests for _detect_provider."""

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test"}, clear=True)
    def test_detect_gemini_first(self) -> None:
        """Should detect Gemini first when available."""
        registry = ModelRegistry()
        assert registry._detect_provider() == Provider.GEMINI

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True)
    def test_detect_openai_when_no_gemini(self) -> None:
        """Should detect OpenAI when Gemini is unavailable."""
        registry = ModelRegistry()
        assert registry._detect_provider() == Provider.OPENAI

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_no_provider_raises(self) -> None:
        """Should raise ModelError when no provider is available."""
        registry = ModelRegistry()
        with pytest.raises(ModelError, match="No LLM provider available"):
            registry._detect_provider()


class TestGetLLM:
    """Tests for get_llm and ModelRegistry.get_llm."""

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    def test_get_llm_with_gemini_key(self) -> None:
        """Test get_llm can get Gemini model with API key."""
        model = get_llm(provider=Provider.GEMINI)
        assert isinstance(model, Model)
        assert model.provider == "gemini"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_get_llm_with_openai_key(self) -> None:
        """Test get_llm can get OpenAI model with API key."""
        model = get_llm(provider=Provider.OPENAI)
        assert isinstance(model, Model)
        assert model.provider == "openai"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    def test_get_llm_caches_model(self) -> None:
        """Same provider+model should return cached instance."""
        registry = ModelRegistry()
        llm1 = registry.get_llm(provider=Provider.GEMINI)
        llm2 = registry.get_llm(provider=Provider.GEMINI)
        assert llm1 is llm2

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    def test_get_llm_with_string_provider(self) -> None:
        """String provider should be converted to Provider enum."""
        registry = ModelRegistry()
        llm = registry.get_llm(provider="gemini")
        assert isinstance(llm, Model)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    def test_get_llm_with_explicit_model(self) -> None:
        """Explicit model name should be used."""
        registry = ModelRegistry()
        llm = registry.get_llm(provider=Provider.GEMINI, model="gemini-1.5-flash")
        assert isinstance(llm, Model)

    @patch.dict(os.environ, {ENV_LLM_MODEL: "gemini-custom", "GOOGLE_API_KEY": "test"})
    def test_get_llm_uses_env_model(self) -> None:
        """Should use PERSONAUT_LLM_MODEL from environment."""
        registry = ModelRegistry()
        llm = registry.get_llm(provider=Provider.GEMINI)
        assert isinstance(llm, Model)


class TestGetEmbedding:
    """Tests for get_embedding function."""

    def test_get_embedding_returns_local(self) -> None:
        """Test get_embedding returns LocalEmbedding."""
        embed = get_embedding()
        assert isinstance(embed, EmbeddingModel)
        assert "MiniLM" in embed.model_name or "sentence" in embed.model_name.lower()

    def test_get_embedding_with_custom_model(self) -> None:
        """Test get_embedding with custom model path."""
        embed = get_embedding(model="custom/model")
        assert "custom/model" in embed.model_name

    def test_get_embedding_caches(self) -> None:
        """Same embedding request should return cached instance."""
        registry = ModelRegistry()
        embed1 = registry.get_embedding()
        embed2 = registry.get_embedding()
        assert embed1 is embed2

    def test_get_embedding_with_model_not_cached(self) -> None:
        """Embedding with explicit model should not use default cache."""
        registry = ModelRegistry()
        embed1 = registry.get_embedding()
        embed2 = registry.get_embedding(model="custom/model")
        # Different models should not be the same instance
        assert embed2 is not embed1


class TestGetRegistry:
    """Tests for get_registry function."""

    def test_get_registry_returns_singleton(self) -> None:
        """Test get_registry returns a ModelRegistry."""
        registry = get_registry()
        assert isinstance(registry, ModelRegistry)


class TestEnvironmentVariables:
    """Tests for environment variable constants."""

    def test_env_variable_names(self) -> None:
        """Test environment variable constant names."""
        assert ENV_LLM_PROVIDER == "PERSONAUT_LLM_PROVIDER"
        assert ENV_LLM_MODEL == "PERSONAUT_LLM_MODEL"
        assert ENV_EMBEDDING_MODEL == "PERSONAUT_EMBEDDING_MODEL"
