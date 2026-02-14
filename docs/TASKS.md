# Personaut PDK Implementation Task List

This document provides a comprehensive, ordered task list to build out all functionality documented in the Personaut PDK. Each task includes detailed subtasks, documentation references, and acceptance criteria.

**Target**: PyPI deployment-ready package

---

## Phase 1: Project Foundation ✅ COMPLETE

### Task 1.1: Project Setup and Configuration ✅
**Documentation**: [PERSONAS.md](../PERSONAS.md), [STYLE_GUIDE.md](STYLE_GUIDE.md)

**Subtasks**:
1. [x] Create `pyproject.toml` with:
   - Package metadata (name: `personaut`, version: `0.1.0`)
   - Python version requirement: `>=3.10`
   - Build system: `hatchling`
   - Dependencies: `pydantic>=2.0`, `numpy`, `sqlalchemy`, `sqlite-vec`, `httpx`
   - Optional dependencies groups: `[dev]`, `[server]`, `[bedrock]`, `[gemini]`
   - Ruff configuration (line-length: 120, target-version: py310)
   - Mypy configuration (strict mode)
   - Pytest configuration
   - Commitizen configuration

2. [x] Create `.pre-commit-config.yaml` with:
   - ruff (format + lint)
   - mypy
   - commitizen (commit-msg)

3. [x] Create directory structure per PERSONAS.md:
   ```
   src/personaut/
   ├── __init__.py
   ├── py.typed
   ├── emotions/
   ├── traits/
   ├── states/
   ├── masks/
   ├── models/
   ├── memory/
   ├── interfaces/
   ├── relationships/
   ├── situations/
   ├── simulations/
   ├── triggers/
   ├── prompts/
   ├── server/
   └── types/
   ```

4. [x] Create `tests/` directory structure mirroring `src/personaut/`

5. [x] Create `tests/conftest.py` with base fixtures

6. [x] Create `CONTRIBUTING.md`

7. [x] Initialize git repository and make initial commit

**Acceptance Criteria**: ✅ All verified
- ✅ `hatch shell` enters dev environment
- ✅ `pre-commit install` succeeds
- ✅ `hatch test` runs (2 tests pass)
- ✅ `hatch fmt` runs without errors
- ✅ `mypy src/` passes (16 files, no issues)


---

## Phase 2: Core Type System ✅ COMPLETE

### Task 2.1: Exception Definitions ✅
**Documentation**: [STYLE_GUIDE.md](STYLE_GUIDE.md) (Error Handling section)

**File**: `src/personaut/types/exceptions.py`

**Subtasks**:
1. [x] Create base `PersonautError(Exception)` class
2. [x] Create `ValidationError(PersonautError)` for invalid input
3. [x] Create `EmotionValueError(ValidationError)` for emotion values outside 0-1
4. [x] Create `TraitNotFoundError(PersonautError)` for unknown traits
5. [x] Create `TrustThresholdError(PersonautError)` for insufficient trust
6. [x] Create `SimulationError(PersonautError)` for simulation failures
7. [x] Create `ModelError(PersonautError)` for model provider errors
8. [x] Create `MemoryError(PersonautError)` for memory system errors
9. [x] Add docstrings following Google style
10. [x] BONUS: Added `EmotionNotFoundError`, `TraitValueError`, `ConfigurationError`

**Tests**: `tests/personaut/types/test_exceptions.py` ✅ (27 tests)
- ✅ Test exception inheritance
- ✅ Test exception messages include context

---

### Task 2.2: Common Type Definitions ✅
**Documentation**: [STYLE_GUIDE.md](STYLE_GUIDE.md) (Type Annotations section)

**File**: `src/personaut/types/common.py`

**Subtasks**:
1. [x] Define type aliases:
   ```python
   EmotionDict = dict[str, float]
   TraitDict = dict[str, float]
   TrustDict = dict[str, float]
   EmbeddingVector = list[float]
   JsonDict = dict[str, Any]
   ```
2. [x] Define TypeVars for generics (T, T_co, IndividualT, MemoryT)
3. [x] Define Protocol classes for interfaces:
   - IndividualProtocol, EmotionalStateProtocol, MemoryProtocol
   - ModelProtocol, EmbeddingModelProtocol, VectorStoreProtocol
4. [x] Define callback types (OnTurnCallback, OnCompleteCallback, OnEmotionChangeCallback)

**File**: `src/personaut/types/modality.py`

**Subtasks**:
1. [x] Create `Modality` enum with values:
   - `IN_PERSON`
   - `TEXT_MESSAGE`
   - `EMAIL`
   - `PHONE_CALL`
   - `VIDEO_CALL`
   - `SURVEY`
2. [x] Add description property for each modality
3. [x] Add UI template mapping
4. [x] Add is_synchronous, has_visual_cues, has_audio_cues, formality_level properties
5. [x] Add parse_modality() utility function

**Tests**: `tests/personaut/types/test_modality.py` ✅ (20 tests)
**Tests**: `tests/personaut/types/test_common.py` ✅ (14 tests)

---

### Task 2.3: Individual Types ✅
**Documentation**: [PERSONAS.md](../PERSONAS.md) (Domain Concepts section)

**File**: `src/personaut/types/individual.py`

**Subtasks**:
1. [x] Define `IndividualType` enum: `SIMULATED`, `HUMAN`, `NONTRACKED`
2. [x] Add properties: has_emotional_state, has_memory, generates_responses, requires_context
3. [x] Add parse_individual_type() utility function
4. [x] Individual protocol defined in common.py

**Tests**: `tests/personaut/types/test_individual.py` ✅ (22 tests)

**Phase 2 Totals**: 93 tests passing, 20 source files, mypy clean


## Phase 3: Emotion System ✅ COMPLETE

### Task 3.1: Emotion Definitions ✅
**Documentation**: [EMOTIONS.md](EMOTIONS.md), [STYLE_GUIDE.md](STYLE_GUIDE.md)

**File**: `src/personaut/emotions/emotion.py`

**Subtasks**:
1. [x] Define all 36 emotion constants (UPPER_SNAKE_CASE):
   - Anger/Mad: `HOSTILE`, `HURT`, `ANGRY`, `SELFISH`, `HATEFUL`, `CRITICAL`
   - Sad/Sadness: `GUILTY`, `ASHAMED`, `DEPRESSED`, `LONELY`, `BORED`, `APATHETIC`
   - Fear/Scared: `REJECTED`, `CONFUSED`, `SUBMISSIVE`, `INSECURE`, `ANXIOUS`, `HELPLESS`
   - Joy/Happiness: `EXCITED`, `SENSUAL`, `ENERGETIC`, `CHEERFUL`, `CREATIVE`, `HOPEFUL`
   - Powerful/Confident: `PROUD`, `RESPECTED`, `APPRECIATED`, `IMPORTANT`, `FAITHFUL`, `SATISFIED`
   - Peaceful/Calm: `CONTENT`, `THOUGHTFUL`, `INTIMATE`, `LOVING`, `TRUSTING`, `NURTURING`

2. [x] Create `Emotion` class with:
   - `name: str`
   - `category: str`
   - `description: str`

3. [x] Create `ALL_EMOTIONS: list[str]` containing all 36

4. [x] Export constants via `__all__`

5. [x] BONUS: Added `EMOTION_METADATA` registry, `get_emotion_metadata()`, `is_valid_emotion()`

**Tests**: `tests/personaut/emotions/test_emotion.py` ✅ (21 tests)
- ✅ Test all 36 emotions are defined
- ✅ Test emotion values are lowercase strings
- ✅ Test ALL_EMOTIONS contains exactly 36 items

---

### Task 3.2: Emotion Categories ✅
**Documentation**: [EMOTIONS.md](EMOTIONS.md) (Emotion Categories section)

**File**: `src/personaut/emotions/categories.py`

**Subtasks**:
1. [x] Define `EmotionCategory` enum:
   - `ANGER`, `SAD`, `FEAR`, `JOY`, `POWERFUL`, `PEACEFUL`

2. [x] Create `CATEGORY_EMOTIONS: dict[EmotionCategory, list[str]]` mapping

3. [x] Create `get_category(emotion: str) -> EmotionCategory` function

4. [x] Create `get_emotions_in_category(category: EmotionCategory) -> list[str]`

5. [x] BONUS: Added `description`, `is_positive`, `is_negative`, `valence`, `arousal` properties
6. [x] BONUS: Added `get_positive_emotions()`, `get_negative_emotions()`, `parse_category()`

**Tests**: `tests/personaut/emotions/test_categories.py` ✅ (34 tests)
- ✅ Test each emotion maps to correct category
- ✅ Test category contains correct emotions

---

### Task 3.3: EmotionalState Class ✅
**Documentation**: [EMOTIONS.md](EMOTIONS.md) (EmotionalState Class section)

**File**: `src/personaut/emotions/state.py`

**Subtasks**:
1. [x] Create `EmotionalState` class with:
   ```python
   def __init__(self, emotions: list[str] | None = None, baseline: float = 0.0) -> None
   ```
   - If `emotions` is None, include ALL 36 emotions
   - If `emotions` is provided, include only those emotions
   - Initialize all included emotions to `baseline` value

2. [x] Implement `change_emotion(emotion: str, value: float) -> None`:
   - Validate value is between 0.0 and 1.0
   - Raise `EmotionValueError` if out of range
   - Update the emotion value

3. [x] Implement `change_state(emotions: dict[str, float], fill: float | None = None) -> None`:
   - Update specified emotions to their values
   - If `fill` is provided, set ALL unspecified emotions to `fill`
   - If `fill` is None, leave unspecified emotions unchanged

4. [x] Implement `reset(value: float = 0.0) -> None`:
   - Set all emotions to the specified value

5. [x] Implement `to_dict() -> dict[str, float]`:
   - Return copy of current emotional state

6. [x] Implement `get_emotion(emotion: str) -> float`:
   - Return current value of emotion

7. [x] Implement `get_category_emotions(category: EmotionCategory) -> dict[str, float]`:
   - Return dict of emotions in category with their values

8. [x] Implement `get_dominant() -> tuple[str, float]`:
   - Return emotion with highest value

9. [x] Implement `get_top(n: int = 5) -> list[tuple[str, float]]`:
   - Return top N emotions by value

10. [x] Implement `any_above(threshold: float, category: EmotionCategory | None = None) -> bool`:
    - Return True if any emotion (optionally in category) exceeds threshold

11. [x] Implement `__repr__`, `__eq__`, `__len__`, `__contains__`, `__iter__` methods

12. [x] BONUS: Added `get_valence()`, `get_arousal()`, `get_category_average()`, `copy()` methods

**Tests**: `tests/personaut/emotions/test_state.py` ✅ (43 tests)
- ✅ Test default creation includes all 36 emotions
- ✅ Test creation with subset includes only those
- ✅ Test change_emotion with valid/invalid values
- ✅ Test change_state with and without fill parameter
- ✅ Test reset functionality
- ✅ Test query methods (get_dominant, get_top, any_above)
- ✅ Test boundary values (0.0, 0.5, 1.0)

---

### Task 3.4: Emotion Module Exports ✅
**Documentation**: [STYLE_GUIDE.md](STYLE_GUIDE.md) (Import Organization section)

**File**: `src/personaut/emotions/__init__.py`

**Subtasks**:
1. [x] Export `EmotionalState` class
2. [x] Export all 36 emotion constants
3. [x] Export `ALL_EMOTIONS`
4. [x] Export `EmotionCategory` enum
5. [x] Export category functions
6. [x] Define `__all__` list

**Phase 3 Totals**: 98 new tests (191 total), 23 source files, mypy clean

---


## Phase 4: Trait System ✅ COMPLETE

### Task 4.1: Trait Definitions ✅
**Documentation**: [TRAITS.md](TRAITS.md), [STYLE_GUIDE.md](STYLE_GUIDE.md)

**File**: `src/personaut/traits/trait.py`

**Subtasks**:
1. [x] Define all 17 trait constants (UPPER_SNAKE_CASE):
   - `WARMTH`, `REASONING`, `EMOTIONAL_STABILITY`, `DOMINANCE`, `HUMILITY`
   - `LIVELINESS`, `RULE_CONSCIOUSNESS`, `SOCIAL_BOLDNESS`, `SENSITIVITY`, `VIGILANCE`
   - `ABSTRACTEDNESS`, `PRIVATENESS`, `APPREHENSION`, `OPENNESS_TO_CHANGE`
   - `SELF_RELIANCE`, `PERFECTIONISM`, `TENSION`

2. [x] Create `Trait` dataclass with:
   - `name: str`
   - `description: str`
   - `low_pole: str`
   - `high_pole: str`

3. [x] Create `ALL_TRAITS: list[str]` containing all 17

4. [x] Create trait clusters: `INTERPERSONAL_TRAITS`, `EMOTIONAL_TRAITS`, `COGNITIVE_TRAITS`, `BEHAVIORAL_TRAITS`

5. [x] Create `TRAIT_METADATA` registry with pole labels

6. [x] Implement utility functions: `get_trait_metadata()`, `is_valid_trait()`, `get_trait_cluster()`

**Tests**: `tests/personaut/traits/test_trait.py` ✅ (22 tests)
- ✅ Test all 17 traits are defined
- ✅ Test trait constants and clusters
- ✅ Test Trait class and metadata

---

### Task 4.2: TraitProfile Class ✅
**Documentation**: [TRAITS.md](TRAITS.md)

**File**: `src/personaut/traits/profile.py`

**Subtasks**:
1. [x] Create `TraitProfile` class with:
   ```python
   def __init__(self, traits: list[str] | None = None, baseline: float = 0.5) -> None
   ```
   - If `traits` is None, include ALL 17 traits
   - If `traits` is provided, include only those traits
   - Initialize all included traits to `baseline` value (default 0.5 = population average)

2. [x] Implement `set_trait(trait: str, value: float) -> None`
3. [x] Implement `set_traits(traits: dict[str, float]) -> None`
4. [x] Implement `get_trait(trait: str) -> float`
5. [x] Implement `to_dict() -> dict[str, float]`
6. [x] Implement `get_high_traits(threshold: float = 0.7) -> list[tuple[str, float]]`
7. [x] Implement `get_low_traits(threshold: float = 0.3) -> list[tuple[str, float]]`
8. [x] Implement `get_extreme_traits() -> dict[str, list[tuple[str, float]]]`
9. [x] Implement `get_deviation_from_average() -> float`
10. [x] Implement `is_similar_to(other: TraitProfile, threshold: float) -> bool`
11. [x] Implement `blend_with(other: TraitProfile, weight: float) -> TraitProfile`
12. [x] Implement `copy() -> TraitProfile`
13. [x] Implement `__len__`, `__contains__`, `__iter__`, `__eq__`, `__repr__`

**Tests**: `tests/personaut/traits/test_profile.py` ✅ (48 tests)
- ✅ Test creation with all traits and subsets
- ✅ Test set_trait and set_traits
- ✅ Test high/low/extreme trait queries
- ✅ Test deviation, similarity, blending, and copy

---

### Task 4.3: Trait-Emotion Coefficients ✅
**Documentation**: [TRAITS.md](TRAITS.md) (Trait-Emotion Coefficients section)

**File**: `src/personaut/traits/coefficients.py`

**Subtasks**:
1. [x] Define coefficient mappings for all 17 traits with affected emotions

2. [x] Create `get_coefficient(trait: str, emotion: str) -> float` function

3. [x] Create `get_affected_emotions(trait: str) -> list[str]` function

4. [x] Create `get_traits_affecting_emotion(emotion: str) -> dict[str, float]` function

5. [x] Create `calculate_emotion_modifier(traits: dict[str, float], emotion: str) -> float`

**Tests**: `tests/personaut/traits/test_coefficients.py` ✅ (18 tests)
- ✅ Test coefficient retrieval for each trait
- ✅ Test affected emotions and traits
- ✅ Test modifier calculation

---

### Task 4.4: Trait Module Exports ✅
**File**: `src/personaut/traits/__init__.py`

**Subtasks**:
1. [x] Export `Trait`, `TraitProfile` classes
2. [x] Export all 17 trait constants
3. [x] Export all trait clusters
4. [x] Export coefficient functions
5. [x] Export utility functions
6. [x] Define `__all__`

**Phase 4 Totals**: 78 new tests (269 total), 26 source files, mypy clean

---


## Phase 5: State Calculation System ✅ COMPLETE

### Task 5.1: State Modes ✅
**Documentation**: [EMOTIONS.md](EMOTIONS.md) (State Calculation Modes section)

**File**: `src/personaut/states/mode.py`

**Subtasks**:
1. [x] Define `StateMode` enum:
   - `AVERAGE` - Average intensity across history
   - `MAXIMUM` - Maximum intensity from history
   - `MINIMUM` - Minimum intensity from history
   - `RECENT` - Weighted with exponential decay
   - `CUSTOM` - User-provided calculation function

2. [x] Add `description` property for each mode
3. [x] Add `requires_custom_function` property
4. [x] Implement `parse_state_mode()` helper function

**Tests**: `tests/personaut/states/test_mode.py` ✅ (18 tests)

---

### Task 5.2: StateCalculator Class ✅
**File**: `src/personaut/states/calculator.py`

**Subtasks**:
1. [x] Create `StateCalculator` class with:
   - `mode: StateMode`
   - `history_size: int` (default 10)
   - `decay_factor: float` (for RECENT mode)
   - `custom_function: Callable | None`

2. [x] Implement `add_state(state: EmotionalState) -> None`
3. [x] Implement `clear_history() -> None`
4. [x] Implement `get_history() -> list[EmotionalState]`
5. [x] Implement `calculate(history: list[EmotionalState]) -> EmotionalState`:
   - AVERAGE: average each emotion across history
   - MAXIMUM: max value for each emotion
   - MINIMUM: min value for each emotion
   - RECENT: exponentially weighted average
   - CUSTOM: call custom function

6. [x] Implement `get_calculated_state() -> EmotionalState`
7. [x] Implement `__len__` and `__repr__` methods

**Tests**: `tests/personaut/states/test_calculator.py` ✅ (25 tests)

---

### Task 5.3: Markov Chain Transitions ✅
**Documentation**: [EMOTIONS.md](EMOTIONS.md) (Markov Chain Transitions section)

**File**: `src/personaut/states/markov.py`

**Subtasks**:
1. [x] Create `MarkovTransitionMatrix` class with:
   - `transitions: dict[EmotionCategory, dict[EmotionCategory, float]]`
   - `volatility: float` (0-1, how much emotions change per transition)

2. [x] Define `DEFAULT_CATEGORY_TRANSITIONS` probabilities

3. [x] Implement `get_transition_probability(from_category, to_category) -> float`

4. [x] Implement `apply_trait_modifiers(base_probability, target_emotion, traits) -> float`

5. [x] Implement `next_state(current: EmotionalState, traits: TraitDict | None) -> EmotionalState`

6. [x] Implement `simulate_trajectory(initial, steps, traits) -> list[EmotionalState]`

**Tests**: `tests/personaut/states/test_markov.py` ✅ (18 tests)

---

### Task 5.4: State Module Exports ✅
**File**: `src/personaut/states/__init__.py`

**Subtasks**:
1. [x] Export `StateMode` enum
2. [x] Export `StateCalculator` class
3. [x] Export `MarkovTransitionMatrix` class
4. [x] Export mode constants (AVERAGE, MAXIMUM, etc.)
5. [x] Export `parse_state_mode` function
6. [x] Define `__all__`

**Phase 5 Totals**: 61 new tests (325 total), 29 source files, mypy clean

---


## Phase 5.5: Facts System ✅ COMPLETE

### Task 5.5.1: Fact and FactCategory ✅
**File**: `src/personaut/facts/fact.py`

**Subtasks**:
1. [x] Define `FactCategory` enum with 8 categories:
   - `LOCATION` - Physical location and venue details
   - `ENVIRONMENT` - Environmental conditions
   - `TEMPORAL` - Time-related facts
   - `SOCIAL` - Social dynamics
   - `PHYSICAL` - Physical conditions
   - `BEHAVIORAL` - Observable behaviors
   - `ECONOMIC` - Economic factors
   - `SENSORY` - Sensory perceptions

2. [x] Add `description` property for each category
3. [x] Add `embedding_weight` property (0.5 to 1.0)

4. [x] Create `Fact` dataclass (frozen, immutable):
   - `category: FactCategory`
   - `key: str`
   - `value: Any`
   - `unit: str | None`
   - `confidence: float` (0.0 to 1.0)
   - `source: str | None`
   - `metadata: dict[str, Any]`

5. [x] Implement `to_embedding_text() -> str`
6. [x] Implement `to_dict()` and `from_dict()` methods
7. [x] Define fact templates (LOCATION_FACTS, ENVIRONMENT_FACTS, etc.)
8. [x] Create factory functions (`create_location_fact`, etc.)

**Tests**: `tests/personaut/facts/test_fact.py` ✅ (24 tests)

---

### Task 5.5.2: SituationalContext ✅
**File**: `src/personaut/facts/context.py`

**Subtasks**:
1. [x] Create `SituationalContext` class to aggregate facts:
   - `facts: list[Fact]`
   - `timestamp: datetime`
   - `description: str | None`

2. [x] Implement `add_*` methods for each category
3. [x] Implement `get_facts_by_category(category) -> list[Fact]`
4. [x] Implement `get_fact(key) -> Fact | None`
5. [x] Implement `get_value(key, default) -> Any`
6. [x] Implement `to_embedding_text(include_categories) -> str`
7. [x] Implement `to_weighted_embedding_pairs() -> list[tuple[str, float]]`
8. [x] Implement `to_dict()`, `from_dict()`, `copy()`, `merge()`
9. [x] Implement dunder methods: `__len__`, `__iter__`, `__contains__`, `__repr__`
10. [x] Create template functions (`create_coffee_shop_context`, `create_office_context`)

**Tests**: `tests/personaut/facts/test_context.py` ✅ (29 tests)

---

### Task 5.5.3: FactExtractor ✅
**File**: `src/personaut/facts/extractor.py`

**Subtasks**:
1. [x] Create `ExtractionPattern` dataclass with:
   - `category: FactCategory`
   - `key: str`
   - `pattern: str` (regex)
   - `group: int`
   - `transform: Callable | None`

2. [x] Define `DEFAULT_PATTERNS` with 16+ extraction patterns
3. [x] Create `FactExtractor` class with:
   - `patterns: list[ExtractionPattern]`
   - `confidence_default: float`

4. [x] Implement `extract(text, existing_context) -> SituationalContext`
5. [x] Implement `add_pattern(pattern) -> None`
6. [x] Implement `extract_all_matches(text) -> list[tuple]`

**Tests**: `tests/personaut/facts/test_extractor.py` ✅ (17 tests)

---

### Task 5.5.4: LLM-Based Extraction ✅
**File**: `src/personaut/facts/llm_extractor.py`

**Subtasks**:
1. [x] Define `LLMClient` protocol for LLM integration
2. [x] Define `EXTRACTION_PROMPT` template for fact extraction
3. [x] Create `LLMFactExtractor` class (async):
   - `llm_client: LLMClient`
   - `prompt_template: str`
   - `fallback_to_regex: bool`

4. [x] Implement `extract(text, existing_context) -> SituationalContext`
5. [x] Implement `_parse_response(response) -> list[dict]` with markdown cleanup
6. [x] Implement `with_custom_prompt(template) -> LLMFactExtractor`
7. [x] Create `SyncLLMFactExtractor` for synchronous usage

**Tests**: `tests/personaut/facts/test_llm_extractor.py` ✅ (20 tests)

---

### Task 5.5.5: Facts Module Exports ✅
**File**: `src/personaut/facts/__init__.py`

**Subtasks**:
1. [x] Export all classes and enums
2. [x] Export factory functions
3. [x] Export templates and patterns
4. [x] Export LLM extractor classes
5. [x] Define `__all__`

**Phase 5.5 Totals**: 90 new tests (415 total), 34 source files, mypy clean

---


## Phase 6: Memory System ✅

> **Dependencies**: This phase integrates with the Facts System (Phase 5.5) for situational grounding.

**Phase 6 Totals**: 127 new tests (542 total), 6 source files, mypy clean

### Task 6.1: Memory Base Classes ✅
**Documentation**: [PERSONAS.md](../PERSONAS.md) (Memory Types section), [FACTS.md](FACTS.md)

**File**: `src/personaut/memory/memory.py`

**Subtasks**:
1. [x] Create `Memory` base class with:
   - `id: str`
   - `description: str`
   - `created_at: datetime`
   - `emotional_state: EmotionalState | None`
   - `context: SituationalContext | None` - Structured facts about the situation
   - `embedding: list[float] | None`


2. [x] Create `MemoryType` enum: `INDIVIDUAL`, `SHARED`, `PRIVATE`

3. [x] Implement `to_embedding_text() -> str` that combines:
   - Memory description
   - Emotional state summary
   - Situational context embedding text (weighted by category)

4. [x] Implement `get_context_value(key, default) -> Any` convenience method

**File**: `src/personaut/memory/individual.py`

**Subtasks**:
1. [x] Create `IndividualMemory(Memory)` class
2. [x] Factory function `create_individual_memory(individual, description, emotional_state, context)`

**File**: `src/personaut/memory/shared.py`

**Subtasks**:
1. [x] Create `SharedMemory(Memory)` class with:
   - `relationships: list[Relationship]`
   - `perspectives: dict[str, str]` (individual_id -> perspective)

2. [x] Factory function `create_shared_memory(description, relationships, context)`

**File**: `src/personaut/memory/private.py`

**Subtasks**:
1. [x] Create `PrivateMemory(Memory)` class with:
   - `trust_threshold: float`
   - `owner_id: str`

2. [x] Factory function `create_private_memory(individual, description, emotional_state, context, trust_threshold)`

3. [x] Implement `can_access(trust_level: float) -> bool`

**Tests**: `tests/personaut/memory/test_memory.py`, `test_individual.py`, `test_shared.py`, `test_private.py`

---


### Task 6.2: Vector Store Interface ✅
**Documentation**: [PERSONAS.md](../PERSONAS.md) (Storage section)

**File**: `src/personaut/memory/vector_store.py`

**Subtasks**:
1. [x] Create `VectorStore` Protocol/ABC with:
   - `store(memory: Memory, embedding: list[float]) -> None`
   - `search(query_embedding: list[float], limit: int) -> list[tuple[Memory, float]]`
   - `delete(memory_id: str) -> None`
   - `get(memory_id: str) -> Memory | None`

**File**: `src/personaut/memory/sqlite_store.py`

**Subtasks**:
1. [x] Create `SQLiteVectorStore(VectorStore)` using sqlite-vec
2. [x] Implement connection management
3. [x] Implement CRUD operations
4. [x] Implement vector similarity search

**Tests**: `tests/personaut/memory/test_vector_store.py`, `test_sqlite_store.py`

---

### Task 6.3: Memory Search ✅
**File**: `src/personaut/memory/__init__.py`

**Subtasks**:
1. [x] Create `search_memories(store, query, embed_func, limit) -> list[Memory]` function
2. [x] Create `get_relevant_memories(store, context: SituationalContext, embed_func, limit) -> list[Memory]`
   - Uses context embedding text for similarity search
   - Weights results by category relevance
3. [x] Create `extract_and_search(store, text, embed_func, limit) -> list[Memory]`
   - Uses `FactExtractor` to extract context from text
   - Then searches using extracted context
4. [x] Create `filter_accessible_memories(memories, trust_level) -> list[Memory]`
   - Filters private memories based on trust threshold

---


## Phase 7: Mask and Trigger System ✅

### Task 7.1: Mask Implementation ✅
**Documentation**: [SIMULATIONS.md](SIMULATIONS.md) (Masks section)

**File**: `src/personaut/masks/mask.py`

**Subtasks**:
1. [x] Create `Mask` class with:
   - `name: str`
   - `emotional_modifications: dict[str, float]`
   - `trigger_situations: list[str]`
   - `active_by_default: bool`

2. [x] Create `create_mask()` factory function

3. [x] Implement `apply(emotional_state: EmotionalState) -> EmotionalState`

**File**: `src/personaut/masks/defaults.py`

**Subtasks**:
1. [x] Create predefined masks:
   - `PROFESSIONAL_MASK`
   - `CASUAL_MASK`
   - `STOIC_MASK`
   - `ENTHUSIASTIC_MASK`
   - `NURTURING_MASK` (bonus)
   - `GUARDED_MASK` (bonus)

**Tests**: `tests/personaut/masks/test_mask.py` ✅ (36 tests)

---

### Task 7.2: Trigger Implementation ✅
**Documentation**: [SIMULATIONS.md](SIMULATIONS.md) (Triggers section)

**File**: `src/personaut/triggers/trigger.py`

**Subtasks**:
1. [x] Create `Trigger` base class with:
   - `description: str`
   - `active: bool`
   - `response: Mask | EmotionalState`

2. [x] Create abstract `check(context) -> bool` method

**File**: `src/personaut/triggers/emotional.py`

**Subtasks**:
1. [x] Create `EmotionalTrigger(Trigger)` with:
   - `rules: list[TriggerRule]` (emotional state rules)

2. [x] Implement `check(emotional_state: EmotionalState) -> bool`

3. [x] Factory `create_emotional_trigger(description, rules, response)`

**File**: `src/personaut/triggers/situational.py`

**Subtasks**:
1. [x] Create `SituationalTrigger(Trigger)` with:
   - `rules: list[TriggerRule]` (physical state rules)
   - `keyword_triggers: list[str]` (keyword matching)

2. [x] Implement `check(situation) -> bool`

3. [x] Factory `create_situational_trigger(description, rules, response)`

**Tests**: `tests/personaut/triggers/test_emotional.py`, `test_situational.py` ✅ (56 tests)

---


## Phase 8: Relationship System ✅

### Task 8.1: Relationship Implementation ✅
**Documentation**: [SIMULATIONS.md](SIMULATIONS.md) (Relationships section)

**File**: `src/personaut/relationships/relationship.py`

**Subtasks**:
1. [x] Create `Relationship` class with:
   - `id: str`
   - `individual_ids: list[str]`
   - `trust: dict[str, dict[str, float]]` (bilateral trust matrix)
   - `shared_memory_ids: list[str]`
   - `history: str`
   - `relationship_type: str`
   - `trust_history: list[TrustChange]`

2. [x] Factory `create_relationship(individual_ids, trust, history)`

3. [x] Implement `get_trust(from_individual, to_individual) -> float`

4. [x] Implement `update_trust(from_individual, to_individual, change, reason) -> float`

5. [x] Additional methods:
   - `get_mutual_trust(ind_a, ind_b) -> float`
   - `get_trust_asymmetry(ind_a, ind_b) -> float`
   - `get_trust_level(from_ind, to_ind) -> TrustLevel`
   - `add_individual(id, default_trust)`
   - `remove_individual(id)`

**File**: `src/personaut/relationships/trust.py`

**Subtasks**:
1. [x] Create trust calculation utilities:
   - `get_trust_level(value) -> TrustLevel`
   - `get_trust_info(value) -> TrustInfo`
   - `calculate_trust_change(current, change, reason)`
   - `trust_allows_disclosure(trust_value, threshold)`
2. [x] Define trust level thresholds and descriptions (6 levels: NONE, MINIMAL, LOW, MODERATE, HIGH, COMPLETE)
3. [x] Define behavioral modifiers per trust level

**File**: `src/personaut/relationships/network.py`

**Subtasks**:
1. [x] Create `RelationshipNetwork` class for graph operations
2. [x] Implement `get_relationships(individual) -> list[Relationship]`
3. [x] Additional methods:
   - `get_relationship_between(ind_a, ind_b)`
   - `get_connected_individuals(individual_id)`
   - `find_path(from_ind, to_ind, max_depth)`
   - `calculate_path_trust(path)`
   - `get_common_connections(ind_a, ind_b)`

**Tests**: `tests/personaut/relationships/` ✅ (91 tests)

---


## Phase 9: Situation System ✅

### Task 9.1: Situation Implementation ✅
**Documentation**: [SIMULATIONS.md](SIMULATIONS.md) (Creating Situations section)

**File**: `src/personaut/situations/situation.py`

**Subtasks**:
1. [x] Create `Situation` class with:
   - `id: str`
   - `modality: Modality`
   - `description: str`
   - `time: datetime | None`
   - `location: str | None`
   - `context: dict[str, Any]`
   - `participants: list[str]`
   - `tags: list[str]`

2. [x] Factory `create_situation(modality, description, time, location, context)`

3. [x] Additional methods:
   - `get_context_value(key, default)` - nested key access
   - `set_context_value(key, value)` - nested key setting
   - `is_in_person()`, `is_remote()`, `is_synchronous()`, `is_asynchronous()`
   - `get_modality_traits()` - returns communication characteristics
   - Participant and tag management

**File**: `src/personaut/situations/context.py`

**Subtasks**:
1. [x] Create `SituationContext` class for managing context data
   - `get(key)`, `set(key, value)`, `has(key)`, `remove(key)`
   - `merge(other)` - deep merge dictionaries
   - `get_category()`, `set_category()` - category-based access
   - `copy()` - deep copy
2. [x] Implement context validation
   - `CONTEXT_SCHEMA` definitions for environment, social, temporal, atmosphere
   - `validate(strict)` - returns ValidationResult with errors/warnings
   - Custom validator support via `add_validator()`
3. [x] Factory functions:
   - `create_context(**kwargs)`
   - `create_environment_context(...)`
   - `create_social_context(...)`

**Tests**: `tests/personaut/situations/` ✅ (61 tests)

---


## Phase 10: Individual System ✅

### Task 10.1: Individual Implementation ✅
**Documentation**: [PERSONAS.md](../PERSONAS.md)

**File**: `src/personaut/individuals/individual.py`

**Subtasks**:
1. [x] Create `Individual` class with:
   - `id: str`
   - `name: str`
   - `emotional_state: EmotionalState`
   - `traits: TraitProfile`
   - `memories: list[Memory]`
   - `masks: list[Mask]`
   - `triggers: list[Trigger]`
   - `active_mask: Mask | None`
   - `metadata: dict[str, Any]`
   - `created_at: datetime`
   - `updated_at: datetime`

2. [x] Implement trait methods (`get_trait`, `set_trait`, `get_high_traits`, `get_low_traits`)

3. [x] Implement `add_memory(memory: Memory) -> None`

4. [x] Implement `add_mask(mask: Mask) -> None`

5. [x] Implement `add_trigger(trigger: Trigger) -> None`

6. [x] Implement `check_triggers() -> list[Trigger]` (with situational support)

7. [x] Factory `create_individual(name, traits, emotional_state)`

8. [x] Factory `create_human(name, context)`

9. [x] Factory `create_nontracked_individual(role)`

**Tests**: `tests/personaut/individuals/test_individual.py` ✅ (54 tests)

---

## Phase 11: Model Providers ✅

> **Design Philosophy**: The PDK uses a **local-first embedding strategy** to ensure consistency across all providers and eliminate API costs for embeddings. The default embedding model is **sentence-transformers/all-MiniLM-L6-v2**, a lightweight model suitable for most use cases.

### Task 11.1: Model Interface ✅
**Documentation**: [PERSONAS.md](../PERSONAS.md) (Model Providers section)

**File**: `src/personaut/models/model.py` ✅

**Subtasks**:
1. [x] Create `Model` Protocol/ABC with:
   - `generate(prompt: str) -> GenerationResult`
   - `generate_structured(prompt: str, schema: type[T]) -> T`
   - `generate_stream(prompt: str) -> Iterator[str]`
2. [x] Create `ModelConfig` dataclass for model parameters
3. [x] Create `GenerationResult` dataclass for standardized output
4. [x] Define `ModelError` exception hierarchy (RateLimitError, AuthenticationError, InvalidRequestError)

**File**: `src/personaut/models/embeddings.py` ✅

**Subtasks**:
1. [x] Create `EmbeddingModel` Protocol/ABC with:
   - `embed(text: str) -> list[float]`
   - `embed_batch(texts: list[str]) -> list[list[float]]`
   - `dimension: int` (property)
   - `model_name: str` (property)

2. [x] Create `EmbeddingConfig` dataclass with:
   - `model_name: str`
   - `dimension: int`
   - `device: str = "auto"` (cpu, cuda, mps, auto)
   - `batch_size: int = 32`
   - `normalize: bool = True`

3. [x] Create `EMBEDDING_MODELS` registry for known model dimensions

---

### Task 11.2: Local Embedding Provider (Default) ✅
**File**: `src/personaut/models/local_embedding.py` ✅

> **Default Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
> - Open-source, lightweight (~80MB)
> - 384-dimensional embeddings
> - Runs locally via `sentence-transformers`
> - No API costs, consistent across all LLM providers

**Subtasks**:
1. [x] Create `LocalEmbedding(EmbeddingModel)` implementation
   - Default model: `sentence-transformers/all-MiniLM-L6-v2`
   - Alternative: `BAAI/bge-large-en-v1.5` (1024d, higher quality)
2. [x] Implement lazy model loading (only load when first used)
3. [x] Support device selection (CPU, CUDA, MPS for Apple Silicon)
4. [x] Implement caching for repeated embeddings
5. [x] Factory function `create_local_embedding()`

**Supported Local Embedding Models**:
| Model | Dimensions | Size | Notes |
|-------|------------|------|-------|
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | ~80MB | **Default** - Fast, lightweight |
| `BAAI/bge-large-en-v1.5` | 1024 | ~1.3GB | Higher quality |
| `nomic-ai/nomic-embed-text-v1.5` | 768 | ~550MB | Good for long contexts |

**Tests**: `tests/personaut/models/test_embeddings.py` ✅

---

### Task 11.3: Gemini Provider (LLM Only) ✅
**File**: `src/personaut/models/gemini.py` ✅

> **Note**: Gemini is used for LLM generation only. Embeddings use the local model for consistency.

**Subtasks**:
1. [x] Create `GeminiModel(Model)` implementation
2. [x] Handle API authentication via `GOOGLE_API_KEY`
3. [x] Implement error handling with ModelError hierarchy
4. [x] Support streaming responses
5. [x] Support structured output generation
6. [x] Factory function `create_gemini_model()`

**Tests**: `tests_integ/models/test_model_gemini.py` (integration)

---

### Task 11.4: Bedrock Provider (LLM Only) ✅
**File**: `src/personaut/models/bedrock.py` ✅

> **Note**: Bedrock is used for LLM generation only. Embeddings use the local model for consistency.

**Subtasks**:
1. [x] Create `BedrockModel(Model)` implementation
2. [x] Support Claude, Llama, Mistral models
3. [x] Handle AWS authentication via boto3
4. [x] Implement error handling with ModelError hierarchy
5. [x] Support streaming responses
6. [x] Factory function `create_bedrock_model()`

**Tests**: `tests_integ/models/test_model_bedrock.py` (integration)

---

### Task 11.5: OpenAI Provider (LLM Only) ✅
**File**: `src/personaut/models/openai.py` ✅

> **Note**: OpenAI is used for LLM generation only. Embeddings use the local model for consistency.

**Subtasks**:
1. [x] Create `OpenAIModel(Model)` implementation
2. [x] Handle API authentication via `OPENAI_API_KEY`
3. [x] Implement error handling with ModelError hierarchy
4. [x] Support GPT-4, GPT-4o, o1 models
5. [x] Support streaming responses
6. [x] Support native structured output for Pydantic models
7. [x] Factory function `create_openai_model()`

**Tests**: `tests_integ/models/test_model_openai.py` (integration)

---

### Task 11.6: Ollama Provider (Local LLM) ✅
**File**: `src/personaut/models/ollama.py` ✅

> **Note**: Ollama provides local LLM inference. Embeddings still use the dedicated local embedding model.

**Subtasks**:
1. [x] Create `OllamaModel(Model)` implementation
2. [x] Auto-detect Ollama server at `http://localhost:11434`
3. [x] Support streaming responses
4. [x] List available models via `list_models()`
5. [x] Check server availability via `is_available()`
6. [x] Factory function `create_ollama_model()`

**Tests**: `tests_integ/models/test_model_ollama.py` (integration)

---

### Task 11.7: Provider Registry ✅
**File**: `src/personaut/models/registry.py` ✅

**Subtasks**:
1. [x] Create `ModelRegistry` class for managing providers
2. [x] Implement `get_llm(provider: str) -> Model`
3. [x] Implement `get_embedding() -> EmbeddingModel` (always returns local)
4. [x] Support provider configuration via environment variables
5. [x] Implement automatic provider detection based on available credentials

**Default Configuration**:
```python
# Embeddings always use local model (no API costs, consistent vectors)
embedding = get_embedding()  # Returns LocalEmbedding

# LLM can be configured per-use-case
llm = get_llm()           # Auto-detect from environment
llm = get_llm("gemini")   # Google Gemini
llm = get_llm("bedrock")  # AWS Bedrock (Claude, Llama, etc.)
llm = get_llm("openai")   # OpenAI (GPT-4, o1)
llm = get_llm("ollama")   # Local Ollama
```

**Environment Variables**:
- `PERSONAUT_LLM_PROVIDER`: Default LLM provider
- `PERSONAUT_LLM_MODEL`: Default model name
- `PERSONAUT_EMBEDDING_MODEL`: Embedding model path
- `GOOGLE_API_KEY`: For Gemini provider
- `OPENAI_API_KEY`: For OpenAI provider
- AWS credentials for Bedrock (via boto3)

**Tests**: `tests/personaut/models/test_registry.py` ✅ (27 tests)

---


## Phase 12: Prompt System

> **Dependencies**: This phase integrates with the Facts System (Phase 5.5) for situational context in prompts.

### Task 12.1: Prompt Components
**Documentation**: [PROMPTS.md](PROMPTS.md), [STYLE_GUIDE.md](STYLE_GUIDE.md), [FACTS.md](FACTS.md)

**File**: `src/personaut/prompts/components/emotional_state.py`

**Subtasks**:
1. [ ] Create `EmotionalStateComponent` class
2. [ ] Implement intensity mapping (value -> "minimal", "mild", "moderate", etc.)
3. [ ] Implement category-aware descriptions
4. [ ] Implement `format(emotional_state, highlight_dominant) -> str`

**File**: `src/personaut/prompts/components/personality.py`

**Subtasks**:
1. [ ] Create `PersonalityComponent` class
2. [ ] Implement trait value interpretation (high/low descriptions)
3. [ ] Implement `format(traits) -> str`

**File**: `src/personaut/prompts/components/memory.py`

**Subtasks**:
1. [ ] Create `MemoryComponent` class
2. [ ] Filter private memories by trust level
3. [ ] Implement `format(memories, trust_level) -> str`

**File**: `src/personaut/prompts/components/relationship.py`

**Subtasks**:
1. [ ] Create `RelationshipComponent` class
2. [ ] Map trust levels to descriptions
3. [ ] Implement `format(individual, others, relationships) -> str`

**File**: `src/personaut/prompts/components/situation.py`

**Subtasks**:
1. [ ] Create `SituationComponent` class
2. [ ] Implement modality-specific formatting
3. [ ] Implement `format(situation) -> str`
4. [ ] Implement `format_context(context: SituationalContext) -> str`
   - Uses category weights for emphasis
   - Formats facts as natural language descriptions

**Tests**: `tests/personaut/prompts/components/`

---

### Task 12.2: Prompt Templates
**Documentation**: [PROMPTS.md](PROMPTS.md) (Templates section)

**File**: `src/personaut/prompts/templates/base.py`

**Subtasks**:
1. [ ] Create `BaseTemplate` abstract class with:
   - `_render_identity(individual) -> str`
   - `_render_personality(traits) -> str`
   - `_render_emotional_state(state) -> str`
   - `_render_guidelines() -> str`
   - Abstract `render(**kwargs) -> str`

**File**: `src/personaut/prompts/templates/conversation.py`

**Subtasks**:
1. [ ] Create `ConversationTemplate(BaseTemplate)`
2. [ ] Implement `render(individual, others, situation, style) -> str`

**File**: `src/personaut/prompts/templates/survey.py`

**Subtasks**:
1. [ ] Create `SurveyTemplate(BaseTemplate)`
2. [ ] Implement `render(individual, questions, response_format) -> str`

**File**: `src/personaut/prompts/templates/outcome.py`

**Subtasks**:
1. [ ] Create `OutcomeTemplate(BaseTemplate)`
2. [ ] Implement `render(individual, situation, target_outcome) -> str`

**Tests**: `tests/personaut/prompts/templates/`

---

### Task 12.3: PromptBuilder and PromptManager
**Documentation**: [PROMPTS.md](PROMPTS.md)

**File**: `src/personaut/prompts/builder.py`

**Subtasks**:
1. [ ] Create `PromptBuilder` class with fluent interface:
   - `with_individual(individual)`
   - `with_emotional_state(state)`
   - `with_traits(traits)`
   - `with_situation(situation)`
   - `with_memories(memories)`
   - `with_relationships(relationships)`
   - `using_template(template_name)`
   - `section_order(order: list[str])`
   - `build() -> str`

**File**: `src/personaut/prompts/manager.py`

**Subtasks**:
1. [ ] Create `PromptManager` class with:
   - Configuration options (intensity_threshold, max_memories, etc.)
   - `generate(individual, situation, **overrides) -> str`
   - `validate(prompt) -> ValidationResult`

**Tests**: `tests/personaut/prompts/test_builder.py`, `test_manager.py`

---

## Phase 13: Simulation System ✅ COMPLETE

> **Dependencies**: This phase integrates with the Facts System (Phase 5.5) for rich situational context.

**Phase 13 Totals**: 86 new tests (1077 total), 8 source files, mypy clean

### Task 13.1: Simulation Types and Styles ✅
**Documentation**: [SIMULATIONS.md](SIMULATIONS.md), [FACTS.md](FACTS.md)

**File**: `src/personaut/simulations/types.py`

**Subtasks**:
1. [x] Create `SimulationType` enum:
   - `CONVERSATION`
   - `SURVEY`
   - `OUTCOME_SUMMARY`
   - `LIVE_CONVERSATION`
2. [x] Add `description`, `is_interactive`, `supports_multi_turn`, `default_style` properties
3. [x] Add `parse_simulation_type()` helper function
4. [x] Export string constants (CONVERSATION, SURVEY, etc.)

**File**: `src/personaut/simulations/styles.py`

**Subtasks**:
1. [x] Create `SimulationStyle` enum:
   - `SCRIPT`
   - `QUESTIONNAIRE`
   - `NARRATIVE`
   - `JSON`
   - `TXT`
2. [x] Add `description`, `extension`, `is_structured`, `supports_metadata` properties
3. [x] Add `parse_simulation_style()` helper function
4. [x] Export string constants

**Tests**: `tests/personaut/simulations/test_types.py` ✅ (10 tests)
**Tests**: `tests/personaut/simulations/test_styles.py` ✅ (11 tests)

---

### Task 13.2: Base Simulation Class ✅
**File**: `src/personaut/simulations/simulation.py`

**Subtasks**:
1. [x] Create `Simulation` base class with:
   - `situation: Situation`
   - `individuals: list[Individual]`
   - `simulation_type: SimulationType`
   - `style: SimulationStyle | None`
   - `output_format: str`
   - `context: dict[str, Any] | None` - Rich situational facts

2. [x] Create `SimulationResult` dataclass with:
   - `simulation_id: str`
   - `simulation_type: SimulationType`
   - `content: str`
   - `output_path: Path | None`
   - `metadata: dict[str, Any]`
   - `created_at: datetime`
   - `to_dict()` and `to_json()` methods

3. [x] Implement abstract `_generate(run_index, **options) -> str`

4. [x] Implement `run(num, dir, **options) -> list[SimulationResult]`

5. [x] Factory `create_simulation(situation, individuals, type, style, output, context, **kwargs)`

**Tests**: `tests/personaut/simulations/test_simulation.py` ✅ (10 tests)

---

### Task 13.3: Conversation Simulation ✅
**File**: `src/personaut/simulations/conversation.py`

**Subtasks**:
1. [x] Create `ConversationSimulation(Simulation)`
2. [x] Implement multi-turn conversation logic with `max_turns` option
3. [x] Implement SCRIPT output formatter (`_format_script`)
4. [x] Implement JSON output formatter (`_format_json`)
5. [x] Handle emotional state updates per turn
6. [x] Track conversation history
7. [x] Support `include_actions` and `update_emotions` options

**Tests**: `tests/personaut/simulations/test_conversation.py` ✅ (13 tests)

---

### Task 13.4: Survey Simulation ✅
**File**: `src/personaut/simulations/survey.py`

**Subtasks**:
1. [x] Create `SurveySimulation(Simulation)`
2. [x] Implement question processing
3. [x] Implement QUESTIONNAIRE output formatter
4. [x] Handle different question types:
   - `likert_5`, `likert_7`, `likert_10`
   - `yes_no`
   - `multiple_choice`
   - `open_ended`
5. [x] Add `QUESTION_TYPES` configuration dictionary
6. [x] Implement emotional positivity influence on responses
7. [x] Support `include_reasoning` option

**Tests**: `tests/personaut/simulations/test_survey.py` ✅ (14 tests)

---

### Task 13.5: Outcome Simulation ✅
**File**: `src/personaut/simulations/outcome.py`

**Subtasks**:
1. [x] Create `OutcomeSimulation(Simulation)`
2. [x] Implement `target_outcome` tracking
3. [x] Implement factor analysis:
   - `_calculate_emotional_factor()`
   - `_calculate_trait_factor()`
   - `_calculate_situation_factor()`
4. [x] Implement randomization options (`randomize_emotions`, `randomize_range`)
5. [x] Generate outcome summary statistics
6. [x] Generate insights and recommendations
7. [x] Create aggregate summary file for multiple runs

**Tests**: `tests/personaut/simulations/test_outcome.py` ✅ (10 tests)

---

### Task 13.6: Live Simulation ✅
**Documentation**: [SIMULATIONS.md](SIMULATIONS.md) (Live Conversation section), [LIVE_INTERACTIONS.md](LIVE_INTERACTIONS.md)

**File**: `src/personaut/simulations/live.py`

**Subtasks**:
1. [x] Create `LiveSimulation(Simulation)`
2. [x] Create `ChatMessage` dataclass with:
   - `sender: str`
   - `content: str`
   - `action: str | None`
   - `timestamp: datetime`
   - `to_dict()` method
3. [x] Create `ChatSession` class with:
   - `session_id: str`
   - `messages: list[ChatMessage]`
   - `send(content)` and `send_action(action)` methods
   - `get_state()` and `get_history()` methods
   - `end()` method
4. [x] Implement `create_chat_session() -> ChatSession`
5. [x] Implement `get_session(session_id) -> ChatSession | None`
6. [x] Implement `load_session(path)` and `save_session(session, path)`
7. [x] Implement placeholder `start_simulator()` and `stop_simulator()`

**Tests**: `tests/personaut/simulations/test_live.py` ✅ (18 tests)

---

### Task 13.7: Module Exports ✅
**File**: `src/personaut/simulations/__init__.py`

**Subtasks**:
1. [x] Export `SimulationType`, `SimulationStyle` enums
2. [x] Export type/style constants
3. [x] Export parse functions
4. [x] Export `Simulation`, `SimulationResult`, `create_simulation`
5. [x] Export all simulation classes
6. [x] Export `ChatMessage`, `ChatSession`
7. [x] Define `__all__`

---


## Phase 14: Server System (FastAPI + Flask)

### Task 14.1: FastAPI Application ✅
**Documentation**: [LIVE_INTERACTIONS.md](LIVE_INTERACTIONS.md), [STYLE_GUIDE.md](STYLE_GUIDE.md)

**File**: `src/personaut/server/api/app.py`

**Subtasks**:
1. [x] Create FastAPI application
2. [x] Configure CORS
3. [x] Add exception handlers
4. [x] Configure OpenAPI documentation

**File**: `src/personaut/server/api/schemas.py`

**Subtasks**:
1. [x] Create Pydantic schemas for all request/response types
2. [x] Individual schemas (create, update, response)
3. [x] Emotion schemas
4. [x] Trait schemas
5. [x] Situation schemas
6. [x] Relationship schemas
7. [x] Session schemas
8. [x] Message schemas

**Tests**: `tests/personaut/server/api/test_app.py`, `tests/personaut/server/api/test_schemas.py` ✅ (30 tests)

---

### Task 14.2: API Routes ✅
**Documentation**: [LIVE_INTERACTIONS.md](LIVE_INTERACTIONS.md) (FastAPI Backend section)

**File**: `src/personaut/server/api/routes/individuals.py`

**Subtasks**:
1. [x] `GET /api/individuals` - List all
2. [x] `POST /api/individuals` - Create
3. [x] `GET /api/individuals/{id}` - Get details
4. [x] `PATCH /api/individuals/{id}` - Update
5. [x] `DELETE /api/individuals/{id}` - Delete

**File**: `src/personaut/server/api/routes/emotions.py`

**Subtasks**:
1. [x] `GET /api/individuals/{id}/emotions` - Get state
2. [x] `PATCH /api/individuals/{id}/emotions` - Update
3. [x] `POST /api/individuals/{id}/emotions/reset` - Reset
4. [x] `GET /api/individuals/{id}/emotions/history` - History

**File**: `src/personaut/server/api/routes/situations.py`

**Subtasks**:
1. [x] CRUD endpoints for situations
2. [x] Modality configuration endpoints

**File**: `src/personaut/server/api/routes/relationships.py`

**Subtasks**:
1. [x] CRUD endpoints for relationships
2. [x] Trust update endpoint
3. [x] Shared memory endpoints

**File**: `src/personaut/server/api/routes/sessions.py`

**Subtasks**:
1. [x] `POST /api/sessions` - Create session
2. [x] `GET /api/sessions/{id}` - Get session
3. [x] `POST /api/sessions/{id}/messages` - Send message
4. [x] `GET /api/sessions/{id}/messages` - Get history
5. [x] `DELETE /api/sessions/{id}` - End session

**File**: `src/personaut/server/api/routes/websocket.py`

**Subtasks**:
1. [x] WebSocket connection handler
2. [x] Real-time message broadcasting
3. [x] Emotional state change notifications
4. [x] Trigger activation notifications

**Tests**: `tests/personaut/server/api/` for all routes

---

### Task 14.3: Flask Web UI ✅
**Documentation**: [LIVE_INTERACTIONS.md](LIVE_INTERACTIONS.md) (Flask Web UI section)

**File**: `src/personaut/server/ui/app.py`

**Subtasks**:
1. [x] Create Flask application
2. [x] Configure template directory
3. [x] Configure static files

**File**: `src/personaut/server/ui/views/dashboard.py`

**Subtasks**:
1. [x] Main dashboard view
2. [x] Individual listing
3. [x] Situation listing
4. [x] Session management

**File**: `src/personaut/server/ui/views/individuals.py`

**Subtasks**:
1. [x] Individual editor view
2. [x] Emotional state controls
3. [x] Trait management
4. [x] Trigger/mask configuration

**File**: `src/personaut/server/ui/views/situations.py`

**Subtasks**:
1. [x] Situation configuration view
2. [x] Modality selection
3. [x] Context editor

**File**: `src/personaut/server/ui/views/relationships.py`

**Subtasks**:
1. [x] Relationship editor view
2. [x] Trust level controls
3. [x] Shared memory management

**File**: `src/personaut/server/ui/views/chat.py`

**Subtasks**:
1. [x] Modality-specific chat interfaces
2. [x] Text message UI (bubble style)
3. [x] Email UI (thread style)
4. [x] In-person UI (narrative style)
5. [x] Phone call UI
6. [x] Video call UI

**Templates**: `src/personaut/server/ui/templates/`

**Subtasks**:
1. [x] `base.html` - Base layout
2. [x] `dashboard.html`
3. [x] `individual_editor.html`
4. [x] `situation_config.html`
5. [x] `relationship_editor.html`
6. [x] `chat/text_message.html`
7. [x] `chat/email.html`
8. [x] `chat/in_person.html`

**Static**: `src/personaut/server/ui/static/`

**Subtasks**:
1. [x] CSS styles (dark theme)
2. [x] JavaScript for WebSocket
3. [x] Emotion visualization

---

### Task 14.4: LiveInteractionServer ✅
**File**: `src/personaut/server/server.py`

**Subtasks**:
1. [x] Create `LiveInteractionServer` class
2. [x] Implement `add_individual(individual)`
3. [x] Implement `start(api_port, ui_port, **config)`
4. [x] Coordinate FastAPI and Flask startup
5. [x] Handle graceful shutdown

**File**: `src/personaut/server/server.py` (includes `LiveInteractionClient`)

**Subtasks**:
1. [x] Create `LiveInteractionClient` class
2. [x] Implement individual operations
3. [x] Implement situation operations
4. [x] Implement relationship operations
5. [x] Implement session operations

**Tests**: `tests/personaut/server/test_server.py` ✅ (17 tests)

---

## Phase 15: Storage Interface ✅

### Task 15.1: Storage Abstraction ✅
**File**: `src/personaut/interfaces/storage.py`

**Subtasks**:
1. [x] Create `Storage` Protocol/ABC
2. [x] Define CRUD operations for all entity types

**File**: `src/personaut/interfaces/sqlite.py`

**Subtasks**:
1. [x] Implement SQLite storage
2. [x] Create database schema
3. [x] Implement migrations (schema versioning)

**File**: `src/personaut/interfaces/file.py`

**Subtasks**:
1. [x] Implement file-based JSON storage

**Tests**: `tests/personaut/interfaces/` ✅ (75 tests)

---

## Phase 16: Public API ✅

### Task 16.1: Package Exports ✅
**File**: `src/personaut/__init__.py`

**Subtasks**:
1. [x] Export all public classes and functions
2. [x] Create convenience imports:
   ```python
   from personaut import create_individual, create_human
   from personaut import EmotionalState, ANXIOUS, HOPEFUL
   from personaut import TraitProfile, WARMTH
   from personaut import create_simulation
   from personaut import create_situation, create_relationship
   from personaut import SQLiteStorage, FileStorage
   ```
3. [x] Define `__version__` (exports from `_version.py`)
4. [x] Define `__all__` (47 public exports)

---

## Phase 17: Integration Tests ✅

### Task 17.1: Model Provider Tests ✅
**File**: `tests_integ/models/test_model_gemini.py`

**Subtasks**:
1. [x] Test Gemini text generation
2. [x] Test Gemini embeddings
3. [x] Test error handling

**File**: `tests_integ/models/test_model_bedrock.py`

**Subtasks**:
1. [x] Test Bedrock text generation
2. [x] Test Bedrock embeddings

---

### Task 17.2: Simulation Tests ✅
**File**: `tests_integ/simulations/test_conversation.py`

**Subtasks**:
1. [x] End-to-end conversation simulation
2. [x] Verify emotional state changes
3. [x] Verify prompt generation

**File**: `tests_integ/simulations/test_survey.py`

**Subtasks**:
1. [x] End-to-end survey simulation
2. [x] Verify response generation

---

### Task 17.3: Memory Tests ✅
**File**: `tests_integ/memory/test_sqlite_store.py`

**Subtasks**:
1. [x] Test vector storage
2. [x] Test similarity search

---

## Phase 18: Documentation and PyPI Prep

### Task 18.1: README.md
**File**: `README.md`

**Subtasks**:
1. [ ] Write package overview
2. [ ] Add installation instructions
3. [ ] Add quick start examples
4. [ ] Add feature list
5. [ ] Add links to documentation

---

### Task 18.2: API Documentation
**Subtasks**:
1. [ ] Add docstrings to all public APIs
2. [ ] Generate API reference (optional: mkdocs/sphinx)

---

### Task 18.3: PyPI Preparation
**Subtasks**:
1. [ ] Finalize `pyproject.toml` metadata
2. [ ] Create `LICENSE` file (choose license)
3. [ ] Create `CHANGELOG.md`
4. [ ] Run `hatch build`
5. [ ] Test installation from built package
6. [ ] Create PyPI account (if needed)
7. [ ] Upload to TestPyPI first
8. [ ] Verify installation from TestPyPI
9. [ ] Upload to PyPI

---

## Task Summary

| Phase | Tasks | Est. Complexity |
|-------|-------|-----------------|
| 1. Foundation | 1 | Low |
| 2. Type System | 3 | Low |
| 3. Emotions | 4 | Medium |
| 4. Traits | 4 | Medium |
| 5. States | 2 | Medium |
| 6. Memory | 3 | High |
| 7. Masks/Triggers | 2 | Medium |
| 8. Relationships | 1 | Medium |
| 9. Situations | 1 | Low |
| 10. Individuals | 1 | Medium |
| 11. Models | 3 | High |
| 12. Prompts | 3 | High |
| 13. Simulations | 6 | High |
| 14. Server | 4 | Very High |
| 15. Storage | 1 | Medium |
| 16. Public API | 1 | Low |
| 17. Integration Tests | 3 | Medium |
| 18. PyPI Prep | 3 | Low |

**Total Tasks**: ~46 major tasks

---

## Recommended Build Order

1. **Foundation** (Phase 1)
2. **Type System** (Phase 2)
3. **Emotions** (Phase 3) - Core functionality
4. **Traits** (Phase 4) - Core functionality
5. **States** (Phase 5) - Depends on Emotions
6. **Individuals** (Phase 10) - Depends on Emotions, Traits
7. **Memory** (Phase 6) - Depends on Individuals
8. **Masks/Triggers** (Phase 7) - Depends on Emotions
9. **Relationships** (Phase 8) - Depends on Individuals, Memory
10. **Situations** (Phase 9)
11. **Models** (Phase 11) - Required for simulations
12. **Prompts** (Phase 12) - Depends on all core components
13. **Simulations** (Phase 13) - Integration layer
14. **Storage** (Phase 15)
15. **Server** (Phase 14) - Complex, build last
16. **Public API** (Phase 16)
17. **Integration Tests** (Phase 17)
18. **PyPI Prep** (Phase 18)

---

## Notes

- All code must follow [STYLE_GUIDE.md](STYLE_GUIDE.md)
- All tests must follow patterns in [STYLE_GUIDE.md](STYLE_GUIDE.md) (Testing section)
- Run `hatch fmt` before each commit
- Run `hatch test` to verify no regressions
- Use conventional commits for version tracking
