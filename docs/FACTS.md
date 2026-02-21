# Facts System Guide

This document describes the Facts system in the Personaut PDK. Facts provide structured situational context that can be used for embedding generation, memory grounding, and realistic simulation scenarios.

## Overview

The Facts system captures concrete, extractable details about situations such as:
- **Location**: City, venue type, address, neighborhood
- **Environment**: Crowd levels, noise, atmosphere, capacity
- **Temporal**: Time of day, day of week, duration
- **Social**: Number of people, relationships, formality
- **Behavioral**: Queue lengths, wait times, activity levels
- **Sensory**: Sounds, smells, temperatures

```python
from personaut.facts import SituationalContext, FactExtractor

# Create context from structured data
ctx = SituationalContext(description="Coffee shop visit")
ctx.add_location("city", "Miami, FL")
ctx.add_location("venue_type", "coffee shop")
ctx.add_environment("capacity_percent", 80, unit="percent")
ctx.add_behavioral("queue_length", 5, unit="people")

# Or extract from natural language
extractor = FactExtractor()
ctx = extractor.extract("A busy coffee shop in downtown Miami")

# Generate embedding text
print(ctx.to_embedding_text())
```

## Fact Categories

The system organizes facts into 8 categories, each with an embedding weight that indicates relative importance for similarity matching:

| Category | Weight | Description | Example Facts |
|----------|--------|-------------|---------------|
| `LOCATION` | 1.0 | Physical location details | city, venue_type, address, neighborhood |
| `SOCIAL` | 0.9 | Social dynamics | people_count, group_size, relationship_type |
| `ENVIRONMENT` | 0.8 | Atmospheric conditions | crowd_level, noise_level, atmosphere |
| `BEHAVIORAL` | 0.8 | Observable patterns | queue_length, wait_time, activity_level |
| `TEMPORAL` | 0.7 | Time-related context | time_of_day, day_of_week, season |
| `SENSORY` | 0.7 | Perceptions | smell, sound, temperature |
| `PHYSICAL` | 0.6 | Physical conditions | temperature, weather, lighting |
| `ECONOMIC` | 0.5 | Economic factors | price_level, demand_indicators |

```python
from personaut.facts import FactCategory

# Access category properties
category = FactCategory.LOCATION
print(category.description)      # "Physical location and venue details"
print(category.embedding_weight) # 1.0
```

## Creating Facts

### Individual Facts

```python
from personaut.facts import Fact, FactCategory

# Basic fact
fact = Fact(
    category=FactCategory.LOCATION,
    key="city",
    value="Miami, FL",
)

# Fact with unit and confidence
fact = Fact(
    category=FactCategory.ENVIRONMENT,
    key="capacity_percent",
    value=80,
    unit="percent",
    confidence=0.95,
)

# Convert to embedding text
print(fact.to_embedding_text())  # "capacity_percent: 80 percent"
```

### Factory Functions

```python
from personaut.facts import (
    create_location_fact,
    create_environment_fact,
    create_behavioral_fact,
)

city = create_location_fact("city", "Miami, FL")
capacity = create_environment_fact("capacity", 80, unit="percent")
queue = create_behavioral_fact("queue_length", 5, unit="people")
```

## Situational Context

`SituationalContext` aggregates multiple facts into a coherent situation representation:

```python
from personaut.facts import SituationalContext

# Create empty context
ctx = SituationalContext(description="Morning visit to a coffee shop")

# Add facts by category
ctx.add_location("city", "Miami, FL")
ctx.add_location("venue_type", "coffee shop")
ctx.add_location("venue_name", "Sunrise Cafe")

ctx.add_environment("capacity_percent", 80, unit="percent")
ctx.add_environment("noise_level", "moderate")
ctx.add_environment("atmosphere", "cozy")

ctx.add_behavioral("queue_length", 5, unit="people")
ctx.add_behavioral("wait_time", 8, unit="minutes")

ctx.add_temporal("time_of_day", "morning")
ctx.add_temporal("day_of_week", "Saturday")

ctx.add_sensory("smell", "fresh coffee")
ctx.add_sensory("sound", "jazz music")
```

### Retrieving Facts

```python
# Get a specific fact
city_fact = ctx.get_fact("city")
print(city_fact.value)  # "Miami, FL"

# Get just the value
city = ctx.get_value("city")              # "Miami, FL"
unknown = ctx.get_value("unknown", "N/A") # "N/A" (default)

# Get all facts in a category
location_facts = ctx.get_facts_by_category(FactCategory.LOCATION)
```

### Context Templates

For common scenarios, use template functions:

```python
from personaut.facts import create_coffee_shop_context, create_office_context

# Coffee shop with common defaults
ctx = create_coffee_shop_context(
    city="Miami, FL",
    venue_name="Sunrise Cafe",
    capacity_percent=80,
    queue_length=5,
    noise_level="moderate",
    time_of_day="morning",
)

# Office environment
ctx = create_office_context(
    city="New York, NY",
    company_name="Acme Corp",
    floor=12,
    people_count=25,
    formality="professional",
)
```

## Embedding Generation

Facts are designed to generate text suitable for embedding-based similarity matching:

### Basic Embedding Text

```python
ctx = create_coffee_shop_context(
    city="Miami, FL",
    capacity_percent=80,
    queue_length=5,
)

print(ctx.to_embedding_text())
# Output:
# city: Miami, FL
# venue_type: coffee shop
# indoor_outdoor: indoor
# capacity_percent: 80 percent
# noise_level: moderate
# atmosphere: casual
# queue_length: 5 people
```

### Filtered Embedding

```python
# Include only specific categories
text = ctx.to_embedding_text(include_categories=[
    FactCategory.LOCATION,
    FactCategory.ENVIRONMENT,
])
```

### Weighted Embedding Pairs

For sophisticated embedding strategies that weight different facts:

```python
pairs = ctx.to_weighted_embedding_pairs()
# Returns: [
#   ("city: Miami, FL", 1.0),        # LOCATION weight
#   ("venue_type: coffee shop", 1.0),
#   ("capacity_percent: 80 percent", 0.8),  # ENVIRONMENT weight
#   ...
# ]

# Use with weighted average embedding
embeddings = []
weights = []
for text, weight in pairs:
    embedding = your_embedding_model.embed(text)
    embeddings.append(embedding)
    weights.append(weight)

# Compute weighted average
weighted_embedding = np.average(embeddings, weights=weights, axis=0)
```

## Fact Extraction

### Regex-Based Extraction

Fast, deterministic extraction using pattern matching:

```python
from personaut.facts import FactExtractor

extractor = FactExtractor()

text = """
We met at a busy coffee shop in downtown Miami around 3pm. 
It was about 80% capacity with a line of 5 people waiting.
The atmosphere was relaxed despite being busy.
"""

ctx = extractor.extract(text)

print(ctx.get_value("venue_type"))       # "coffee shop"
print(ctx.get_value("crowd_level"))      # "busy"
print(ctx.get_value("capacity_percent")) # 80
print(ctx.get_value("queue_length"))     # 5
print(ctx.get_value("atmosphere"))       # "relaxed"
```

### Custom Patterns

Add domain-specific extraction patterns:

```python
from personaut.facts import FactExtractor, ExtractionPattern, FactCategory

extractor = FactExtractor()

# Add custom pattern for parking
parking_pattern = ExtractionPattern(
    category=FactCategory.LOCATION,
    key="parking",
    pattern=r"(free|paid|no|ample|limited)\s+parking",
)
extractor.add_pattern(parking_pattern)

ctx = extractor.extract("Great cafe with free parking")
print(ctx.get_value("parking"))  # "free"
```

### LLM-Based Extraction

For richer, more nuanced extraction from natural language:

```python
from personaut.facts import LLMFactExtractor

# Async extraction (recommended for production)
extractor = LLMFactExtractor(llm_client=your_llm_client)

ctx = await extractor.extract(
    "We grabbed coffee at the corner spot in Miami. Super packed today, "
    "about 80% full with a line of 5. Waited like 10 minutes. Great vibe "
    "with jazz playing."
)

print(ctx.get_value("city"))             # "Miami, FL"
print(ctx.get_value("venue_type"))       # "coffee shop"
print(ctx.get_value("capacity_percent")) # 80
print(ctx.get_value("queue_length"))     # 5
print(ctx.get_value("wait_time"))        # 10
print(ctx.get_value("atmosphere"))       # "cozy"
print(ctx.get_value("sound"))            # "jazz music"
```

### Sync LLM Extraction

For simpler use cases without async:

```python
from personaut.facts import SyncLLMFactExtractor

extractor = SyncLLMFactExtractor(llm_client=your_sync_client)
ctx = extractor.extract("A busy coffee shop downtown")
```

### LLM Client Protocol

Any LLM client implementing this protocol works:

```python
from personaut.facts import LLMClient

class MyLLMClient(LLMClient):
    async def generate(self, prompt: str) -> str:
        # Call your LLM provider
        response = await my_llm_api.complete(prompt)
        return response.text
```

### Fallback Behavior

LLM extractors automatically fall back to regex extraction on failure:

```python
# Fallback enabled (default)
extractor = LLMFactExtractor(
    llm_client=your_client,
    fallback_to_regex=True,  # Default
)

# Disable fallback (raises RuntimeError on failure)
extractor = LLMFactExtractor(
    llm_client=your_client,
    fallback_to_regex=False,
)
```

### Custom Prompts

Customize the extraction prompt for domain-specific needs:

```python
custom_prompt = '''Extract restaurant-specific facts from:
"""
{text}
"""

Return JSON array with category, key, value, and confidence.'''

custom_extractor = extractor.with_custom_prompt(custom_prompt)
ctx = await custom_extractor.extract("Great Italian place, amazing pasta")
```

## Serialization

### To/From Dictionary

```python
# Save to dictionary
data = ctx.to_dict()

# Restore from dictionary
restored = SituationalContext.from_dict(data)
```

### Individual Facts

```python
# Fact to dictionary
fact = Fact(FactCategory.LOCATION, "city", "Miami")
data = fact.to_dict()
# {"category": "location", "key": "city", "value": "Miami", ...}

# Restore fact
fact = Fact.from_dict(data)
```

## Context Operations

### Copy and Merge

```python
# Create independent copy
ctx_copy = ctx.copy()

# Merge two contexts
morning_ctx = create_coffee_shop_context(city="Miami, FL")
afternoon_ctx = SituationalContext()
afternoon_ctx.add_temporal("time_of_day", "afternoon")

combined = morning_ctx.merge(afternoon_ctx)
```

### Iteration and Membership

```python
# Iterate over facts
for fact in ctx:
    print(f"{fact.key}: {fact.value}")

# Check if fact exists
if "city" in ctx:
    print("City is known")

# Get count
print(f"Total facts: {len(ctx)}")
```

## Integration with Memory System

Facts provide structured context for memories:

```python
# Create memory with situational context
memory = Memory(
    description="First date at the coffee shop",
    emotional_state=EmotionalState({"cheerful": 0.8, "anxious": 0.4}),
    context=create_coffee_shop_context(
        city="Miami, FL",
        venue_name="Sunrise Cafe",
        atmosphere="romantic",
        time_of_day="evening",
    ),
)

# Use context for embedding-based retrieval
embedding_text = memory.context.to_embedding_text()
embedding = embed_model.embed(embedding_text)
```

## Integration with Simulations

Facts enhance simulation realism:

```python
from personaut.facts import create_coffee_shop_context

# Create rich situational context
context = create_coffee_shop_context(
    city="Miami, FL",
    venue_name="Sunrise Cafe",
    capacity_percent=85,
    queue_length=7,
    noise_level="loud",
    atmosphere="bustling",
    time_of_day="morning",
)

# Use in simulation
situation = personaut.situation.create_situation(
    type=personaut.types.modality.IN_PERSON,
    description=context.description,
    location=context.get_value("city"),
    context=context.to_dict(),  # Full situational context
)
```

## API Reference

### Classes

| Class | Description |
|-------|-------------|
| `Fact` | Immutable dataclass representing a single situational fact |
| `FactCategory` | Enum of 8 fact categories with weights |
| `SituationalContext` | Aggregates facts into coherent situation |
| `FactExtractor` | Regex-based fact extraction |
| `ExtractionPattern` | Custom extraction pattern definition |
| `LLMFactExtractor` | Async LLM-powered extraction |
| `SyncLLMFactExtractor` | Sync LLM-powered extraction |
| `LLMClient` | Protocol for LLM client implementations |

### Factory Functions

| Function | Description |
|----------|-------------|
| `create_location_fact()` | Create LOCATION category fact |
| `create_environment_fact()` | Create ENVIRONMENT category fact |
| `create_behavioral_fact()` | Create BEHAVIORAL category fact |
| `create_coffee_shop_context()` | Template for coffee shop scenarios |
| `create_office_context()` | Template for office scenarios |

### Constants

| Constant | Description |
|----------|-------------|
| `LOCATION_FACTS` | Template dict of location fact keys |
| `ENVIRONMENT_FACTS` | Template dict of environment fact keys |
| `BEHAVIORAL_FACTS` | Template dict of behavioral fact keys |
| `SENSORY_FACTS` | Template dict of sensory fact keys |
| `SOCIAL_FACTS` | Template dict of social fact keys |
| `TEMPORAL_FACTS` | Template dict of temporal fact keys |
| `DEFAULT_PATTERNS` | List of default extraction patterns |
| `EXTRACTION_PROMPT` | Default LLM extraction prompt template |
