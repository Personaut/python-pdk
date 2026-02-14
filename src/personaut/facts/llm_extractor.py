"""LLM-based fact extraction for Personaut PDK.

This module provides LLM-powered extraction of structured facts
from unstructured text descriptions. Unlike the regex-based extractor,
LLM extraction can understand context, infer implicit facts, and
extract nuanced situational details.

Example:
    >>> from personaut.facts import LLMFactExtractor
    >>> extractor = LLMFactExtractor(llm_client)
    >>> ctx = await extractor.extract(
    ...     "We grabbed coffee at the corner spot. Super packed today, "
    ...     "must've waited 10 minutes. Great vibe though."
    ... )
    >>> ctx.get_value("venue_type")
    'coffee shop'
    >>> ctx.get_value("wait_time")
    10
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from personaut.facts.context import SituationalContext
from personaut.facts.fact import Fact, FactCategory


# Prompt template for LLM extraction
EXTRACTION_PROMPT = '''Extract structured facts from the following situational description.

Categories of facts to extract:
- LOCATION: city, venue_type, venue_name, address, neighborhood, indoor_outdoor
- ENVIRONMENT: crowd_level, capacity_percent, noise_level, lighting, cleanliness, atmosphere
- TEMPORAL: time_of_day, day_of_week, season, duration, rush_hour
- SOCIAL: people_count, group_size, age_range, formality, relationship_type
- PHYSICAL: temperature, weather
- BEHAVIORAL: queue_length, wait_time, activity_level, service_speed
- SENSORY: smell, sound, texture

Return a JSON array of extracted facts. Each fact should have:
- "category": one of the categories above (lowercase)
- "key": a short identifier for the fact type
- "value": the extracted value (string, number, or boolean)
- "unit": optional unit of measurement (e.g., "percent", "minutes", "people")
- "confidence": your confidence in this extraction (0.0 to 1.0)

Only include facts that are explicitly stated or can be reasonably inferred.
Do not invent facts that aren't supported by the text.

Text to analyze:
"""
{text}
"""

Respond with ONLY a valid JSON array, no other text.'''


class LLMClient(Protocol):
    """Protocol for LLM clients.

    Any LLM client that implements this protocol can be used
    with the LLMFactExtractor.
    """

    async def generate(self, prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The LLM's response text.
        """
        ...


@dataclass
class LLMFactExtractor:
    """Extracts structured facts from text using an LLM.

    This extractor uses an LLM to understand natural language
    and extract nuanced situational details that regex patterns
    might miss.

    Attributes:
        llm_client: An LLM client implementing the LLMClient protocol.
        prompt_template: The prompt template to use for extraction.
        fallback_to_regex: Whether to use regex extraction as fallback.

    Example:
        >>> extractor = LLMFactExtractor(my_llm_client)
        >>> ctx = await extractor.extract("A cozy cafe downtown")
        >>> print(ctx.to_embedding_text())
    """

    llm_client: LLMClient
    prompt_template: str = EXTRACTION_PROMPT
    fallback_to_regex: bool = True
    _category_map: dict[str, FactCategory] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Initialize the category mapping."""
        self._category_map = {cat.value: cat for cat in FactCategory}

    async def extract(
        self,
        text: str,
        existing_context: SituationalContext | None = None,
    ) -> SituationalContext:
        """Extract facts from text using an LLM.

        Args:
            text: The text to extract facts from.
            existing_context: Optional existing context to add facts to.

        Returns:
            A SituationalContext with extracted facts.

        Example:
            >>> extractor = LLMFactExtractor(llm_client)
            >>> ctx = await extractor.extract(
            ...     "We met at a busy coffee shop in Miami. "
            ...     "There was a line of about 5 people and it took "
            ...     "10 minutes to get our order. Nice jazz playing."
            ... )
            >>> ctx.get_value("venue_type")
            'coffee shop'
            >>> ctx.get_value("queue_length")
            5
        """
        context = existing_context.copy() if existing_context else SituationalContext()
        context.description = text[:200] if len(text) > 200 else text

        try:
            # Generate prompt and get LLM response
            prompt = self.prompt_template.format(text=text)
            response = await self.llm_client.generate(prompt)

            # Parse the JSON response
            facts_data = self._parse_response(response)

            # Add extracted facts to context
            for fact_data in facts_data:
                fact = self._create_fact(fact_data)
                if fact and fact.key not in context:
                    context.add_fact(fact)

        except Exception as e:
            # If LLM extraction fails and fallback is enabled, use regex
            if self.fallback_to_regex:
                from personaut.facts.extractor import FactExtractor

                regex_extractor = FactExtractor()
                return regex_extractor.extract(text, existing_context)
            msg = f"LLM extraction failed: {e}"
            raise RuntimeError(msg) from e

        return context

    def _parse_response(self, response: str) -> list[dict[str, Any]]:
        """Parse the LLM response into a list of fact dictionaries.

        Args:
            response: The raw LLM response.

        Returns:
            A list of fact dictionaries.

        Raises:
            ValueError: If the response cannot be parsed as JSON.
        """
        # Clean up the response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Remove markdown code block
            lines = cleaned.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
            if not isinstance(data, list):
                msg = "Expected a JSON array"
                raise ValueError(msg)
            return data
        except json.JSONDecodeError as e:
            msg = f"Failed to parse LLM response as JSON: {e}"
            raise ValueError(msg) from e

    def _create_fact(self, data: dict[str, Any]) -> Fact | None:
        """Create a Fact from a dictionary.

        Args:
            data: Dictionary with fact data from LLM.

        Returns:
            A Fact instance, or None if the data is invalid.
        """
        try:
            category_str = data.get("category", "").lower()
            if category_str not in self._category_map:
                return None

            category = self._category_map[category_str]
            key = data.get("key", "")
            value = data.get("value")

            if not key or value is None:
                return None

            return Fact(
                category=category,
                key=key,
                value=value,
                unit=data.get("unit"),
                confidence=float(data.get("confidence", 0.8)),
                source="llm",
            )
        except (KeyError, TypeError, ValueError):
            return None

    def with_custom_prompt(self, prompt_template: str) -> LLMFactExtractor:
        """Create a new extractor with a custom prompt template.

        Args:
            prompt_template: The new prompt template. Must contain {text}.

        Returns:
            A new LLMFactExtractor with the custom prompt.

        Example:
            >>> custom_extractor = extractor.with_custom_prompt(
            ...     "Extract location facts from: {text}"
            ... )
        """
        return LLMFactExtractor(
            llm_client=self.llm_client,
            prompt_template=prompt_template,
            fallback_to_regex=self.fallback_to_regex,
        )


# Synchronous wrapper for environments without async support
class SyncLLMFactExtractor:
    """Synchronous wrapper for LLMFactExtractor.

    Use this when you need to extract facts in a synchronous context.
    It wraps the async extractor and runs it in an event loop.

    Example:
        >>> extractor = SyncLLMFactExtractor(sync_llm_client)
        >>> ctx = extractor.extract("A busy coffee shop in Miami")
    """

    def __init__(
        self,
        llm_client: Any,
        prompt_template: str = EXTRACTION_PROMPT,
        fallback_to_regex: bool = True,
    ) -> None:
        """Initialize the synchronous extractor.

        Args:
            llm_client: An LLM client with a `generate(prompt)` method.
            prompt_template: The prompt template to use.
            fallback_to_regex: Whether to fall back to regex extraction.
        """
        self.llm_client = llm_client
        self.prompt_template = prompt_template
        self.fallback_to_regex = fallback_to_regex
        self._category_map = {cat.value: cat for cat in FactCategory}

    def extract(
        self,
        text: str,
        existing_context: SituationalContext | None = None,
    ) -> SituationalContext:
        """Extract facts from text using an LLM (synchronously).

        Args:
            text: The text to extract facts from.
            existing_context: Optional existing context to add facts to.

        Returns:
            A SituationalContext with extracted facts.
        """
        context = existing_context.copy() if existing_context else SituationalContext()
        context.description = text[:200] if len(text) > 200 else text

        try:
            # Generate prompt and get LLM response
            prompt = self.prompt_template.format(text=text)
            response = self.llm_client.generate(prompt)

            # Parse the JSON response
            facts_data = self._parse_response(response)

            # Add extracted facts to context
            for fact_data in facts_data:
                fact = self._create_fact(fact_data)
                if fact and fact.key not in context:
                    context.add_fact(fact)

        except Exception as e:
            if self.fallback_to_regex:
                from personaut.facts.extractor import FactExtractor

                regex_extractor = FactExtractor()
                return regex_extractor.extract(text, existing_context)
            msg = f"LLM extraction failed: {e}"
            raise RuntimeError(msg) from e

        return context

    def _parse_response(self, response: str) -> list[dict[str, Any]]:
        """Parse the LLM response into a list of fact dictionaries."""
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
            if not isinstance(data, list):
                msg = "Expected a JSON array"
                raise ValueError(msg)
            return data
        except json.JSONDecodeError as e:
            msg = f"Failed to parse LLM response as JSON: {e}"
            raise ValueError(msg) from e

    def _create_fact(self, data: dict[str, Any]) -> Fact | None:
        """Create a Fact from a dictionary."""
        try:
            category_str = data.get("category", "").lower()
            if category_str not in self._category_map:
                return None

            category = self._category_map[category_str]
            key = data.get("key", "")
            value = data.get("value")

            if not key or value is None:
                return None

            return Fact(
                category=category,
                key=key,
                value=value,
                unit=data.get("unit"),
                confidence=float(data.get("confidence", 0.8)),
                source="llm",
            )
        except (KeyError, TypeError, ValueError):
            return None


__all__ = [
    "EXTRACTION_PROMPT",
    "LLMClient",
    "LLMFactExtractor",
    "SyncLLMFactExtractor",
]
