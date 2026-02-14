"""Tests for the embedding interfaces."""

from __future__ import annotations

from personaut.models.embeddings import (
    DEFAULT_MODEL_LARGE,
    DEFAULT_MODEL_SMALL,
    EMBEDDING_MODELS,
    EmbeddingConfig,
    EmbeddingError,
    EmbeddingModel,
    ModelLoadError,
    ModelNotLoadedError,
    TextTooLongError,
)


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = EmbeddingConfig()
        assert config.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.dimension == 384
        assert config.device == "auto"
        assert config.batch_size == 32
        assert config.normalize is True
        assert config.cache_embeddings is True
        assert config.max_length == 512

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = EmbeddingConfig(
            model_name="BAAI/bge-large-en-v1.5",
            dimension=1024,
            device="cuda",
            batch_size=64,
            normalize=False,
            cache_embeddings=False,
            max_length=256,
        )
        assert config.model_name == "BAAI/bge-large-en-v1.5"
        assert config.dimension == 1024
        assert config.device == "cuda"
        assert config.batch_size == 64
        assert config.normalize is False
        assert config.cache_embeddings is False
        assert config.max_length == 256


class TestEmbeddingModels:
    """Tests for embedding model constants."""

    def test_embedding_models_registry(self) -> None:
        """Test EMBEDDING_MODELS contains expected models."""
        assert "sentence-transformers/all-MiniLM-L6-v2" in EMBEDDING_MODELS
        assert EMBEDDING_MODELS["sentence-transformers/all-MiniLM-L6-v2"] == 384

        assert "BAAI/bge-large-en-v1.5" in EMBEDDING_MODELS
        assert EMBEDDING_MODELS["BAAI/bge-large-en-v1.5"] == 1024

    def test_default_models(self) -> None:
        """Test default model constants."""
        assert DEFAULT_MODEL_SMALL == "sentence-transformers/all-MiniLM-L6-v2"
        assert DEFAULT_MODEL_LARGE == "BAAI/bge-large-en-v1.5"


class TestEmbeddingErrors:
    """Tests for embedding error classes."""

    def test_embedding_error(self) -> None:
        """Test basic EmbeddingError."""
        error = EmbeddingError("Test error", model="test-model")
        assert str(error) == "Test error"
        assert error.model == "test-model"
        assert error.cause is None

    def test_model_not_loaded_error(self) -> None:
        """Test ModelNotLoadedError is an EmbeddingError."""
        error = ModelNotLoadedError("Model not loaded")
        assert isinstance(error, EmbeddingError)
        assert str(error) == "Model not loaded"

    def test_model_load_error(self) -> None:
        """Test ModelLoadError is an EmbeddingError."""
        error = ModelLoadError("Failed to load model")
        assert isinstance(error, EmbeddingError)
        assert str(error) == "Failed to load model"

    def test_text_too_long_error(self) -> None:
        """Test TextTooLongError has length info."""
        error = TextTooLongError(
            "Text too long",
            text_length=1000,
            max_length=512,
            model="test-model",
        )
        assert isinstance(error, EmbeddingError)
        assert error.text_length == 1000
        assert error.max_length == 512
        assert error.model == "test-model"

    def test_error_with_cause(self) -> None:
        """Test error with wrapped cause."""
        cause = ValueError("Original error")
        error = EmbeddingError("Wrapped error", cause=cause)
        assert error.cause is cause


class MockEmbeddingModel(EmbeddingModel):
    """Mock embedding model for testing."""

    def __init__(self, dim: int = 384):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return "mock-embedding"

    def embed(self, text: str) -> list[float]:
        # Return a simple embedding based on text length
        return [float(len(text)) / 100] * self._dim

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class TestEmbeddingModelProtocol:
    """Tests for EmbeddingModel protocol implementation."""

    def test_mock_model_properties(self) -> None:
        """Test embedding model properties."""
        model = MockEmbeddingModel(dim=768)
        assert model.dimension == 768
        assert model.model_name == "mock-embedding"

    def test_mock_model_embed(self) -> None:
        """Test single text embedding."""
        model = MockEmbeddingModel(dim=10)
        embedding = model.embed("Hello")
        assert len(embedding) == 10
        assert all(isinstance(v, float) for v in embedding)

    def test_mock_model_embed_batch(self) -> None:
        """Test batch text embedding."""
        model = MockEmbeddingModel(dim=5)
        embeddings = model.embed_batch(["Text 1", "Text 2", "Text 3"])
        assert len(embeddings) == 3
        assert all(len(e) == 5 for e in embeddings)

    def test_mock_model_is_loaded(self) -> None:
        """Test is_loaded default implementation."""
        model = MockEmbeddingModel()
        assert model.is_loaded() is True
