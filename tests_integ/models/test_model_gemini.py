"""Integration tests for Gemini model provider.

These tests require a valid GOOGLE_API_KEY environment variable.
"""

from __future__ import annotations

import os

import pytest

from personaut.models import get_llm, get_embedding, Provider


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY environment variable not set",
)


class TestGeminiTextGeneration:
    """Tests for Gemini text generation."""

    def test_simple_generation(self) -> None:
        """Test basic text generation with Gemini."""
        llm = get_llm(Provider.GEMINI)

        result = llm.generate("Say hello in exactly 3 words.")

        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)

    def test_generation_with_system_prompt(self) -> None:
        """Test generation with system instruction."""
        llm = get_llm(Provider.GEMINI)

        result = llm.generate(
            "What is 2+2?",
            system="You are a math tutor. Always respond with just the number.",
        )

        assert result is not None
        assert "4" in result

    def test_generation_with_temperature(self) -> None:
        """Test generation with temperature parameter."""
        llm = get_llm(Provider.GEMINI)

        # Low temperature should give consistent results
        result1 = llm.generate("What is the capital of France?", temperature=0.0)
        result2 = llm.generate("What is the capital of France?", temperature=0.0)

        assert "Paris" in result1
        assert "Paris" in result2

    def test_generation_with_max_tokens(self) -> None:
        """Test generation respects max tokens limit."""
        llm = get_llm(Provider.GEMINI)

        result = llm.generate(
            "Write a very long essay about programming.",
            max_tokens=50,
        )

        # Response should be limited (not exact due to tokenization)
        assert result is not None
        # Just verify we got something reasonable
        assert len(result) < 1000

    def test_long_context_generation(self) -> None:
        """Test generation with longer context."""
        llm = get_llm(Provider.GEMINI)

        long_prompt = "The quick brown fox " * 100 + "What animal was mentioned?"

        result = llm.generate(long_prompt)

        assert result is not None
        assert "fox" in result.lower()


class TestGeminiEmbeddings:
    """Tests for Gemini embeddings."""

    def test_simple_embedding(self) -> None:
        """Test basic embedding generation."""
        embed = get_embedding(Provider.GEMINI)

        result = embed.embed("Hello, world!")

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, float) for x in result)

    def test_embedding_dimensions(self) -> None:
        """Test embedding has expected dimensions."""
        embed = get_embedding(Provider.GEMINI)

        result = embed.embed("Test text")

        # Gemini text-embedding-004 produces 768-dimensional embeddings
        assert len(result) == 768

    def test_similar_texts_similar_embeddings(self) -> None:
        """Test that similar texts produce similar embeddings."""
        embed = get_embedding(Provider.GEMINI)

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
        assert sim_similar > 0.8  # Should be quite similar

    def test_empty_text_embedding(self) -> None:
        """Test embedding of empty or minimal text."""
        embed = get_embedding(Provider.GEMINI)

        result = embed.embed("")

        # Should still return a valid embedding
        assert result is not None
        assert len(result) == 768


class TestGeminiErrorHandling:
    """Tests for Gemini error handling."""

    def test_invalid_api_key_error(self) -> None:
        """Test handling of invalid API key."""
        # Temporarily set invalid key
        original_key = os.environ.get("GOOGLE_API_KEY")

        try:
            os.environ["GOOGLE_API_KEY"] = "invalid_key_12345"
            llm = get_llm(Provider.GEMINI)

            with pytest.raises(Exception):  # Should raise API error
                llm.generate("Hello")
        finally:
            if original_key:
                os.environ["GOOGLE_API_KEY"] = original_key

    def test_recovery_from_rate_limit(self) -> None:
        """Test behavior under rate limiting (informational)."""
        llm = get_llm(Provider.GEMINI)

        # Make several requests in quick succession
        results = []
        for i in range(3):
            try:
                result = llm.generate(f"Say the number {i}")
                results.append(result)
            except Exception as e:
                # Rate limit errors should be graceful
                assert "rate" in str(e).lower() or "quota" in str(e).lower()

        # At least some should succeed
        assert len(results) >= 1


class TestGeminiWithPersonautWorkflow:
    """Tests for Gemini in typical Personaut workflows."""

    def test_persona_prompt_generation(self) -> None:
        """Test generating persona-like responses."""
        llm = get_llm(Provider.GEMINI)

        system = """You are Sarah, a friendly barista. You love coffee and art.
        You speak warmly and often mention drinks. Keep responses under 50 words."""

        result = llm.generate(
            "Hi there! How's your day going?",
            system=system,
            temperature=0.7,
        )

        assert result is not None
        assert len(result) > 0

    def test_emotion_analysis(self) -> None:
        """Test analyzing emotional content."""
        llm = get_llm(Provider.GEMINI)

        system = """Analyze the emotion in the text and respond with just the emotion name.
        Choose from: happy, sad, angry, anxious, neutral."""

        result = llm.generate(
            "I just got a promotion at work! I'm thrilled!",
            system=system,
            temperature=0.0,
        )

        assert result is not None
        assert "happy" in result.lower() or "thrill" in result.lower()

    def test_conversation_continuation(self) -> None:
        """Test multi-turn conversation context."""
        llm = get_llm(Provider.GEMINI)

        # Simulate conversation history in prompt
        conversation = """
        User: My name is Alex.
        Assistant: Nice to meet you, Alex!
        User: What's my name?
        """

        result = llm.generate(conversation, temperature=0.0)

        assert "Alex" in result
