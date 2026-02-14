"""Tests for common type definitions."""

from __future__ import annotations

from personaut.types.common import (
    EmbeddingModelProtocol,
    EmbeddingVector,
    EmotionalStateProtocol,
    EmotionDict,
    IndividualProtocol,
    IndividualT,
    JsonDict,
    MemoryProtocol,
    MemoryT,
    ModelProtocol,
    T,
    T_co,
    TraitDict,
    TrustDict,
    VectorStoreProtocol,
)


class TestTypeAliases:
    """Tests for type aliases."""

    def test_emotion_dict_type(self) -> None:
        """EmotionDict should be a dict type alias."""
        emotions: EmotionDict = {"anxious": 0.6, "hopeful": 0.8}
        assert isinstance(emotions, dict)
        assert emotions["anxious"] == 0.6

    def test_trait_dict_type(self) -> None:
        """TraitDict should be a dict type alias."""
        traits: TraitDict = {"warmth": 0.9, "dominance": 0.3}
        assert isinstance(traits, dict)
        assert traits["warmth"] == 0.9

    def test_trust_dict_type(self) -> None:
        """TrustDict should be a dict type alias."""
        trust: TrustDict = {"user_1": 0.5, "user_2": 0.8}
        assert isinstance(trust, dict)
        assert trust["user_1"] == 0.5

    def test_embedding_vector_type(self) -> None:
        """EmbeddingVector should be a list of floats."""
        embedding: EmbeddingVector = [0.1, 0.2, 0.3, 0.4]
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

    def test_json_dict_type(self) -> None:
        """JsonDict should accept various value types."""
        data: JsonDict = {
            "name": "test",
            "count": 42,
            "active": True,
            "nested": {"key": "value"},
        }
        assert isinstance(data, dict)
        assert data["name"] == "test"


class TestTypeVars:
    """Tests for TypeVars."""

    def test_typevars_exist(self) -> None:
        """TypeVars should be defined."""
        assert T is not None
        assert T_co is not None
        assert IndividualT is not None
        assert MemoryT is not None


class TestIndividualProtocol:
    """Tests for IndividualProtocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """IndividualProtocol should be runtime checkable."""

        class MockIndividual:
            @property
            def id(self) -> str:
                return "test_id"

            @property
            def name(self) -> str:
                return "Test Name"

        individual = MockIndividual()
        assert isinstance(individual, IndividualProtocol)

    def test_non_conforming_type(self) -> None:
        """Non-conforming types should not match protocol."""

        class NotAnIndividual:
            pass

        obj = NotAnIndividual()
        assert not isinstance(obj, IndividualProtocol)


class TestEmotionalStateProtocol:
    """Tests for EmotionalStateProtocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """EmotionalStateProtocol should be runtime checkable."""

        class MockEmotionalState:
            def __init__(self) -> None:
                self._emotions: EmotionDict = {}

            def get_emotion(self, emotion: str) -> float:
                return self._emotions.get(emotion, 0.0)

            def change_emotion(self, emotion: str, value: float) -> None:
                self._emotions[emotion] = value

            def to_dict(self) -> EmotionDict:
                return dict(self._emotions)

        state = MockEmotionalState()
        assert isinstance(state, EmotionalStateProtocol)


class TestMemoryProtocol:
    """Tests for MemoryProtocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """MemoryProtocol should be runtime checkable."""

        class MockMemory:
            @property
            def id(self) -> str:
                return "mem_123"

            @property
            def description(self) -> str:
                return "A test memory"

        memory = MockMemory()
        assert isinstance(memory, MemoryProtocol)


class TestModelProtocol:
    """Tests for ModelProtocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """ModelProtocol should be runtime checkable."""

        class MockModel:
            def generate(self, prompt: str) -> str:
                return f"Response to: {prompt}"

        model = MockModel()
        assert isinstance(model, ModelProtocol)


class TestEmbeddingModelProtocol:
    """Tests for EmbeddingModelProtocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """EmbeddingModelProtocol should be runtime checkable."""

        class MockEmbedding:
            def embed(self, _text: str) -> EmbeddingVector:
                return [0.1, 0.2, 0.3]

        embedding = MockEmbedding()
        assert isinstance(embedding, EmbeddingModelProtocol)


class TestVectorStoreProtocol:
    """Tests for VectorStoreProtocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """VectorStoreProtocol should be runtime checkable."""

        class MockVectorStore:
            def store(self, _id: str, _embedding: EmbeddingVector, _metadata: JsonDict) -> None:
                pass

            def search(
                self,
                _query_embedding: EmbeddingVector,
                _limit: int = 10,
            ) -> list[tuple[str, float, JsonDict]]:
                return []

        store = MockVectorStore()
        assert isinstance(store, VectorStoreProtocol)
