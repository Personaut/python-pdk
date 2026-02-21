# Personaut PDK

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Hatch](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

A Python SDK for creating and simulating AI personas with emotional states, personality traits, memories, and relationships.

## Overview

Personaut PDK enables you to create rich, psychologically-grounded AI personas that can participate in:

- **Conversations**: Multi-party dialogues with realistic emotional dynamics
- **Surveys**: Persona-driven questionnaire responses
- **Outcome Analysis**: Simulation-based prediction of behavioral outcomes
- **Live Interactions**: Real-time chat with modality-specific interfaces

## Features

- 🎭 **36 Emotional States** - Fine-grained emotional modeling across 6 categories
- 🧠 **17 Personality Traits** - Based on the 16PF psychological model
- 📍 **Situational Facts** - Structured context with 8 categories and LLM extraction
- 💾 **Vector Memory** - Semantic memory retrieval with trust-gated access
- 🔗 **Relationships** - Trust-based relationship dynamics
- 🎯 **Triggers & Masks** - Context-aware behavioral modifications
- 🚀 **Live Server** - FastAPI backend + Flask UI for interactive sessions

## Installation

```bash
pip install personaut
```

### Optional Dependencies

```bash
# For Gemini model provider
pip install personaut[gemini]

# For AWS Bedrock provider
pip install personaut[bedrock]

# For live interaction server
pip install personaut[server]

# For development
pip install personaut[dev]

# Install everything
pip install personaut[all]
```

## Quick Start

### Creating an Individual

```python
import personaut

# Create an individual with personality traits and emotional state
sarah = personaut.create_individual(
    name="Sarah",
    traits={"warmth": 0.8, "dominance": 0.4, "sensitivity": 0.7},
    emotional_state={"cheerful": 0.6, "creative": 0.5},
)

# Update emotional state
sarah.change_emotion("anxious", 0.3)

# Access traits
print(sarah.get_high_traits())  # [('warmth', 0.8), ...]

# Get dominant emotion (respects active mask)
print(sarah.get_dominant_emotion())  # ('cheerful', 0.6)
```

### Using Masks for Contextual Behavior

```python
from personaut.masks import PROFESSIONAL_MASK

# Add a professional mask
sarah.add_mask(PROFESSIONAL_MASK)
sarah.activate_mask("professional")

# Emotional state is now filtered through the mask
modified_state = sarah.get_emotional_state()  # Suppresses strong emotions

# Get raw state without mask
raw_state = sarah.get_raw_emotional_state()
```

### Running a Conversation Simulation

```python
import personaut

# Create individuals
sarah = personaut.create_individual(name="Sarah")
mike = personaut.create_individual(name="Mike")

# Create situation
situation = personaut.create_situation(
    modality=personaut.types.modality.TEXT_MESSAGE,
    description='Catching up after a long time'
)

# Create and run simulation
simulation = personaut.create_simulation(
    situation=situation,
    individuals=[sarah, mike],
    type=personaut.simulations.types.CONVERSATION,
    style=personaut.simulations.styles.SCRIPT
)

simulation.run(num=5, dir='./output/')
```

### Situational Facts

```python
from personaut.facts import FactExtractor, LLMFactExtractor

# Regex-based extraction (fast, deterministic)
extractor = FactExtractor()
ctx = extractor.extract(
    "A busy coffee shop in downtown Miami around 3pm. "
    "80% capacity with a line of 5 people."
)
print(ctx.get_value("venue_type"))       # "coffee shop"
print(ctx.get_value("capacity_percent")) # 80

# LLM-based extraction (richer, more nuanced)
llm_extractor = LLMFactExtractor(llm_client=your_client)
ctx = await llm_extractor.extract(
    "We grabbed coffee at the corner spot. Super packed, great vibe."
)

# Generate embedding text
print(ctx.to_embedding_text())
```

### Live Interactive Chat

```python
import personaut
from personaut.server import LiveInteractionServer

# Create server and add individual
server = LiveInteractionServer()
server.add_individual(sarah)

# Start server
server.start(api_port=8000, ui_port=5000)

# Access:
# - UI: http://localhost:5000
# - API: http://localhost:8000/docs
```

## Emotional System

The emotion system models 36 discrete emotions organized into 6 categories:

| Category | Emotions |
|----------|----------|
| **Anger/Mad** | hostile, hurt, angry, selfish, hateful, critical |
| **Sad/Sadness** | guilty, ashamed, depressed, lonely, bored, apathetic |
| **Fear/Scared** | rejected, confused, submissive, insecure, anxious, helpless |
| **Joy/Happiness** | excited, sensual, energetic, cheerful, creative, hopeful |
| **Powerful/Confident** | proud, respected, appreciated, important, faithful, satisfied |
| **Peaceful/Calm** | content, thoughtful, intimate, loving, trusting, nurturing |

```python
from personaut.emotions import EmotionalState, ANXIOUS, HOPEFUL

state = EmotionalState()
state.change_emotion(ANXIOUS, 0.6)
state.change_emotion(HOPEFUL, 0.8)

# Query dominant emotion
dominant, value = state.get_dominant()  # ('hopeful', 0.8)
```

## Personality Traits

Based on the 16PF model with 17 traits that influence emotional transitions:

```python
import personaut

individual = personaut.create_individual(name="Sarah")

# High warmth = more approachable, friendly
individual.set_trait("warmth", 0.8)

# High emotional stability = less reactive to stress
individual.set_trait("emotional_stability", 0.7)
```

## Memory System

Store and retrieve memories with emotional context and trust-gated access:

```python
from personaut.memory import (
    create_individual_memory,
    create_shared_memory,
    create_private_memory,
    InMemoryVectorStore,
    search_memories,
)

# Individual memory with situational context
memory = create_individual_memory(
    owner_id="sarah_123",
    description="Met Alex at the coffee shop",
    context=ctx,  # SituationalContext from facts extraction
    salience=0.8,
)

# Shared memory between multiple people
shared = create_shared_memory(
    description="Team dinner at the Italian restaurant",
    participant_ids=["sarah_123", "mike_456"],
    perspectives={
        "sarah_123": "Great food, but Mike was late",
        "mike_456": "Traffic was terrible",
    },
)

# Private memory with trust threshold
private = create_private_memory(
    owner_id="sarah_123",
    description="My anxiety about the presentation",
    trust_threshold=0.8,  # Only shared with high-trust individuals
)

# Store and search memories
store = InMemoryVectorStore()
store.store(memory, embedding=[...])  # Vector from embedding model

results = search_memories(
    store=store,
    query="coffee meetings",
    embed_func=my_embed_function,
    trust_level=0.5,  # Filters private memories
)
```

## Masks and Triggers

Masks modify emotional expression based on context. Triggers activate responses when conditions are met:

```python
from personaut.masks import (
    create_mask,
    PROFESSIONAL_MASK,
    STOIC_MASK,
)
from personaut.triggers import (
    create_emotional_trigger,
    create_situational_trigger,
)

# Apply professional mask in office settings
if PROFESSIONAL_MASK.should_trigger("Going to an office meeting"):
    modified_state = PROFESSIONAL_MASK.apply(emotional_state)
    # Suppresses anger, boosts composure

# Create custom mask
interview_mask = create_mask(
    name="interview",
    emotional_modifications={"anxious": -0.3, "content": 0.2},
    trigger_situations=["interview", "formal"],
)

# Emotional trigger: activate stoic mask when anxiety is high
anxiety_trigger = create_emotional_trigger(
    description="High anxiety response",
    rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
    response=STOIC_MASK,
)

if anxiety_trigger.check(emotional_state):
    calmed_state = anxiety_trigger.fire(emotional_state)

# Situational trigger: increase anxiety in dark spaces
dark_trigger = create_situational_trigger(
    description="Dark space phobia",
    keywords=["dark", "basement", "cave"],
    response={"anxious": 0.3, "helpless": 0.2},
)
```

## Relationships

Model trust dynamics between individuals and query relationship networks:

```python
from personaut.relationships import (
    create_relationship,
    RelationshipNetwork,
    get_trust_level,
    TrustLevel,
)

# Create relationship with asymmetric trust
rel = create_relationship(
    individual_ids=["sarah", "mike"],
    trust={"sarah": 0.8, "mike": 0.5},  # Sarah trusts Mike more
    history="Roommates in college for 2 years",
    relationship_type="friends",
)

# Query trust
trust = rel.get_trust("sarah", "mike")  # 0.8
mutual = rel.get_mutual_trust("sarah", "mike")  # 0.65

# Update trust after an event
rel.update_trust("mike", "sarah", 0.2, "helped during crisis")

# Check trust level
level = rel.get_trust_level("sarah", "mike")
if level == TrustLevel.HIGH:
    # Sarah will share private memories with Mike

# Build a relationship network
network = RelationshipNetwork()
network.add_relationship(rel)
network.add_relationship(create_relationship(["mike", "carol"], trust={"mike": 0.7, "carol": 0.6}))

# Find connection path
path = network.find_path("sarah", "carol")  # ['sarah', 'mike', 'carol']
path_trust = network.calculate_path_trust(path)  # Trust decays along path
```

## Situations

Define the context for simulations with modality, location, and structured context:

```python
from datetime import datetime
from personaut.situations import (
    create_situation,
    SituationContext,
    create_environment_context,
)
from personaut.types.modality import Modality

# Create a situation
situation = create_situation(
    modality=Modality.IN_PERSON,
    description="Meeting at a coffee shop to discuss a project",
    time=datetime.now(),
    location="Miami, FL",
    context={"atmosphere": "relaxed"},
)

# Query modality characteristics
if situation.is_synchronous():
    # Real-time communication expected
    traits = situation.get_modality_traits()
    print(f"Visual cues: {traits['visual_cues']}")

# Build structured context with validation
ctx = create_environment_context(
    lighting="dim",
    noise_level="quiet",
    indoor=True,
    private=True,
)
result = ctx.validate()
if result.valid:
    # Context data meets schema requirements
    pass
```


## Documentation

| Document | Description |
|----------|-------------|
| [PERSONAS.md](PERSONAS.md) | Main agent guidelines |
| [docs/EMOTIONS.md](docs/EMOTIONS.md) | Emotion system reference |
| [docs/TRAITS.md](docs/TRAITS.md) | Trait system reference |
| [docs/FACTS.md](docs/FACTS.md) | Situational context and fact extraction |
| [docs/MEMORY.md](docs/MEMORY.md) | Memory system and vector storage |
| [docs/PROMPTS.md](docs/PROMPTS.md) | Prompt generation |
| [docs/SIMULATIONS.md](docs/SIMULATIONS.md) | Simulation types |
| [docs/LIVE_INTERACTIONS.md](docs/LIVE_INTERACTIONS.md) | Server architecture |
| [docs/STYLE_GUIDE.md](docs/STYLE_GUIDE.md) | Code conventions |

## Development

```bash
# Clone repository
git clone https://github.com/personaut/python-pdk.git
cd python-pdk

# Install with dev dependencies
pip install hatch
hatch shell

# Run tests
hatch test

# Run linters
hatch fmt

# Type check
hatch run type
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guidelines.

## Requirements

- Python 3.10+
- See [pyproject.toml](pyproject.toml) for dependencies

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
