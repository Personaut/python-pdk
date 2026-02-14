# PERSONAS.md

This document provides context, patterns, and guidelines for AI coding assistants working in this repository. For human contributors, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Product Overview

Personaut Persona Development Kit (PDK) is an open-source Python SDK for managing complex agent interactions and simulations through emotions, personality traits, and interaction management. It enables authentic agent interactions and complex simulations for synthetic surveys, probabilistic outcomes, and feedback simulation from different personas.

**Core Features:**
- **Emotion-Driven Agents**: Full emotional state modeling with 36+ emotions across 6 categories (Anger, Sad, Fear, Joy, Powerful, Peaceful)
- **Personality Traits**: 17 configurable traits (e.g., Warmth, Reasoning, Dominance) with emotion influence coefficients
- **Memory System**: Individual, shared, and private memories with vector search for similarity matching
- **Masks & Triggers**: Contextual persona switching based on emotional or situational triggers
- **Relationship Modeling**: Trust-based relationship networks between individuals
- **Simulation Types**: Conversations, surveys, outcome analysis, and live interactions
- **Prompt Generation**: Dynamic prompt assembly from emotional state, traits, memories, and context
- **State Modes**: Configurable emotional state calculation (AVERAGE, MAXIMUM, MODE, custom)
- **Model Providers**: Local embedding (Qwen3-8B default), extensible LLM providers (Gemini, Bedrock, OpenAI, Ollama)
- **Storage**: SQLite with sqlite-vec for embeddings (extensible to PostgreSQL)

## Directory Structure

```
personaut-pdk/
│
├── src/personaut/                        # Main package source code
│   ├── traits/                           # Personality trait system
│   │   ├── trait.py                      # Trait base class and definitions
│   │   ├── coefficients.py               # Emotion influence coefficients
│   │   └── defaults.py                   # Default trait definitions (17 traits)
│   │
│   ├── emotions/                         # Emotional state system
│   │   ├── emotion.py                    # Emotion definitions (36+ emotions)
│   │   ├── state.py                      # EmotionalState class
│   │   ├── categories.py                 # Emotion categories (Anger, Sad, Fear, Joy, etc.)
│   │   └── defaults.py                   # Default emotion definitions
│   │
│   ├── states/                           # State calculation and management
│   │   ├── mode.py                       # State modes (AVERAGE, MAXIMUM, MODE)
│   │   ├── calculator.py                 # State calculation logic
│   │   └── markov.py                     # Markov chain state transitions
│   │
│   ├── masks/                            # Contextual persona masks
│   │   ├── mask.py                       # Mask class definitions
│   │   ├── triggers.py                   # Mask trigger conditions
│   │   └── defaults.py                   # Default masks (professional, casual, etc.)
│   │
│   ├── models/                           # Model provider implementations
│   │   ├── model.py                      # Base model interface
│   │   ├── embeddings.py                 # Embedding model interface
│   │   ├── local_embedding.py            # Local embedding (Qwen3-8B default)
│   │   ├── gemini.py                     # Google Gemini LLM
│   │   ├── bedrock.py                    # AWS Bedrock LLM
│   │   ├── openai.py                     # OpenAI LLM
│   │   ├── ollama.py                     # Ollama local LLM
│   │   └── registry.py                   # Provider registry
│   │
│   ├── memory/                           # Memory management system
│   │   ├── memory.py                     # Memory base class
│   │   ├── individual.py                 # Individual memories
│   │   ├── shared.py                     # Shared memories (multi-perspective)
│   │   ├── private.py                    # Trust-gated private memories
│   │   ├── vector_store.py               # Vector search interface
│   │   └── sqlite_store.py               # SQLite + sqlite-vec implementation
│   │
│   ├── interfaces/                       # Storage interfaces
│   │   ├── storage.py                    # Abstract storage interface
│   │   ├── sqlite.py                     # SQLite implementation
│   │   ├── file.py                       # File-based storage
│   │   └── postgresql.py                 # PostgreSQL implementation (future)
│   │
│   ├── relationships/                    # Relationship modeling
│   │   ├── relationship.py               # Relationship class
│   │   ├── trust.py                      # Trust calculations
│   │   └── network.py                    # Relationship network graphs
│   │
│   ├── situations/                       # Situation context
│   │   ├── situation.py                  # Situation class
│   │   ├── modality.py                   # Interaction modalities (IN_PERSON, TEXT, etc.)
│   │   └── context.py                    # Situational context management
│   │
│   ├── simulations/                      # Simulation engine
│   │   ├── simulation.py                 # Base simulation class
│   │   ├── types.py                      # Simulation types (CONVERSATION, SURVEY, etc.)
│   │   ├── styles.py                     # Output styles (SCRIPT, QUESTIONNAIRE, etc.)
│   │   ├── conversation.py               # Conversation simulation
│   │   ├── survey.py                     # Survey simulation
│   │   ├── outcome.py                    # Outcome analysis simulation
│   │   └── live.py                       # Live/real-time simulation
│   │
│   ├── triggers/                         # Trigger system
│   │   ├── trigger.py                    # Base trigger class
│   │   ├── emotional.py                  # Emotional triggers
│   │   └── situational.py                # Situational triggers
│   │
│   ├── prompts/                          # Prompt generation system
│   │   ├── manager.py                    # PromptManager class
│   │   ├── builder.py                    # PromptBuilder for assembly
│   │   ├── templates/                    # Prompt templates by type
│   │   │   ├── conversation.py           # Conversation prompts
│   │   │   ├── survey.py                 # Survey response prompts
│   │   │   ├── outcome.py                # Outcome analysis prompts
│   │   │   └── base.py                   # Base template interface
│   │   ├── components/                   # Reusable prompt components
│   │   │   ├── emotional_state.py        # Emotional state formatting
│   │   │   ├── personality.py            # Trait-based personality text
│   │   │   ├── memory.py                 # Memory context injection
│   │   │   ├── relationship.py           # Relationship context
│   │   │   └── situation.py              # Situational context
│   │   └── defaults.py                   # Default templates and config
│   │
│   ├── server/                           # Live interaction server
│   │   ├── api/                          # FastAPI backend
│   │   │   ├── app.py                    # FastAPI application
│   │   │   ├── routes/                   # API route handlers
│   │   │   │   ├── individuals.py        # Individual CRUD endpoints
│   │   │   │   ├── emotions.py           # Emotional state endpoints
│   │   │   │   ├── situations.py         # Situation management
│   │   │   │   ├── relationships.py      # Relationship endpoints
│   │   │   │   ├── sessions.py           # Session management
│   │   │   │   └── websocket.py          # WebSocket handlers
│   │   │   └── schemas.py                # Pydantic request/response schemas
│   │   ├── ui/                           # Flask web UI
│   │   │   ├── app.py                    # Flask application
│   │   │   ├── views/                    # View handlers
│   │   │   │   ├── dashboard.py          # Main dashboard
│   │   │   │   ├── individuals.py        # Individual editor
│   │   │   │   ├── situations.py         # Situation configuration
│   │   │   │   ├── relationships.py      # Relationship editor
│   │   │   │   └── chat.py               # Modality interfaces
│   │   │   ├── templates/                # Jinja2 templates
│   │   │   └── static/                   # CSS, JS, assets
│   │   ├── server.py                     # LiveInteractionServer class
│   │   └── client.py                     # Python client for API
│   │
│   ├── types/                            # Type definitions
│   │   ├── individual.py                 # Individual types
│   │   ├── modality.py                   # Modality enums
│   │   ├── exceptions.py                 # Custom exceptions
│   │   └── common.py                     # Common type definitions
│   │
│   ├── __init__.py                       # Public API exports
│   └── py.typed                          # PEP 561 marker
│
├── tests/                                # Unit tests (mirrors src/)
│   ├── conftest.py                       # Pytest fixtures
│   ├── fixtures/                         # Test fixtures
│   │   ├── mock_model.py                 # Mock model for testing
│   │   ├── sample_individuals.py         # Sample individual data
│   │   └── sample_emotions.py            # Sample emotional states
│   └── personaut/                        # Tests mirror src/personaut/
│       ├── traits/
│       ├── emotions/
│       ├── states/
│       ├── masks/
│       ├── models/
│       ├── memory/
│       ├── relationships/
│       ├── simulations/
│       ├── triggers/
│       └── prompts/
│
├── tests_integ/                          # Integration tests
│   ├── conftest.py
│   ├── models/                           # Model provider tests
│   │   ├── test_model_gemini.py
│   │   └── test_model_bedrock.py
│   ├── memory/                           # Memory system tests
│   │   ├── test_sqlite_store.py
│   │   └── test_vector_search.py
│   ├── simulations/                      # Simulation tests
│   │   ├── test_conversation.py
│   │   └── test_survey.py
│   └── ...
│
├── docs/                                 # Developer documentation
│   ├── README.md                         # Docs folder overview
│   ├── STYLE_GUIDE.md                    # Code style conventions
│   ├── EMOTIONS.md                       # Emotion system guide
│   ├── TRAITS.md                         # Trait system guide
│   ├── PROMPTS.md                        # Prompt generation guide
│   ├── SIMULATIONS.md                    # Simulation patterns
│   ├── LIVE_INTERACTIONS.md              # Live interaction server
│   └── TASKS.md                          # Implementation task list
│
├── pyproject.toml                        # Project config (build, deps, tools)
├── PERSONAS.md                           # This file
└── CONTRIBUTING.md                       # Human contributor guidelines
```

### Directory Purposes

- **`src/personaut/`**: All production code
- **`tests/`**: Unit tests mirroring src/ structure
- **`tests_integ/`**: Integration tests with real model providers
- **`docs/`**: Developer documentation for contributors

**IMPORTANT**: After making changes that affect the directory structure (adding new directories, moving files, or adding significant new files), you MUST update this directory structure section to reflect the current state of the repository.

## Development Workflow

### 1. Environment Setup
```bash
hatch shell                                    # Enter dev environment
pre-commit install -t pre-commit -t commit-msg # Install hooks
```

### 2. Making Changes
1. Create feature branch
2. Implement changes following the patterns below
3. Run quality checks before committing
4. Commit with conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
5. Push and open PR

### 3. Pull Request Guidelines
When creating pull requests:

- Focus on WHY: Explain motivation and user impact, not implementation details
- Document public API changes: Show before/after code examples
- Be concise: Use prose over bullet lists; avoid exhaustive checklists
- Target senior engineers: Assume familiarity with the SDK
- Exclude implementation details: Leave these to code comments and diffs

### 4. Quality Gates
Pre-commit hooks run automatically on commit:
- Formatting (ruff)
- Linting (ruff + mypy)
- Tests (pytest)
- Commit message validation (commitizen)

All checks must pass before commit is allowed.

## Coding Patterns and Best Practices

### Logging Style
Use structured logging with field-value pairs followed by human-readable messages:

```python
logger.debug("field1=<%s>, field2=<%s> | human readable message", field1, field2)
```

**Guidelines:**
- Add context as `FIELD=<VALUE>` pairs at the beginning
- Separate pairs with commas
- Enclose values in `<>` for readability (especially for empty values)
- Use `%s` string interpolation (not f-strings) for performance
- Use lowercase messages, no punctuation
- Separate multiple statements with pipe `|`

**Good:**
```python
logger.debug("individual_id=<%s>, emotion=<%s> | updating emotional state", individual_id, emotion)
logger.info("simulation_id=<%s>, iterations=<%d> | simulation completed", sim_id, iterations)
logger.warning("trust_level=<%s>, threshold=<%s> | private memory access denied", trust, threshold)
```

**Bad:**
```python
logger.debug(f"Individual {individual_id} emotion updated to {emotion}")  # Don't use f-strings
logger.info("Simulation completed in %d iterations.", iterations)          # Don't add punctuation
```

### Type Annotations
All code must include type annotations:
- Function parameters and return types required
- No implicit optional types
- Use `typing` or `typing_extensions` for complex types
- Mypy strict mode enforced

```python
def create_individual(
    name: str,
    traits: list[Trait] | None = None,
    emotional_state: EmotionalState | None = None
) -> Individual:
    ...
```

### Docstrings
Use Google-style docstrings for all public functions, classes, and modules:

```python
def create_emotional_trigger(
    description: str,
    emotional_state_rules: list[dict],
    response: Mask | EmotionalState
) -> EmotionalTrigger:
    """Create an emotional trigger that activates based on emotional state rules.

    Emotional triggers monitor an individual's emotional state and activate
    when specified thresholds are crossed, applying either a mask or modifying
    the emotional state.

    Args:
        description: Human-readable description of the trigger condition
        emotional_state_rules: List of rules with emotion, threshold, and operator
        response: The mask to apply or emotional state modification to execute

    Returns:
        A configured EmotionalTrigger instance

    Raises:
        ValueError: When emotional_state_rules is empty or malformed

    Example:
        >>> trigger = create_emotional_trigger(
        ...     description='Unknown or unfamiliar situations',
        ...     emotional_state_rules=[{'fear': 0.8, 'threshold': '>'}],
        ...     response=Mask('stoic')
        ... )
    """
    pass
```

### Import Organization
Imports must be at the top of the file.

Imports are automatically organized by ruff/isort:
1. Standard library imports
2. Third-party imports
3. Local application imports

Use absolute imports for cross-package references, relative imports within packages.

```python
# Standard library
import logging
from datetime import datetime
from typing import Any

# Third-party
import numpy as np
from pydantic import BaseModel

# Local
from personaut.emotions import EmotionalState
from personaut.traits import Trait
from .individual import Individual
```

### File Organization
- Each major feature in its own directory
- Base classes and interfaces defined first
- Implementation-specific code in separate files
- Private modules prefixed with `_`
- Test files prefixed with `test_`

### Naming Conventions
- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: Prefix with `_`
- **Emotions**: `UPPER_SNAKE_CASE` (e.g., `HOSTILE`, `LOVING`)
- **Traits**: `UPPER_SNAKE_CASE` (e.g., `WARMTH`, `DOMINANCE`)
- **State Modes**: `UPPER_SNAKE_CASE` (e.g., `AVERAGE`, `MAXIMUM`, `MODE`)

### Error Handling
- Use custom exceptions from `personaut.types.exceptions`
- Provide clear error messages with context
- Don't swallow exceptions silently
- Validate emotional values are between 0 and 1
- Validate trust thresholds before memory access

## Domain Concepts

### Emotional State System
Emotions are grouped into 6 categories with values between 0 and 1:

| Category | Emotions |
|----------|----------|
| Anger/Mad | HOSTILE, HURT, ANGRY, SELFISH, HATEFUL, CRITICAL |
| Sad/Sadness | GUILTY, ASHAMED, DEPRESSED, LONELY, BORED, APATHETIC |
| Fear/Scared | REJECTED, CONFUSED, SUBMISSIVE, INSECURE, ANXIOUS, HELPLESS |
| Joy/Happiness | EXCITED, SENSUAL, ENERGETIC, CHEERFUL, CREATIVE, HOPEFUL |
| Powerful/Confident | PROUD, RESPECTED, APPRECIATED, IMPORTANT, FAITHFUL, SATISFIED |
| Peaceful/Calm | CONTENT, THOUGHTFUL, INTIMATE, LOVING, TRUSTING, NURTURING |

### Trait-Emotion Coefficients
Traits influence emotional state transitions. Examples:

- **WARMTH (High)**: Speeds up LOVING, TRUSTING; buffers against HOSTILE
- **WARMTH (Low)**: Increases CRITICAL, LONELY; slows NURTURING
- **EMOTIONAL_STABILITY (High)**: Buffers "Sad" and "Fear" categories; stabilizes CONTENT
- **EMOTIONAL_STABILITY (Low)**: Rapid spikes in ANXIOUS, DEPRESSED, HURT
- **DOMINANCE (High)**: Correlates with PROUD, IMPORTANT; moves toward ANGRY if challenged
- **VIGILANCE (High)**: Rapid movement toward HOSTILE, CRITICAL; blocks TRUSTING

### State Calculation Modes
- **AVERAGE**: Averages emotional values from past N interactions (default)
- **MAXIMUM**: Uses highest emotional state from past interactions
- **MODE**: Uses most common emotional state from past interactions
- **Custom**: User-defined state calculation function

### Memory Types
- **Individual**: Personal perception of an event or situation
- **Shared**: Multi-perspective memory attached to relationships
- **Private**: Trust-gated memory with trust_threshold for access

## Testing Patterns

### Unit Tests (`tests/`)
- Mirror the `src/personaut/` structure exactly
- Focus on isolated component testing
- Use mocking for external dependencies (models, databases)
- Use fixtures from `tests/fixtures/`

```python
# tests/personaut/emotions/test_state.py mirrors src/personaut/emotions/state.py
```

### Integration Tests (`tests_integ/`)
- End-to-end testing with real model providers
- Require credentials/API keys (set via environment variables)
- Organized by feature area

### Test File Naming
- Unit tests: `test_{module}.py` in `tests/personaut/{path}/`
- Integration tests: `test_{feature}.py` in `tests_integ/`

### Running Tests
```bash
hatch test                           # Run unit tests
hatch test -c                        # Run with coverage
hatch run test-integ                 # Run integration tests
hatch test tests/personaut/emotions/ # Run specific directory
hatch test --all                     # Test all Python versions (3.10-3.13)
```

### Writing Tests
- Use pytest fixtures for setup/teardown
- Use `pytest.mark.asyncio` for async tests
- Validate emotional state bounds (0-1)
- Test trait coefficient influences
- Keep tests focused and independent

## Things to Do
- Use explicit return types for all functions
- Write Google-style docstrings for public APIs
- Use structured logging format
- Add type annotations everywhere
- Use relative imports within packages
- Mirror src/ structure in tests/
- Run `hatch fmt --formatter` and `hatch fmt --linter` before committing
- Follow conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- Validate emotional values are between 0 and 1
- Document trait-emotion coefficient relationships

## Things NOT to Do
- Don't use f-strings in logging calls
- Don't use `Any` type without good reason
- Don't skip type annotations
- Don't put unit tests outside `tests/personaut/` structure
- Don't commit without running pre-commit hooks
- Don't add punctuation to log messages
- Don't use implicit optional types
- Don't allow emotional values outside 0-1 range
- Don't access private memories without trust validation

## Development Commands
```bash
# Environment
hatch shell                    # Enter dev environment

# Formatting & Linting
hatch fmt --formatter          # Format code
hatch fmt --linter             # Run linters (ruff + mypy)

# Testing
hatch test                     # Run unit tests
hatch test -c                  # Run with coverage
hatch run test-integ           # Run integration tests
hatch test --all               # Test all Python versions

# Pre-commit
pre-commit run --all-files     # Run all hooks manually

# Readiness Check
hatch run prepare              # Run all checks (format, lint, test)

# Build
hatch build                    # Build package
```

## Agent-Specific Notes

### Writing Code
- Make the SMALLEST reasonable changes to achieve the desired outcome
- Prefer simple, clean, maintainable solutions over clever ones
- Reduce code duplication, even if refactoring takes extra effort
- Match the style and formatting of surrounding code
- Fix broken things immediately when you find them
- Keep emotional state calculations consistent and predictable

### Code Comments
- Comments should explain WHAT the code does or WHY it exists
- NEVER add comments about what used to be there or how something changed
- NEVER refer to temporal context ("recently refactored", "moved")
- Keep comments concise and evergreen
- Document trait-emotion coefficient rationale

### Code Review Considerations
- Address all review comments
- Test changes thoroughly
- Update documentation if behavior changes
- Maintain test coverage
- Follow conventional commit format for fix commits
- Verify all emotional state transitions are mathematically sound

## Additional Resources
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Human contributor guidelines
- [docs/](./docs/) - Developer documentation
  - [STYLE_GUIDE.md](./docs/STYLE_GUIDE.md) - Code style conventions
  - [EMOTIONS.md](./docs/EMOTIONS.md) - Emotion system guide
  - [TRAITS.md](./docs/TRAITS.md) - Trait system guide
  - [PROMPTS.md](./docs/PROMPTS.md) - Prompt generation guide
  - [SIMULATIONS.md](./docs/SIMULATIONS.md) - Simulation patterns
  - [LIVE_INTERACTIONS.md](./docs/LIVE_INTERACTIONS.md) - Live interaction server
