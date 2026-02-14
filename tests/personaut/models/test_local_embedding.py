"""Extended tests for LocalEmbedding — targeting uncovered branches."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from personaut.models.embeddings import (
    DEFAULT_MODEL_SMALL,
    EMBEDDING_MODELS,
    EmbeddingError,
    ModelLoadError,
)
from personaut.models.local_embedding import (
    LocalEmbedding,
    _detect_device,
    _hash_text,
    create_local_embedding,
)


class TestDetectDevice:
    """Tests for _detect_device helper."""

    @patch.dict("sys.modules", {"torch": None})
    def test_no_torch_returns_cpu(self) -> None:
        """Without torch, should return cpu."""
        # Force reimport with torch unavailable
        result = _detect_device()
        assert result == "cpu"


class TestHashText:
    """Tests for _hash_text helper."""

    def test_hash_consistent(self) -> None:
        """Same text should produce same hash."""
        assert _hash_text("hello") == _hash_text("hello")

    def test_hash_different(self) -> None:
        """Different text should produce different hash."""
        assert _hash_text("hello") != _hash_text("world")


class TestLocalEmbeddingInit:
    """Tests for LocalEmbedding initialization."""

    def test_default_model(self) -> None:
        """Default model should be DEFAULT_MODEL_SMALL."""
        embed = LocalEmbedding()
        assert embed.model_path == DEFAULT_MODEL_SMALL

    def test_auto_device_detection(self) -> None:
        """Auto device should resolve to something."""
        embed = LocalEmbedding(device="auto")
        assert embed.device in ("cpu", "cuda", "mps")

    def test_explicit_device(self) -> None:
        """Explicit device should be preserved."""
        embed = LocalEmbedding(device="cpu")
        assert embed.device == "cpu"

    def test_known_model_gets_dimension(self) -> None:
        """Known model should get dimension from registry."""
        embed = LocalEmbedding(model_path=DEFAULT_MODEL_SMALL)
        assert embed._dimension > 0
        assert embed._dimension == EMBEDDING_MODELS[DEFAULT_MODEL_SMALL]

    def test_unknown_model_no_dimension(self) -> None:
        """Unknown model should have 0 dimension initially."""
        embed = LocalEmbedding(model_path="unknown/model")
        assert embed._dimension == 0


class TestLocalEmbeddingProperties:
    """Tests for LocalEmbedding properties."""

    def test_model_name(self) -> None:
        """model_name should return model_path."""
        embed = LocalEmbedding(model_path="test/model")
        assert embed.model_name == "test/model"

    def test_is_loaded_false_initially(self) -> None:
        """Model should not be loaded initially."""
        embed = LocalEmbedding()
        assert embed.is_loaded() is False


class TestLocalEmbeddingCache:
    """Tests for embedding cache."""

    def test_update_cache(self) -> None:
        """Cache should store embeddings."""
        embed = LocalEmbedding(cache_size=5)
        embed._update_cache("key1", [0.1, 0.2])
        assert "key1" in embed._cache

    def test_cache_eviction(self) -> None:
        """Cache should evict when full."""
        embed = LocalEmbedding(cache_size=2)
        embed._update_cache("key1", [0.1])
        embed._update_cache("key2", [0.2])
        embed._update_cache("key3", [0.3])  # This should evict key1
        assert "key1" not in embed._cache
        assert "key3" in embed._cache
        assert len(embed._cache) == 2

    def test_clear_cache(self) -> None:
        """clear_cache should empty the cache."""
        embed = LocalEmbedding(cache_size=5)
        embed._update_cache("key1", [0.1])
        embed._update_cache("key2", [0.2])
        embed.clear_cache()
        assert len(embed._cache) == 0


class TestLocalEmbeddingEmbed:
    """Tests for embed method with mocked model."""

    def test_embed_uses_cache(self) -> None:
        """Cached embedding should be returned without model call."""
        embed = LocalEmbedding(cache_size=100)
        cached_emb = [0.1, 0.2, 0.3]
        cache_key = _hash_text("test text")
        embed._cache[cache_key] = cached_emb

        result = embed.embed("test text")
        assert result == cached_emb

    def test_embed_no_cache(self) -> None:
        """With cache disabled, should always call model."""
        embed = LocalEmbedding(cache_size=0)
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        embed._model = mock_model

        result = embed.embed("test")
        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once()

    def test_embed_stores_in_cache(self) -> None:
        """New embedding should be cached."""
        embed = LocalEmbedding(cache_size=100)
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        embed._model = mock_model

        embed.embed("new text")
        assert len(embed._cache) == 1

    def test_embed_error_raises_embedding_error(self) -> None:
        """Model error should raise EmbeddingError."""
        embed = LocalEmbedding(cache_size=0)
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("Model error")
        embed._model = mock_model

        with pytest.raises(EmbeddingError, match="Failed to generate embedding"):
            embed.embed("test")


class TestLocalEmbeddingEmbedBatch:
    """Tests for embed_batch method."""

    def test_embed_batch_empty(self) -> None:
        """Empty list should return empty list."""
        embed = LocalEmbedding()
        assert embed.embed_batch([]) == []

    def test_embed_batch_with_cache(self) -> None:
        """Batch should use cached results when available."""
        embed = LocalEmbedding(cache_size=100)
        # Pre-cache one text
        cache_key = _hash_text("cached text")
        embed._cache[cache_key] = [0.1, 0.2]

        # Mock model for uncached text
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.3, 0.4]])
        embed._model = mock_model

        results = embed.embed_batch(["cached text", "new text"])
        assert len(results) == 2
        assert results[0] == [0.1, 0.2]

    def test_embed_batch_no_cache(self) -> None:
        """Batch with cache disabled should encode all."""
        embed = LocalEmbedding(cache_size=0)
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        embed._model = mock_model

        results = embed.embed_batch(["text1", "text2"])
        assert len(results) == 2
        mock_model.encode.assert_called_once()

    def test_embed_batch_error_raises(self) -> None:
        """Model error in batch should raise EmbeddingError."""
        embed = LocalEmbedding(cache_size=0)
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("Batch error")
        embed._model = mock_model

        with pytest.raises(EmbeddingError, match="Failed to generate batch"):
            embed.embed_batch(["text1"])


class TestLocalEmbeddingUnload:
    """Tests for unload method."""

    def test_unload_clears_model_and_cache(self) -> None:
        """Unload should clear model and cache."""
        embed = LocalEmbedding(cache_size=5)
        embed._model = MagicMock()
        embed._cache["key1"] = [0.1]

        embed.unload()
        assert embed._model is None
        assert len(embed._cache) == 0

    def test_unload_no_model(self) -> None:
        """Unload with no model should be safe."""
        embed = LocalEmbedding()
        embed.unload()  # Should not raise


class TestEnsureLoaded:
    """Tests for _ensure_loaded."""

    def test_ensure_loaded_already_loaded(self) -> None:
        """Already loaded model should be a no-op."""
        embed = LocalEmbedding()
        embed._model = MagicMock()
        embed._ensure_loaded()  # Should not reload

    @patch.dict("sys.modules", {"sentence_transformers": None})
    def test_ensure_loaded_no_sentence_transformers(self) -> None:
        """Missing sentence_transformers should raise ModelLoadError."""
        embed = LocalEmbedding()
        with pytest.raises(ModelLoadError, match="sentence-transformers"):
            embed._ensure_loaded()


class TestCreateLocalEmbedding:
    """Tests for create_local_embedding factory."""

    def test_create_with_defaults(self) -> None:
        """Default creation should use small model."""
        embed = create_local_embedding()
        assert embed.model_path == DEFAULT_MODEL_SMALL
        assert embed.normalize is True
        assert embed.batch_size == 32
        assert embed.cache_size == 1000

    def test_create_with_custom_model(self) -> None:
        """Custom model should be used."""
        embed = create_local_embedding(model="custom/model", device="cpu")
        assert embed.model_path == "custom/model"
        assert embed.device == "cpu"

    def test_create_with_none_model(self) -> None:
        """None model should default to DEFAULT_MODEL_SMALL."""
        embed = create_local_embedding(model=None)
        assert embed.model_path == DEFAULT_MODEL_SMALL
