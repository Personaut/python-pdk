# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-02-21

### Fixed
- **Serialization round-trip drops memories, masks, and traits** — `Individual.from_dict()` now fully restores memories, masks, triggers, and active mask state. Previously these were silently dropped. `SQLiteStorage` fixed a key mismatch where `to_dict()` outputs `"traits"` but the DB column expected `"trait_profile"`, causing trait data loss on save. Normalization added in both directions. (Issue #7)
- **`from_dict()` crashes on SQLite-sourced data** — `data.get("memories", [])` returns `None` (not `[]`) when the key exists with a `NULL` value from SQLite, crashing with `TypeError: 'NoneType' object is not iterable`. Changed to `data.get("memories") or []` for memories, masks, and triggers. (Issue #7)
- **Survey template crashes with zero-emotion individual** — `_render_emotional_influence()` in `prompts/templates/survey.py` called `get_dominant()` and immediately unpacked the result as a tuple. When all emotions are at 0, `get_dominant()` returns `None`, causing `TypeError`. Added a `None` guard with early return.
- **Simulation engine now uses LLM when provided** — `create_simulation()` accepts an optional `llm` parameter (or `provider`/`model` shorthand) that wires through to `ConversationSimulation._generate_turn()` for real LLM-powered dialogue generation. Falls back to placeholder responses when no LLM is set. (Issue #5)
- **Invalid emotion names in source code** — Replaced 6+ non-existent emotion names (`confident`, `friendly`, `curious`, `relaxed`, `impatient`, `frustrated`, `suspicious`) with valid 36-emotion equivalents (`proud`, `cheerful`, `creative`, `content`, `angry`, `hostile`) across `coefficients.py`, `conversation.py`, `live.py`, `survey.py`, `outcome.py`, `masks/`, and prompt templates. Additional sweep fixed ~15 remaining instances in docstring examples (`happy`→`cheerful`, `nervous`→`anxious`, `sad`→`depressed`), UI fallback code (`worried`, `melancholy`), and docs (`FACTS.md`, `SIMULATIONS.md`, `LIVE_INTERACTIONS.md`). (Issue #2)
- **Trait coefficient bugs** — Fixed TENSION coefficients referencing `relaxed` and `impatient`, PERFECTIONISM referencing `frustrated`, and VIGILANCE referencing `suspicious` — all non-existent emotions. (Issue #6)
- **Documentation import paths** — Fixed `personaut.emotion.*` → `personaut.emotions.*`, `personaut.situation.*` → `personaut.create_situation`, `personaut.simulation.*` → `personaut.create_simulation` across EMOTIONS.md, SIMULATIONS.md, PROMPTS.md, and LIVE_INTERACTIONS.md. (Issue #4)
- **Documentation non-existent APIs** — Removed references to `personaut.states.mode` (AVERAGE, MAXIMUM, MODE, CustomMode), `get_transition_probabilities()`, `transition()`, `create_trait()`, `add_trait()`, `increase_emotion()`, `decrease_emotion()` — none of which exist. Replaced with correct APIs (`apply_delta()`, `set_trait()`, `EmotionCategory` enums). (Issue #3)
- **Documentation invalid emotion names** — Replaced `confident`, `friendly`, `curious`, `impatient` in all code examples across docs with valid 36-emotion names. (Issue #2)
- **Input validation missing across multiple APIs** — `Individual` now rejects empty or >255-char names; `create_relationship()` rejects self-relationships (fewer than 2 unique IDs) and clamps trust values to [0.0, 1.0]; `add_memory()` deduplicates by ID; `save_individual()` accepts both Individual objects and dicts. (Issue #8)
- **Silent exception swallowing in `from_dict()`** — All `except: pass` blocks in `Individual.from_dict()` now log warnings with `logger.warning()` for skipped traits, memories, masks, and triggers. `ConversationSimulation._generate_llm_turn()` also logs LLM failures before falling back.
- **`MAX_NAME_LENGTH` was a dataclass field** — Changed to `ClassVar[int]` so it doesn't appear in `__init__`, `repr`, or per-instance storage.
- **Test expectations** — Updated `test_registry_list_providers` to expect 5 providers (including Anthropic).

### Added
- `AnthropicModel` lazy-loading in `personaut.models.__init__` — `from personaut.models import AnthropicModel` now works like the other providers.
- `llm` field on `Simulation` base class for optional LLM injection.
- `provider` and `model` shorthand parameters on `create_simulation()` factory.
- `_generate_llm_turn()` method on `ConversationSimulation` for persona-aware LLM dialogue generation.
- Complete API reference table in EMOTIONS.md with all actual `EmotionalState` methods.

### Changed
- `apply_trait_modulated_change()` docstring expanded to document all 17 traits' involvement (not just the 4 previously mentioned).
- EMOTIONS.md: Replaced State Calculation Modes and Markov Chain sections with a note marking them as planned features.

## [0.2.0] - 2026-02-20

### Added
- Anthropic (Claude) model provider with full generate/streaming support
- `AnthropicModel` class with `create_anthropic_model()` factory
- `Provider.ANTHROPIC` enum value in model registry
- Secure API key input using `getpass.getpass()` in CLI setup
- Anthropic provider auto-detection via `ANTHROPIC_API_KEY` environment variable

## [0.1.0] - 2026-02-14

### Added
- Initial release
- EmotionalState class with 36 emotions
- Trait system with 17 personality traits
- Memory system with vector storage
- Mask and trigger system
- Relationship management
- Situation modeling with modalities
- Simulation types (conversation, survey, outcome, live)
- Prompt generation system
- LiveInteractionServer (FastAPI + Flask)

[Unreleased]: https://github.com/personaut/python-pdk/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/personaut/python-pdk/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/personaut/python-pdk/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/personaut/python-pdk/releases/tag/v0.1.0
