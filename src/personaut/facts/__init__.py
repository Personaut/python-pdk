"""Facts module for Personaut PDK.

This module provides structured facts and situational context for
grounding memories and simulations in concrete, extractable details.

Classes:
    Fact: A single situational fact with category, key, value.
    FactCategory: Categories of facts (location, environment, etc.).
    SituationalContext: Aggregates facts into a coherent situation.
    FactExtractor: Extracts facts from unstructured text.

Example:
    >>> from personaut.facts import SituationalContext, FactCategory
    >>> from personaut.facts import create_coffee_shop_context
    >>>
    >>> # Create a context using templates
    >>> ctx = create_coffee_shop_context(
    ...     city="Miami, FL",
    ...     venue_name="Sunrise Cafe",
    ...     capacity_percent=80,
    ...     queue_length=5,
    ... )
    >>> print(ctx.to_embedding_text())
    city: Miami, FL
    venue_type: coffee shop
    ...

    >>> # Or extract from text
    >>> from personaut.facts import FactExtractor
    >>> extractor = FactExtractor()
    >>> ctx = extractor.extract("A busy coffee shop in downtown Miami")
"""

from personaut.facts.context import (
    SituationalContext,
    create_coffee_shop_context,
    create_office_context,
)
from personaut.facts.extractor import (
    DEFAULT_PATTERNS,
    ExtractionPattern,
    FactExtractor,
)
from personaut.facts.fact import (
    BEHAVIORAL_FACTS,
    ENVIRONMENT_FACTS,
    LOCATION_FACTS,
    SENSORY_FACTS,
    SOCIAL_FACTS,
    TEMPORAL_FACTS,
    Fact,
    FactCategory,
    create_behavioral_fact,
    create_environment_fact,
    create_location_fact,
)
from personaut.facts.llm_extractor import (
    EXTRACTION_PROMPT,
    LLMClient,
    LLMFactExtractor,
    SyncLLMFactExtractor,
)


__all__ = [
    # Templates
    "BEHAVIORAL_FACTS",
    "DEFAULT_PATTERNS",
    "ENVIRONMENT_FACTS",
    "EXTRACTION_PROMPT",
    "LOCATION_FACTS",
    "SENSORY_FACTS",
    "SOCIAL_FACTS",
    "TEMPORAL_FACTS",
    # Classes
    "ExtractionPattern",
    "Fact",
    "FactCategory",
    "FactExtractor",
    "LLMClient",
    "LLMFactExtractor",
    "SituationalContext",
    "SyncLLMFactExtractor",
    # Factory functions
    "create_behavioral_fact",
    "create_coffee_shop_context",
    "create_environment_fact",
    "create_location_fact",
    "create_office_context",
]
