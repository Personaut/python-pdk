# Style Guide

This document defines the code style conventions for the Personaut PDK. Following these guidelines ensures consistency, readability, and maintainability across the codebase.

## Quick Reference

| Category | Convention |
|----------|------------|
| Formatter | ruff |
| Linter | ruff + mypy |
| Python Version | 3.10+ |
| Type Checking | mypy strict mode |
| Docstrings | Google-style |
| Line Length | 120 characters |
| Quotes | Double quotes for strings |

## Python Version

The Personaut PDK targets Python 3.10+ and uses modern Python features:

```python
# ✅ Use union types with |
def process(value: str | None) -> bool:
    ...

# ❌ Avoid typing.Union (Python 3.9 style)
from typing import Union
def process(value: Union[str, None]) -> bool:
    ...

# ✅ Use built-in generics
def get_items() -> list[str]:
    ...

# ❌ Avoid typing generics
from typing import List
def get_items() -> List[str]:
    ...
```

## Code Formatting

### Ruff Configuration

The project uses ruff for formatting and linting. Configuration in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Running Formatters

```bash
# Format code
hatch fmt --formatter

# Run linters
hatch fmt --linter

# Run both
hatch fmt
```

## Type Annotations

All code must include complete type annotations. Mypy runs in strict mode.

### Function Signatures

```python
# ✅ Complete type annotations
def create_individual(
    name: str,
    traits: list[Trait] | None = None,
    emotional_state: EmotionalState | None = None
) -> Individual:
    """Create a new individual with optional traits and emotional state."""
    ...

# ❌ Missing return type
def create_individual(name: str):
    ...

# ❌ Missing parameter types
def create_individual(name, traits=None):
    ...
```

### Optional Parameters

```python
# ✅ Explicit None in union
def get_trait(name: str, default: Trait | None = None) -> Trait | None:
    ...

# ❌ Implicit optional (deprecated)
from typing import Optional
def get_trait(name: str, default: Optional[Trait] = None) -> Optional[Trait]:
    ...
```

### Complex Types

```python
from typing import Any, Callable, TypeVar
from collections.abc import Iterable, Mapping

# Type aliases for complex types
EmotionDict = dict[str, float]
TraitCallback = Callable[[Trait, float], None]

# Generic type variables
T = TypeVar("T")
IndividualT = TypeVar("IndividualT", bound="Individual")

# ✅ Use collections.abc for abstract types
def process_items(items: Iterable[str]) -> list[str]:
    ...

def get_config(settings: Mapping[str, Any]) -> dict[str, Any]:
    ...
```

### Avoiding Any

```python
# ✅ Use specific types
def parse_response(data: dict[str, str | int | list[str]]) -> EmotionalState:
    ...

# ❌ Avoid Any without good reason
def parse_response(data: Any) -> Any:
    ...

# ✅ When Any is necessary, document why
def load_plugin(config: Any) -> Plugin:
    """Load a plugin from configuration.
    
    Args:
        config: Plugin-specific configuration. Type varies by plugin.
    """
    ...
```

## Docstrings

Use Google-style docstrings for all public functions, classes, and modules.

### Function Docstrings

```python
def create_emotional_trigger(
    description: str,
    emotional_state_rules: list[dict[str, Any]],
    response: Mask | EmotionalState
) -> EmotionalTrigger:
    """Create an emotional trigger that activates based on emotional state rules.

    Emotional triggers monitor an individual's emotional state and activate
    when specified thresholds are crossed, applying either a mask or modifying
    the emotional state.

    Args:
        description: Human-readable description of the trigger condition.
        emotional_state_rules: List of rules with emotion, threshold, and operator.
            Each rule is a dict with keys:
            - emotion (str): Name of the emotion to monitor
            - threshold (float): Value threshold (0.0-1.0)
            - operator (str): Comparison operator ('>', '<', '>=', '<=', '==')
        response: The mask to apply or emotional state modification to execute.

    Returns:
        A configured EmotionalTrigger instance ready to be added to an individual.

    Raises:
        ValueError: When emotional_state_rules is empty or malformed.
        TypeError: When response is not a Mask or EmotionalState.

    Example:
        >>> trigger = create_emotional_trigger(
        ...     description='High fear response',
        ...     emotional_state_rules=[{'emotion': 'fear', 'threshold': 0.8, 'operator': '>'}],
        ...     response=Mask('stoic')
        ... )
        >>> individual.add_trigger(trigger)
    """
    ...
```

### Class Docstrings

```python
class EmotionalState:
    """Manages the emotional state of an individual.

    An EmotionalState contains all 36 emotions defined in the Personaut PDK,
    each with a value between 0.0 (not present) and 1.0 (maximum intensity).
    By default, all emotions are included at baseline values.

    Emotional states are mutable and change based on situational triggers,
    trait influences, and explicit modifications.

    Attributes:
        emotions: Dictionary mapping emotion names to their current values.
        baseline: The default value for newly initialized emotions.

    Example:
        >>> state = EmotionalState()
        >>> state.change_emotion('anxious', 0.7)
        >>> state.get_emotion('anxious')
        0.7
        >>> state.change_state({'hopeful': 0.5}, fill=0.1)
    """

    def __init__(self, emotions: list[str] | None = None, baseline: float = 0.0) -> None:
        """Initialize an emotional state.

        Args:
            emotions: Optional list of emotion names to include. If None, all
                36 default emotions are included.
            baseline: Initial value for all emotions. Defaults to 0.0.
        """
        ...
```

### Module Docstrings

```python
"""Emotional state management for the Personaut PDK.

This module provides the EmotionalState class and related utilities for
tracking and modifying emotional states of individuals in simulations.

The emotion system models 36 discrete emotions organized into 6 categories:
- Anger/Mad: HOSTILE, HURT, ANGRY, SELFISH, HATEFUL, CRITICAL
- Sad/Sadness: GUILTY, ASHAMED, DEPRESSED, LONELY, BORED, APATHETIC
- Fear/Scared: REJECTED, CONFUSED, SUBMISSIVE, INSECURE, ANXIOUS, HELPLESS
- Joy/Happiness: EXCITED, SENSUAL, ENERGETIC, CHEERFUL, CREATIVE, HOPEFUL
- Powerful/Confident: PROUD, RESPECTED, APPRECIATED, IMPORTANT, FAITHFUL, SATISFIED
- Peaceful/Calm: CONTENT, THOUGHTFUL, INTIMATE, LOVING, TRUSTING, NURTURING

Example:
    >>> from personaut.emotions import EmotionalState, ANXIOUS, HOPEFUL
    >>> state = EmotionalState()
    >>> state.change_state({'anxious': 0.6, 'hopeful': 0.4})
"""
```

## Logging

Use structured logging with field-value pairs followed by human-readable messages.

### Logging Format

```python
import logging

logger = logging.getLogger(__name__)

# Format: field=<value>, field=<value> | human readable message
logger.debug("individual_id=<%s>, emotion=<%s> | updating emotional state", individual_id, emotion)
logger.info("simulation_id=<%s>, iterations=<%d> | simulation completed", sim_id, iterations)
logger.warning("trust_level=<%s>, threshold=<%s> | private memory access denied", trust, threshold)
logger.error("individual_id=<%s>, error=<%s> | failed to create trait", individual_id, str(error))
```

### Logging Guidelines

```python
# ✅ Use structured format with %s interpolation
logger.debug("trait=<%s>, value=<%s> | trait value updated", trait_name, value)

# ❌ Don't use f-strings (performance penalty when logging disabled)
logger.debug(f"Trait {trait_name} updated to {value}")

# ✅ Use lowercase messages, no punctuation
logger.info("individual_id=<%s> | individual created successfully", individual_id)

# ❌ Don't add punctuation
logger.info("Individual created successfully.")

# ✅ Enclose values in <> for readability (especially empty values)
logger.debug("name=<%s>, traits=<%s> | creating individual", name, traits or "none")

# ✅ Separate multiple statements with pipe |
logger.debug("step=<1>, total=<3> | validating input | checking name format")
```

### Log Levels

| Level | Use Case |
|-------|----------|
| `DEBUG` | Detailed execution flow, variable values |
| `INFO` | Key operations (simulation started, completed) |
| `WARNING` | Unexpected but handled conditions |
| `ERROR` | Failures that prevent normal operation |
| `CRITICAL` | System-level failures |

## Error Handling

### Custom Exceptions

Use exceptions from `personaut.types.exceptions`:

```python
from personaut.types.exceptions import (
    PersonautError,          # Base exception
    ValidationError,         # Invalid input
    EmotionValueError,       # Emotion value out of range
    TraitNotFoundError,      # Unknown trait
    TrustThresholdError,     # Insufficient trust for private memory
    SimulationError,         # Simulation execution failure
)

# ✅ Use specific exceptions
def change_emotion(self, emotion: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise EmotionValueError(
            f"Emotion value must be between 0.0 and 1.0, got {value}"
        )
    ...

# ✅ Provide context in error messages
def get_trait(self, trait_name: str) -> Trait:
    if trait_name not in self._traits:
        raise TraitNotFoundError(
            f"Trait '{trait_name}' not found. Available traits: {list(self._traits.keys())}"
        )
    return self._traits[trait_name]
```

### Exception Handling

```python
# ✅ Handle specific exceptions
try:
    individual.set_trait("warmth", value)
except ValidationError as e:
    logger.warning("trait=%s | invalid value: %s", "warmth", e)
    raise

# ❌ Don't swallow exceptions silently
try:
    individual.set_trait("warmth", value)
except Exception:
    pass  # Never do this

# ✅ Re-raise with context when appropriate
try:
    response = model.generate(prompt)
except ModelError as e:
    raise SimulationError(f"Model generation failed: {e}") from e
```

## Import Organization

Imports are organized by ruff/isort automatically:

```python
# 1. Standard library imports (alphabetical)
import logging
from datetime import datetime
from typing import Any, TypeVar

# 2. Third-party imports (alphabetical)
import numpy as np
from pydantic import BaseModel, Field

# 3. Local application imports (alphabetical)
from personaut.emotions import EmotionalState
from personaut.traits import Trait
from personaut.types.exceptions import ValidationError

# 4. Relative imports within packages
from .individual import Individual
from .state import StateManager
```

### Import Guidelines

```python
# ✅ Use absolute imports for cross-package references
from personaut.emotions import EmotionalState

# ✅ Use relative imports within the same package
from .state import EmotionalState

# ❌ Avoid wildcard imports
from personaut.emotions import *

# ✅ Import specific items
from personaut.emotions import EmotionalState, ANXIOUS, HOPEFUL

# ✅ Use module import for many items
from personaut import emotions
state = emotions.EmotionalState()
```

## Naming Conventions

### General

| Type | Convention | Example |
|------|------------|---------|
| Variables | `snake_case` | `emotional_state`, `trust_level` |
| Functions | `snake_case` | `create_individual()`, `change_emotion()` |
| Classes | `PascalCase` | `EmotionalState`, `PromptBuilder` |
| Constants | `UPPER_SNAKE_CASE` | `HOSTILE`, `WARMTH`, `AVERAGE` |
| Private | Prefix `_` | `_validate_input()`, `_cache` |
| Modules | `snake_case` | `emotional_state.py`, `prompt_builder.py` |

### Domain-Specific

```python
# Emotions - UPPER_SNAKE_CASE constants
HOSTILE = "hostile"
LOVING = "loving"
ANXIOUS = "anxious"

# Traits - UPPER_SNAKE_CASE constants
WARMTH = "warmth"
DOMINANCE = "dominance"
EMOTIONAL_STABILITY = "emotional_stability"

# State Modes - UPPER_SNAKE_CASE constants
AVERAGE = "average"
MAXIMUM = "maximum"
MODE = "mode"

# Modalities - UPPER_SNAKE_CASE constants
IN_PERSON = "in_person"
TEXT_MESSAGE = "text_message"
VIDEO_CALL = "video_call"
```

### Prefixes

```python
# Private members - single underscore
class Individual:
    def __init__(self) -> None:
        self._traits: dict[str, Trait] = {}
        self._emotional_state: EmotionalState = EmotionalState()
    
    def _validate_trait(self, trait: Trait) -> None:
        """Internal validation method."""
        ...

# Dunder methods - double underscore
def __repr__(self) -> str:
    return f"Individual(name={self.name!r})"

def __eq__(self, other: object) -> bool:
    if not isinstance(other, Individual):
        return NotImplemented
    return self.id == other.id
```

## File Organization

### Module Structure

```
src/personaut/emotions/
├── __init__.py           # Public API exports
├── emotion.py            # Emotion definitions and constants
├── state.py              # EmotionalState class
├── categories.py         # Category groupings
├── defaults.py           # Default values
└── _helpers.py           # Private helper functions
```

### File Layout

```python
"""Module docstring describing purpose.

Extended description if needed.
"""

# Imports (organized by ruff)
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from personaut.types.exceptions import ValidationError

if TYPE_CHECKING:
    from personaut.traits import Trait

# Module-level constants
logger = logging.getLogger(__name__)

DEFAULT_BASELINE = 0.0
EMOTION_CATEGORIES = ["anger", "sad", "fear", "joy", "powerful", "peaceful"]

# Type aliases
EmotionDict = dict[str, float]

# Classes (main class first, helpers after)
class EmotionalState:
    """Main class docstring."""
    ...

class _EmotionValidator:
    """Private helper class."""
    ...

# Module-level functions
def create_emotional_state(emotions: list[str] | None = None) -> EmotionalState:
    """Factory function for creating emotional states."""
    ...

# Private functions
def _validate_emotion_value(value: float) -> None:
    """Validate emotion value is within bounds."""
    ...
```

## Testing

### Test File Naming

```
tests/personaut/emotions/
├── __init__.py
├── test_emotion.py       # Tests for emotion.py
├── test_state.py         # Tests for state.py
└── conftest.py           # Shared fixtures
```

### Test Structure

```python
"""Tests for EmotionalState class."""

import pytest

from personaut.emotions import EmotionalState
from personaut.types.exceptions import EmotionValueError


class TestEmotionalStateCreation:
    """Tests for EmotionalState initialization."""

    def test_create_default_state(self) -> None:
        """Creating state without arguments includes all emotions."""
        state = EmotionalState()
        assert len(state.emotions) == 36

    def test_create_with_specific_emotions(self) -> None:
        """Creating state with emotion list includes only those emotions."""
        state = EmotionalState(emotions=["anxious", "hopeful"])
        assert len(state.emotions) == 2
        assert "anxious" in state.emotions


class TestEmotionalStateModification:
    """Tests for modifying emotional state."""

    def test_change_emotion_valid_value(self) -> None:
        """change_emotion accepts values between 0 and 1."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.5)
        assert state.get_emotion("anxious") == 0.5

    def test_change_emotion_invalid_value_raises(self) -> None:
        """change_emotion raises EmotionValueError for out-of-range values."""
        state = EmotionalState()
        with pytest.raises(EmotionValueError, match="must be between 0.0 and 1.0"):
            state.change_emotion("anxious", 1.5)

    @pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
    def test_change_emotion_boundary_values(self, value: float) -> None:
        """change_emotion accepts boundary values."""
        state = EmotionalState()
        state.change_emotion("anxious", value)
        assert state.get_emotion("anxious") == value
```

### Fixtures

```python
# conftest.py
import pytest

from personaut import create_individual
from personaut.emotions import EmotionalState
from personaut.traits import WARMTH


@pytest.fixture
def empty_emotional_state() -> EmotionalState:
    """Create an emotional state with all values at 0."""
    state = EmotionalState()
    state.change_state({}, fill=0)
    return state


@pytest.fixture
def anxious_individual():
    """Create an individual with high anxiety."""
    individual = create_individual(name="Test")
    individual.emotional_state.change_state({"anxious": 0.7, "insecure": 0.5})
    return individual


@pytest.fixture
def warm_individual():
    """Create an individual with high warmth trait."""
    individual = create_individual(name="Test")
    individual.set_trait("warmth", 0.8)
    return individual
```

### Running Tests

```bash
# Run all unit tests
hatch test

# Run with coverage
hatch test -c

# Run specific directory
hatch test tests/personaut/emotions/

# Run specific test file
hatch test tests/personaut/emotions/test_state.py

# Run specific test
hatch test tests/personaut/emotions/test_state.py::TestEmotionalStateCreation::test_create_default_state

# Run integration tests
hatch run test-integ
```

## Documentation Standards

### Code Comments

```python
# ✅ Explain WHAT or WHY, not HOW
# Trust threshold determines access to private memories
if trust_level < memory.trust_threshold:
    return None

# ❌ Don't state the obvious
# Check if trust level is less than threshold
if trust_level < memory.trust_threshold:

# ✅ Document non-obvious behavior
# Coefficient is inverted for buffer effects (negative = stronger buffer)
buffer_strength = 1 - (trait_value * abs(coefficient))

# ❌ Never reference temporal context
# Recently refactored from the old system  # DON'T DO THIS
# Moved from emotions.py  # DON'T DO THIS
```

### TODO Comments

```python
# TODO(username): Description of what needs to be done
# TODO(anthony): Add support for custom emotion categories

# FIXME(username): Description of known issue
# FIXME(anthony): This calculation doesn't account for trait interactions
```

### Deprecation

```python
import warnings
from typing import deprecated

@deprecated("Use create_individual() instead")
def make_individual(name: str) -> Individual:
    """Create an individual.
    
    .. deprecated:: 0.2.0
        Use :func:`create_individual` instead.
    """
    warnings.warn(
        "make_individual is deprecated, use create_individual instead",
        DeprecationWarning,
        stacklevel=2
    )
    return create_individual(name)
```

## Pre-commit Hooks

The project uses pre-commit hooks for quality gates:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.0.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

### Installing Hooks

```bash
pre-commit install -t pre-commit -t commit-msg
```

### Commit Message Format

Use conventional commits:

```
feat: add support for custom emotions
fix: correct trait coefficient calculation
docs: update EMOTIONS.md with new examples
refactor: simplify PromptBuilder interface
test: add tests for edge cases in EmotionalState
chore: update dependencies
```

## Related Documentation

- [../PERSONAS.md](../PERSONAS.md) - Main agent guidelines with coding patterns
- [EMOTIONS.md](./EMOTIONS.md) - Emotion system conventions
- [TRAITS.md](./TRAITS.md) - Trait system conventions
- [PROMPTS.md](./PROMPTS.md) - Prompt generation patterns
- [SIMULATIONS.md](./SIMULATIONS.md) - Simulation patterns
