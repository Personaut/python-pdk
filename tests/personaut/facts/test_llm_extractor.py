"""Tests for LLM-based fact extraction."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from personaut.facts.context import SituationalContext
from personaut.facts.llm_extractor import (
    EXTRACTION_PROMPT,
    LLMFactExtractor,
    SyncLLMFactExtractor,
)


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response: str | list[dict[str, Any]]) -> None:
        """Initialize with a fixed response."""
        if isinstance(response, list):
            self.response = json.dumps(response)
        else:
            self.response = response

    async def generate(self, _prompt: str) -> str:
        """Return the mock response."""
        return self.response


class MockSyncLLMClient:
    """Mock synchronous LLM client for testing."""

    def __init__(self, response: str | list[dict[str, Any]]) -> None:
        """Initialize with a fixed response."""
        if isinstance(response, list):
            self.response = json.dumps(response)
        else:
            self.response = response

    def generate(self, _prompt: str) -> str:
        """Return the mock response."""
        return self.response


class TestExtractionPrompt:
    """Tests for the extraction prompt template."""

    def test_prompt_contains_placeholder(self) -> None:
        """Prompt should contain {text} placeholder."""
        assert "{text}" in EXTRACTION_PROMPT

    def test_prompt_lists_categories(self) -> None:
        """Prompt should list all fact categories."""
        assert "LOCATION" in EXTRACTION_PROMPT
        assert "ENVIRONMENT" in EXTRACTION_PROMPT
        assert "TEMPORAL" in EXTRACTION_PROMPT


class TestLLMFactExtractor:
    """Tests for async LLMFactExtractor."""

    @pytest.mark.asyncio
    async def test_extract_basic_facts(self) -> None:
        """Should extract facts from LLM response."""
        response = [
            {"category": "location", "key": "city", "value": "Miami", "confidence": 0.95},
            {"category": "location", "key": "venue_type", "value": "coffee shop", "confidence": 0.9},
        ]
        client = MockLLMClient(response)
        extractor = LLMFactExtractor(llm_client=client)

        ctx = await extractor.extract("A coffee shop in Miami")

        assert ctx.get_value("city") == "Miami"
        assert ctx.get_value("venue_type") == "coffee shop"

    @pytest.mark.asyncio
    async def test_extract_with_units(self) -> None:
        """Should handle facts with units."""
        response = [
            {"category": "behavioral", "key": "wait_time", "value": 10, "unit": "minutes", "confidence": 0.8},
        ]
        client = MockLLMClient(response)
        extractor = LLMFactExtractor(llm_client=client)

        ctx = await extractor.extract("I waited 10 minutes")
        fact = ctx.get_fact("wait_time")

        assert fact is not None
        assert fact.value == 10
        assert fact.unit == "minutes"

    @pytest.mark.asyncio
    async def test_extract_with_existing_context(self) -> None:
        """Should add to existing context without duplicating."""
        response = [
            {"category": "location", "key": "city", "value": "Seattle", "confidence": 0.9},
            {"category": "environment", "key": "noise_level", "value": "quiet", "confidence": 0.8},
        ]
        client = MockLLMClient(response)
        extractor = LLMFactExtractor(llm_client=client)

        existing = SituationalContext()
        existing.add_location("city", "Miami")

        ctx = await extractor.extract("A quiet place", existing_context=existing)

        # Should keep original city, not overwrite
        assert ctx.get_value("city") == "Miami"
        # Should add new fact
        assert ctx.get_value("noise_level") == "quiet"

    @pytest.mark.asyncio
    async def test_handles_markdown_code_blocks(self) -> None:
        """Should handle response wrapped in markdown code blocks."""
        response = """```json
[{"category": "location", "key": "city", "value": "Boston"}]
```"""
        client = MockLLMClient(response)
        extractor = LLMFactExtractor(llm_client=client)

        ctx = await extractor.extract("Downtown Boston")

        assert ctx.get_value("city") == "Boston"

    @pytest.mark.asyncio
    async def test_ignores_invalid_category(self) -> None:
        """Should ignore facts with invalid categories."""
        response = [
            {"category": "invalid_category", "key": "something", "value": "test"},
            {"category": "location", "key": "city", "value": "Miami"},
        ]
        client = MockLLMClient(response)
        extractor = LLMFactExtractor(llm_client=client)

        ctx = await extractor.extract("Some text")

        assert ctx.get_value("city") == "Miami"
        assert ctx.get_value("something") is None

    @pytest.mark.asyncio
    async def test_fallback_to_regex(self) -> None:
        """Should fall back to regex on LLM error."""
        client = Mock()
        client.generate = AsyncMock(side_effect=Exception("API error"))
        extractor = LLMFactExtractor(llm_client=client, fallback_to_regex=True)

        ctx = await extractor.extract("A busy coffee shop")

        # Regex extractor should have extracted these
        assert ctx.get_value("venue_type") == "coffee shop"
        assert ctx.get_value("crowd_level") == "busy"

    @pytest.mark.asyncio
    async def test_no_fallback_raises(self) -> None:
        """Should raise on LLM error without fallback."""
        client = Mock()
        client.generate = AsyncMock(side_effect=Exception("API error"))
        extractor = LLMFactExtractor(llm_client=client, fallback_to_regex=False)

        with pytest.raises(RuntimeError, match="LLM extraction failed"):
            await extractor.extract("Some text")

    @pytest.mark.asyncio
    async def test_sets_source_to_llm(self) -> None:
        """Extracted facts should have source='llm'."""
        response = [{"category": "location", "key": "city", "value": "Miami"}]
        client = MockLLMClient(response)
        extractor = LLMFactExtractor(llm_client=client)

        ctx = await extractor.extract("Miami")
        fact = ctx.get_fact("city")

        assert fact is not None
        assert fact.source == "llm"

    def test_with_custom_prompt(self) -> None:
        """with_custom_prompt should return new extractor."""
        client = MockLLMClient([])
        extractor = LLMFactExtractor(llm_client=client)
        custom = extractor.with_custom_prompt("Custom: {text}")

        assert custom.prompt_template == "Custom: {text}"
        assert custom.llm_client is client


class TestSyncLLMFactExtractor:
    """Tests for synchronous SyncLLMFactExtractor."""

    def test_extract_basic_facts(self) -> None:
        """Should extract facts synchronously."""
        response = [
            {"category": "location", "key": "city", "value": "Miami", "confidence": 0.95},
        ]
        client = MockSyncLLMClient(response)
        extractor = SyncLLMFactExtractor(llm_client=client)

        ctx = extractor.extract("A place in Miami")

        assert ctx.get_value("city") == "Miami"

    def test_extract_with_units(self) -> None:
        """Should handle facts with units."""
        response = [
            {"category": "behavioral", "key": "queue_length", "value": 5, "unit": "people"},
        ]
        client = MockSyncLLMClient(response)
        extractor = SyncLLMFactExtractor(llm_client=client)

        ctx = extractor.extract("Line of 5 people")
        fact = ctx.get_fact("queue_length")

        assert fact is not None
        assert fact.value == 5
        assert fact.unit == "people"

    def test_handles_markdown_code_blocks(self) -> None:
        """Should handle markdown-wrapped responses."""
        response = """```
[{"category": "environment", "key": "atmosphere", "value": "cozy"}]
```"""
        client = MockSyncLLMClient(response)
        extractor = SyncLLMFactExtractor(llm_client=client)

        ctx = extractor.extract("Cozy place")

        assert ctx.get_value("atmosphere") == "cozy"

    def test_fallback_to_regex(self) -> None:
        """Should fall back to regex on error."""
        client = Mock()
        client.generate = Mock(side_effect=Exception("Error"))
        extractor = SyncLLMFactExtractor(llm_client=client, fallback_to_regex=True)

        ctx = extractor.extract("A busy coffee shop")

        assert ctx.get_value("venue_type") == "coffee shop"

    def test_no_fallback_raises(self) -> None:
        """Should raise on error without fallback."""
        client = Mock()
        client.generate = Mock(side_effect=Exception("Error"))
        extractor = SyncLLMFactExtractor(llm_client=client, fallback_to_regex=False)

        with pytest.raises(RuntimeError, match="LLM extraction failed"):
            extractor.extract("Some text")


class TestParseResponse:
    """Tests for response parsing."""

    @pytest.mark.asyncio
    async def test_invalid_json_with_fallback(self) -> None:
        """Invalid JSON should trigger fallback."""
        client = MockLLMClient("not valid json")
        extractor = LLMFactExtractor(llm_client=client, fallback_to_regex=True)

        ctx = await extractor.extract("A quiet library")

        # Should fall back to regex
        assert ctx.get_value("venue_type") == "library"

    @pytest.mark.asyncio
    async def test_non_array_json_with_fallback(self) -> None:
        """Non-array JSON should trigger fallback."""
        client = MockLLMClient('{"not": "an array"}')
        extractor = LLMFactExtractor(llm_client=client, fallback_to_regex=True)

        ctx = await extractor.extract("A busy restaurant")

        # Should fall back to regex
        assert ctx.get_value("venue_type") == "restaurant"

    @pytest.mark.asyncio
    async def test_empty_array(self) -> None:
        """Empty array should return empty context."""
        client = MockLLMClient([])
        extractor = LLMFactExtractor(llm_client=client)

        ctx = await extractor.extract("Some text")

        assert len(ctx) == 0


class TestComplexExtraction:
    """Tests for complex extraction scenarios."""

    @pytest.mark.asyncio
    async def test_coffee_shop_scenario(self) -> None:
        """Should handle realistic coffee shop scenario."""
        response = [
            {"category": "location", "key": "city", "value": "Miami, FL", "confidence": 0.95},
            {"category": "location", "key": "venue_type", "value": "coffee shop", "confidence": 0.98},
            {"category": "environment", "key": "capacity_percent", "value": 80, "unit": "percent", "confidence": 0.7},
            {"category": "behavioral", "key": "queue_length", "value": 5, "unit": "people", "confidence": 0.85},
            {"category": "behavioral", "key": "wait_time", "value": 10, "unit": "minutes", "confidence": 0.6},
            {"category": "environment", "key": "atmosphere", "value": "cozy", "confidence": 0.9},
            {"category": "sensory", "key": "sound", "value": "jazz music", "confidence": 0.8},
        ]
        client = MockLLMClient(response)
        extractor = LLMFactExtractor(llm_client=client)

        ctx = await extractor.extract(
            "We grabbed coffee at the corner spot in Miami. Super packed today, "
            "about 80% full with a line of 5. Waited like 10 minutes. "
            "Great cozy vibe with jazz playing."
        )

        assert ctx.get_value("city") == "Miami, FL"
        assert ctx.get_value("venue_type") == "coffee shop"
        assert ctx.get_value("capacity_percent") == 80
        assert ctx.get_value("queue_length") == 5
        assert ctx.get_value("wait_time") == 10
        assert ctx.get_value("atmosphere") == "cozy"
        assert ctx.get_value("sound") == "jazz music"
