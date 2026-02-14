"""Personaut PDK - A Python SDK for creating and simulating AI personas.

Personaut provides tools for creating individuals with emotional states,
personality traits, memories, and relationships. These individuals can
participate in simulated conversations, surveys, and live interactions.

Quick Start:
    >>> import personaut
    >>>
    >>> # Create a simulated individual
    >>> sarah = personaut.create_individual(
    ...     name="Sarah",
    ...     description="A friendly barista who loves coffee and art",
    ... )
    >>>
    >>> # Set personality traits and emotional state
    >>> sarah.set_trait("warmth", 0.8)
    >>> sarah.set_trait("liveliness", 0.7)
    >>> sarah.change_emotion("cheerful", 0.6)
    >>>
    >>> # Create a situation
    >>> from personaut.situations import create_situation
    >>> from personaut.types import IN_PERSON
    >>>
    >>> situation = create_situation(
    ...     modality=IN_PERSON,
    ...     description="Morning at the coffee shop",
    ...     location="Downtown Miami",
    ... )
    >>>
    >>> # Run a simulation
    >>> from personaut.simulations import create_simulation
    >>> simulation = create_simulation(
    ...     situation=situation,
    ...     individuals=[sarah, customer],
    ... )
    >>> result = simulation.run(num_turns=5)

Core Functions:
    - create_individual: Create a simulated AI persona
    - create_human: Create a tracked human participant
    - create_nontracked_individual: Create an untracked entity
    - get_llm: Get an LLM model for text generation
    - get_embedding: Get an embedding model for vector operations

Submodules:
    - personaut.emotions: Emotional states and 36 distinct emotions
    - personaut.traits: Personality traits based on 16PF model
    - personaut.memory: Memory storage with semantic search
    - personaut.relationships: Trust dynamics and relationship networks
    - personaut.situations: Situation/context definitions
    - personaut.simulations: Conversation, survey, and live simulations
    - personaut.triggers: Conditional emotional activators
    - personaut.masks: Contextual persona modifiers
    - personaut.facts: Situational facts and context extraction
    - personaut.server: Live interaction server
    - personaut.interfaces: Storage interfaces (SQLite, file-based)
    - personaut.types: Common types, protocols, and exceptions
"""

from personaut._version import __version__

# Commonly used emotions (convenience imports)
from personaut.emotions import (
    ALL_EMOTIONS,
    # Commonly used emotion constants
    ANXIOUS,
    CHEERFUL,
    HOPEFUL,
    PEACEFUL_EMOTIONS,
    Emotion,
    EmotionalState,
    EmotionCategory,
)

# Core individual creation
from personaut.individuals import (
    Individual,
    create_human,
    create_individual,
    create_nontracked_individual,
)

# Storage interfaces (convenience imports)
from personaut.interfaces import (
    FileStorage,
    SQLiteStorage,
    Storage,
)

# Model providers
from personaut.models import (
    Provider,
    get_embedding,
    get_llm,
)

# Relationships (convenience imports)
from personaut.relationships import (
    Relationship,
    TrustLevel,
    create_relationship,
)

# Simulations (convenience imports)
from personaut.simulations import (
    # Type constants
    CONVERSATION,
    LIVE_CONVERSATION,
    SURVEY,
    Simulation,
    SimulationResult,
    SimulationType,
    create_simulation,
)

# Situations (convenience imports)
from personaut.situations import (
    Situation,
    create_situation,
)

# Commonly used traits (convenience imports)
from personaut.traits import (
    ALL_TRAITS,
    DOMINANCE,
    EMOTIONAL_STABILITY,
    LIVELINESS,
    # Commonly used trait constants
    WARMTH,
    Trait,
    TraitProfile,
)

# Types (convenience imports)
from personaut.types import (
    EMAIL,
    HUMAN,
    IN_PERSON,
    PHONE_CALL,
    SIMULATED,
    TEXT_MESSAGE,
    VIDEO_CALL,
    IndividualType,
    Modality,
)


__all__ = [
    # Version
    "__version__",
    # Core - Individuals
    "Individual",
    "create_individual",
    "create_human",
    "create_nontracked_individual",
    # Core - Models
    "get_llm",
    "get_embedding",
    "Provider",
    # Emotions
    "EmotionalState",
    "EmotionCategory",
    "Emotion",
    "ANXIOUS",
    "CHEERFUL",
    "HOPEFUL",
    "PEACEFUL_EMOTIONS",
    "ALL_EMOTIONS",
    # Traits
    "TraitProfile",
    "Trait",
    "WARMTH",
    "DOMINANCE",
    "EMOTIONAL_STABILITY",
    "LIVELINESS",
    "ALL_TRAITS",
    # Simulations
    "Simulation",
    "SimulationResult",
    "SimulationType",
    "create_simulation",
    "CONVERSATION",
    "SURVEY",
    "LIVE_CONVERSATION",
    # Relationships
    "Relationship",
    "create_relationship",
    "TrustLevel",
    # Situations
    "Situation",
    "create_situation",
    # Types
    "Modality",
    "IndividualType",
    "IN_PERSON",
    "TEXT_MESSAGE",
    "EMAIL",
    "PHONE_CALL",
    "VIDEO_CALL",
    "SIMULATED",
    "HUMAN",
    # Storage
    "Storage",
    "SQLiteStorage",
    "FileStorage",
]
