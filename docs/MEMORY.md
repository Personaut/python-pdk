# Memory System

The Memory module provides semantic memory storage with emotional context, trust-gated access control, and vector-based retrieval.

## Overview

Personaut's memory system models how individuals remember and share experiences:

- **Individual Memories**: Personal experiences with salience scoring
- **Shared Memories**: Multi-participant memories with perspective tracking  
- **Private Memories**: Trust-gated secrets with disclosure tracking
- **Vector Storage**: SQLite-based similarity search with embedding support

## Memory Types

### Individual Memory

Personal memories belonging to a single individual:

```python
from personaut.memory import create_individual_memory
from personaut.facts import FactExtractor

# Extract situational context
extractor = FactExtractor()
ctx = extractor.extract("Coffee shop in Miami, 3pm, very crowded")

# Create memory with context
memory = create_individual_memory(
    owner_id="sarah_123",
    description="Met Alex for the first time at the cafe",
    context=ctx,
    salience=0.8,  # How memorable (0.0-1.0)
)

# Check ownership
memory.belongs_to("sarah_123")  # True
```

### Shared Memory

Memories involving multiple participants, each with their own perspective:

```python
from personaut.memory import create_shared_memory
from personaut.emotions.state import EmotionalState

memory = create_shared_memory(
    description="Team dinner at the Italian restaurant",
    participant_ids=["alice", "bob", "carol"],
    perspectives={
        "alice": "Great food, but Bob was being annoying",
        "bob": "Fun evening with old friends",
        "carol": "Wish we'd picked a quieter place",
    },
)

# Add emotional state for a participant
alice_state = EmotionalState()
alice_state.change_emotion("cheerful", 0.7)
alice_state.change_emotion("excited", 0.6)
memory.set_emotional_state("alice", alice_state)

# Get perspective-specific embedding text
text = memory.to_embedding_text(perspective_id="alice")
```

### Private Memory

Trust-gated memories only shared with sufficiently trusted individuals:

```python
from personaut.memory import create_private_memory

memory = create_private_memory(
    owner_id="sarah_123",
    description="My anxiety about the upcoming presentation",
    trust_threshold=0.8,  # Requires high trust to access
    tags=["anxiety", "work"],
)

# Check access
memory.can_access(trust_level=0.5)  # False
memory.can_access(trust_level=0.9)  # True

# Track disclosures
memory.record_disclosure()
print(memory.disclosure_count)  # 1

# Get sensitivity level
memory.get_sensitivity_level()  # "highly sensitive"
```

## Vector Storage

The memory system uses a **local-first embedding strategy** for consistency across all LLM providers and to eliminate API costs.

### Default Embedding Model

The PDK uses **Qwen3-Embedding-8B** as the default embedding model:

- **Local execution**: No API calls, no costs, works offline
- **High quality**: 4096-dimensional embeddings, excellent multilingual support
- **Consistency**: Same embeddings regardless of which LLM provider you use

```python
from personaut.models import get_embedding

# Get the default local embedding model
embed = get_embedding()  # Returns LocalEmbedding with Qwen3-8B

# Generate embeddings
vector = embed.embed("Met Alex for the first time at the cafe")
print(f"Dimension: {embed.dimension}")  # 4096

# Batch embedding for efficiency
vectors = embed.embed_batch([
    "Memory 1: Coffee shop meeting",
    "Memory 2: Team dinner",
    "Memory 3: Project kickoff",
])
```

**Supported Local Models**:

| Model | Dimensions | Size | Use Case |
|-------|------------|------|----------|
| `Qwen/Qwen3-Embedding-8B` | 4096 | ~16GB | **Default** - Best quality |
| `BAAI/bge-large-en-v1.5` | 1024 | ~1.3GB | Good balance |
| `all-MiniLM-L6-v2` | 384 | ~80MB | Fast, lightweight |

### In-Memory Store

Fast, ephemeral storage for testing and development:

```python
from personaut.memory import InMemoryVectorStore, Memory

store = InMemoryVectorStore()

# Store memory with embedding
memory = Memory(description="Test memory")
embedding = [0.1, 0.2, 0.3, ...]  # From embedding model
store.store(memory, embedding)

# Search by similarity
results = store.search(
    query_embedding=[0.15, 0.18, 0.32, ...],
    limit=10,
)
for memory, similarity in results:
    print(f"{memory.description}: {similarity:.3f}")
```

### SQLite Store

Persistent storage with optional `sqlite-vec` acceleration:

```python
from pathlib import Path
from personaut.memory import SQLiteVectorStore

# Create persistent store
with SQLiteVectorStore(Path("./memories.db")) as store:
    # Store memories
    store.store(memory, embedding)
    
    # Search with owner filter
    results = store.search(
        query_embedding=query_vec,
        limit=10,
        owner_id="sarah_123",  # Only this owner's memories
    )
    
    # Get by owner
    sarah_memories = store.get_by_owner("sarah_123")
```

## Memory Search

High-level search functions that integrate with the Facts system:

### Basic Search

```python
from personaut.memory import search_memories, InMemoryVectorStore

def my_embed_func(text: str) -> list[float]:
    # Your embedding model here
    return model.encode(text)

store = InMemoryVectorStore()
# ... populate store ...

results = search_memories(
    store=store,
    query="coffee shop meetings",
    embed_func=my_embed_func,
    limit=10,
    trust_level=0.5,  # Filter private memories
)
```

### Context-Based Search

Search using extracted situational context:

```python
from personaut.memory import get_relevant_memories
from personaut.facts import SituationalContext

# Build or extract context
ctx = SituationalContext()
ctx.add_location("city", "Miami")
ctx.add_location("venue_type", "coffee shop")
ctx.add_temporal("time_of_day", "afternoon")

results = get_relevant_memories(
    store=store,
    context=ctx,
    embed_func=my_embed_func,
    limit=10,
)
```

### Extract-and-Search

Automatically extract facts from text before searching:

```python
from personaut.memory import extract_and_search

# Natural language query
results = extract_and_search(
    store=store,
    text="We met at a busy coffee shop in downtown Miami around 3pm",
    embed_func=my_embed_func,
    limit=10,
)
```

### Trust-Based Filtering

Filter memories based on access control:

```python
from personaut.memory import filter_accessible_memories

all_memories = [public_mem, private_mem_low, private_mem_high]

# With medium trust
accessible = filter_accessible_memories(
    memories=all_memories,
    trust_level=0.5,
)
# Returns: public_mem, private_mem_low (threshold < 0.5)
```

## Embedding Text Generation

Each memory type generates optimized text for embedding:

```python
memory = create_individual_memory(
    owner_id="sarah_123",
    description="Had lunch with Alex at the new Italian place",
    context=ctx,  # Includes location: downtown, venue: restaurant
    emotional_state=happy_state,  # cheerful: 0.8
)

text = memory.to_embedding_text()
# Output:
# Had lunch with Alex at the new Italian place
# Emotional state: cheerful (high)
# Location: downtown restaurant
# Temporal: lunch time
```

## Serialization

Memories support full serialization for storage:

```python
# To dictionary
data = memory.to_dict()

# From dictionary
restored = Memory.from_dict(data)

# Type-specific restoration
individual = IndividualMemory.from_dict(data)
shared = SharedMemory.from_dict(data)
private = PrivateMemory.from_dict(data)
```

## Best Practices

### Memory Salience

Use salience to prioritize important memories:
- **0.9-1.0**: Life-changing events
- **0.7-0.9**: Significant moments
- **0.4-0.7**: Notable experiences
- **0.1-0.4**: Routine events

### Trust Thresholds

Choose appropriate thresholds for private memories:
- **0.9+**: Deeply personal secrets
- **0.7-0.9**: Sensitive personal information
- **0.5-0.7**: Moderately private details
- **0.3-0.5**: Slightly private preferences

### Context Integration

Always add situational context when available:

```python
from personaut.facts import FactExtractor

extractor = FactExtractor()
ctx = extractor.extract(situational_description)

memory = create_individual_memory(
    owner_id=owner,
    description=what_happened,
    context=ctx,  # Rich context improves retrieval
)
```

## API Reference

### Classes

| Class | Description |
|-------|-------------|
| `Memory` | Base memory class with description, emotional state, context |
| `IndividualMemory` | Personal memory with owner and salience |
| `SharedMemory` | Multi-participant memory with perspectives |
| `PrivateMemory` | Trust-gated memory with disclosure tracking |
| `InMemoryVectorStore` | Fast in-memory vector storage |
| `SQLiteVectorStore` | Persistent SQLite-based storage |

### Factory Functions

| Function | Description |
|----------|-------------|
| `create_memory()` | Create base memory |
| `create_individual_memory()` | Create personal memory |
| `create_shared_memory()` | Create multi-participant memory |
| `create_private_memory()` | Create trust-gated memory |

### Search Functions

| Function | Description |
|----------|-------------|
| `search_memories()` | Text-based similarity search |
| `get_relevant_memories()` | Context-based retrieval |
| `extract_and_search()` | Extract facts then search |
| `filter_accessible_memories()` | Trust-based filtering |

## See Also

- [FACTS.md](FACTS.md) - Situational context extraction
- [EMOTIONS.md](EMOTIONS.md) - Emotional state system
- [TASKS.md](TASKS.md) - Implementation tasks
