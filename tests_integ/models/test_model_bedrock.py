"""Integration tests for AWS Bedrock model provider.

These tests require valid AWS credentials:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION (default: us-east-1)
"""

from __future__ import annotations

import os

import pytest

from personaut.models import get_llm, get_embedding, Provider


# Skip all tests if no AWS credentials
pytestmark = pytest.mark.skipif(
    not (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")),
    reason="AWS credentials not set",
)


class TestBedrockTextGeneration:
    """Tests for Bedrock text generation."""

    def test_simple_generation(self) -> None:
        """Test basic text generation with Bedrock."""
        llm = get_llm(Provider.BEDROCK)

        result = llm.generate("Say hello in exactly 3 words.")

        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)

    def test_generation_with_system_prompt(self) -> None:
        """Test generation with system instruction."""
        llm = get_llm(Provider.BEDROCK)

        result = llm.generate(
            "What is 2+2?",
            system="You are a math tutor. Always respond with just the number.",
        )

        assert result is not None
        assert "4" in result

    def test_generation_with_temperature(self) -> None:
        """Test generation with temperature parameter."""
        llm = get_llm(Provider.BEDROCK)

        # Low temperature should give consistent results
        result1 = llm.generate("What is the capital of France?", temperature=0.0)
        result2 = llm.generate("What is the capital of France?", temperature=0.0)

        assert "Paris" in result1
        assert "Paris" in result2

    def test_generation_with_max_tokens(self) -> None:
        """Test generation respects max tokens limit."""
        llm = get_llm(Provider.BEDROCK)

        result = llm.generate(
            "Write a very long essay about programming.",
            max_tokens=50,
        )

        assert result is not None
        # Response should be limited
        assert len(result) < 1000

    def test_claude_model_generation(self) -> None:
        """Test Claude model specifically."""
        llm = get_llm(Provider.BEDROCK, model_id="anthropic.claude-3-5-sonnet-20241022-v2:0")

        result = llm.generate("What is Python?", max_tokens=100)

        assert result is not None
        assert "programming" in result.lower() or "language" in result.lower()


class TestBedrockEmbeddings:
    """Tests for Bedrock embeddings."""

    def test_simple_embedding(self) -> None:
        """Test basic embedding generation."""
        embed = get_embedding(Provider.BEDROCK)

        result = embed.embed("Hello, world!")

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, float) for x in result)

    def test_embedding_dimensions(self) -> None:
        """Test embedding has expected dimensions."""
        embed = get_embedding(Provider.BEDROCK)

        result = embed.embed("Test text")

        # Amazon Titan embeddings are 1024-dimensional
        assert len(result) == 1024

    def test_similar_texts_similar_embeddings(self) -> None:
        """Test that similar texts produce similar embeddings."""
        embed = get_embedding(Provider.BEDROCK)

        emb1 = embed.embed("I love coffee")
        emb2 = embed.embed("I enjoy coffee")
        emb3 = embed.embed("The weather is nice today")

        # Calculate cosine similarity
        def cosine_sim(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(x * x for x in b) ** 0.5
            return dot / (norm_a * norm_b)

        sim_similar = cosine_sim(emb1, emb2)
        sim_different = cosine_sim(emb1, emb3)

        # Similar texts should have higher similarity
        assert sim_similar > sim_different


class TestBedrockWithPersonautWorkflow:
    """Tests for Bedrock in typical Personaut workflows."""

    def test_persona_prompt_generation(self) -> None:
        """Test generating persona-like responses."""
        llm = get_llm(Provider.BEDROCK)

        system = """You are Sarah, a friendly barista. You love coffee and art.
        You speak warmly and often mention drinks. Keep responses under 50 words."""

        result = llm.generate(
            "Hi there! How's your day going?",
            system=system,
            temperature=0.7,
        )

        assert result is not None
        assert len(result) > 0

    def test_json_response_generation(self) -> None:
        """Test generating structured JSON responses."""
        llm = get_llm(Provider.BEDROCK)

        system = """Respond with valid JSON only. No other text.
        Format: {"emotion": "name", "intensity": 0.0-1.0}"""

        result = llm.generate(
            "Analyze: I'm so excited about the party!",
            system=system,
            temperature=0.0,
        )

        assert result is not None
        # Should contain JSON-like structure
        assert "{" in result or "emotion" in result.lower()
