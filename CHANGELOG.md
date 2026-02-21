# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.2] - 2026-02-21

### Fixed
- **34 wrong module paths in TRAITS.md** — `personaut.trait.WARMTH` (singular) corrected to `personaut.traits.WARMTH` (plural) across all 17 trait definitions and the constants reference section.
- **17 wrong parameter names in SIMULATIONS.md** — `create_situation(type=...)` corrected to `create_situation(modality=...)` to match the actual function signature.
- **13 trait coefficient tables out of sync with code** — Updated all coefficient example dicts in TRAITS.md to match the actual values in `coefficients.py`. WARMTH was missing `intimate` and `hateful`; DOMINANCE, HUMILITY, LIVELINESS, SOCIAL_BOLDNESS, SENSITIVITY, VIGILANCE, PRIVATENESS, and APPREHENSION all had incorrect values.
- **Non-existent `personaut.memory.*` dot-access in docs** — Replaced `personaut.memory.search()`, `personaut.memory.create_individual_memory()`, etc. with proper `from personaut.memory import ...` style imports in SIMULATIONS.md and PROMPTS.md. `personaut.memory.search()` → `search_memories()`.
- **Non-existent `personaut.actions` module in docs** — Replaced `personaut.actions.ESCALATE_TO_SUPERVISOR` with `personaut.masks.STOIC_MASK` in SIMULATIONS.md.
- **Non-existent `personaut.situation.*` path in FACTS.md** — `personaut.situation.create_situation()` → `personaut.create_situation()`.
- **Wrong `create_relationship()` params in docs** — `individuals=[user_a, user_b]` corrected to `individual_ids=[user_a.id, user_b.id]`; trust dict keys corrected from objects to string IDs.
- **Wrong trigger factory params in docs** — `emotional_state_rules=[...]` and `physical_state_rules=[...]` corrected to `rules=[TriggerRule(...)]` with proper `keywords` param for situational triggers.
- **Invalid `EmotionalState` constructor in docs** — `EmotionalState(increase=[...], decrease=[...])` doesn't exist; replaced with correct `masks.GUARDED_MASK` response pattern.
- **3 non-existent emotion names in SIMULATIONS.md code examples** — `stress` → `angry`, `fear` → `anxious`, `formal` → `hostile`.
- **`type=` → `modality=` in PROMPTS.md and FACTS.md** — 4 additional `create_situation()` calls corrected.
- **`from_dict()` metadata None bug** — `data.get("metadata", {})` suffers the same None-vs-absent-key issue as the memories/masks fix in v0.3.0. Changed to `data.get("metadata") or {}`.
- **`create_individual()` silently drops invalid traits** — Bare `except: pass` replaced with `logger.warning()` for consistency with the `from_dict()` logging fix.
- **`_version.py` was stuck at 0.1.0** — Synced to match the actual release version.

## [0.3.1] - 2026-02-21

### Fixed
- **`apply_trait_modulated_change()` ignores `TraitProfile` objects** — Method signature only accepted `dict[str, float]` but callers naturally pass `TraitProfile` objects, which lack `.items()` and `.get()`. Now auto-converts via `to_dict()` at method entry. (Issue #6)
- **Documentation references 26 non-existent API calls** — Replaced all `add_trait(create_trait(...))` patterns with the actual `set_trait(name, value)` API across SIMULATIONS.md (8 instances), PROMPTS.md (5 instances), and TRAITS.md (13 instances). (Issue #3)
- **Documentation shows 9 non-existent `run()` parameters** — Replaced `parallel`, `track_emotions`, `track_memories`, `save_prompts`, `max_workers`, `filename_prefix`, `include_metadata`, `on_turn`, `on_complete` with the actual run() signature and marked them as planned features. (Issue #4)
- **Documentation shows `simulation_type` param** — Corrected to `template` (the actual parameter name) in PROMPTS.md. (Issue #4)
- **TRAITS.md API reference table listed non-existent methods** — Replaced `create_trait()`, `create_custom_trait()`, `add_trait()`, `trait.get_coefficient()` with actual methods: `set_trait()`, `get_trait()`, `traits.to_dict()`, `get_high_traits()`, `get_low_traits()`, `get_coefficient()`, `get_traits_affecting_emotion()`, `is_valid_trait()`. (Issue #3)
- **3 invalid emotion names in SIMULATIONS.md** — Replaced `helpful`, `patient`, `professional` (not valid emotions) with `cheerful`, `content`, `satisfied` in support agent examples. (Issue #2)
- **`create_custom_trait()` documented as code** — Moved to Planned Feature note since it doesn't exist yet. (Issue #3)

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

[Unreleased]: https://github.com/personaut/python-pdk/compare/v0.3.2...HEAD
[0.3.2]: https://github.com/personaut/python-pdk/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/personaut/python-pdk/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/personaut/python-pdk/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/personaut/python-pdk/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/personaut/python-pdk/releases/tag/v0.1.0
