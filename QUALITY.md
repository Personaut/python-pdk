# Personaut PDK — Code Quality Score

> **Last updated:** 2026-02-14 · **Overall Grade: A (96%)**

---

## Summary Dashboard

| Dimension           | Grade  | Score  | Details                                         |
|---------------------|--------|--------|-------------------------------------------------|
| **Test Suite**      | A+     | 100%   | 1,924 tests, 0 failures, 0 errors               |
| **Test Coverage**   | B+     | 80.5%  | 80.52% line coverage (threshold: 80%)            |
| **Type Safety**     | A+     | 100%   | 0 mypy errors across 114 source files (strict)   |
| **Linting**         | A+     | 100%   | 0 ruff errors (13 rule categories enabled)        |
| **Formatting**      | A+     | 100%   | 226/226 files formatted (ruff format)             |
| **Documentation**   | A+     | 98%    | 1,109/1,130 functions & classes documented        |
| **Complexity**      | B      | 78%    | 73 functions > 50 lines (largest: 221 lines)      |
| **Tech Debt**       | A+     | 99%    | 1 TODO in codebase                                |
| **Safety**          | A+     | 100%   | Age restriction enforced at all layers             |

---

## Detailed Breakdown

### Test Suite — A+ (100%)

```
1,924 tests passed · 0 failed · 0 errors · 3 deprecation warnings
Execution time: ~9 seconds
```

- **Unit tests:** Core domain logic (emotions, traits, triggers, masks, memory, individuals, simulations)
- **Integration tests:** Server API routes, UI views, session management
- **Age restriction tests:** 13 dedicated tests across individual + simulation layers

### Test Coverage — B+ (80.5%)

```
TOTAL: 9,716 statements · 1,544 missed · 80.52% covered
Required threshold: 80.0% ✅
```

| Module                     | Coverage |
|----------------------------|----------|
| `emotions/`                | 95–100%  |
| `traits/`                  | 91–100%  |
| `individuals/`             | 85–100%  |
| `masks/`                   | 86–100%  |
| `memory/`                  | 85–100%  |
| `triggers/`                | 88–90%   |
| `simulations/`             | 76–100%  |
| `server/api/`              | 44–100%  |
| `server/ui/`               | 55–90%   |
| `types/`                   | 83–100%  |
| `prompts/`                 | 75–95%   |

### Type Safety — A+ (100%)

```
mypy --strict: Success — no issues found in 114 source files
```

- **Mode:** `strict = true` with `warn_return_any = true`
- **Configuration:** `pyproject.toml [tool.mypy]`
- **Third-party overrides:** 10 external packages with `ignore_missing_imports`

### Linting — A+ (100%)

```
ruff check: All checks passed (0 errors)
```

**Enabled rule categories (13):**
`E` (pycodestyle errors), `W` (pycodestyle warnings), `F` (pyflakes),
`I` (isort), `B` (flake8-bugbear), `C4` (flake8-comprehensions),
`UP` (pyupgrade), `ARG` (unused-arguments), `SIM` (flake8-simplify),
`TCH` (flake8-type-checking), `PTH` (flake8-use-pathlib),
`RUF` (Ruff-specific), `TC` (type-checking imports)

**Suppressed by design:** `E501`, `B008`, `B905`, `ARG001`, `PTH123`,
`RUF012`, `RUF022`, `SIM105`, `SIM108`, `RUF001–003`, `TC001–003`

**Test-specific ignores:** `ARG001–002`, `B018`, `E741`, `RUF015`,
`SIM117`, `SIM118`

### Formatting — A+ (100%)

```
ruff format --check: 226/226 files already formatted
```

### Documentation — A+ (98%)

```
Functions: 946/967 documented (97%)
Classes:   163/163 documented (100%)
Overall:   1,109/1,130 (98%)
```

### Complexity — B (78%)

```
73 functions exceed 50 lines
Top 5 longest functions:
  221 lines  _get_emotion_guidelines  (prompts/templates/conversation.py)
  196 lines  create_view              (server/ui/views/individuals.py)
  182 lines  _run_outcome_tracking    (server/ui/views/simulations.py)
  147 lines  analyze_emotions         (server/ui/views/chat_engine.py)
  146 lines  generate_conversation_video (images/video.py)
```

### Tech Debt — A+ (99%)

```
TODOs/FIXMEs: 1
  → simulations/live.py:188 — "TODO: Implement mask tracking"
```

### Safety — A+ (100%)

**Age restriction (18+)** enforced at **5 layers:**

1. `Individual.__post_init__` — validates on construction
2. `create_individual()` factory — passes through to constructor
3. `Simulation.run()` — validates all participants before execution
4. `IndividualCreate` API schema — Pydantic `ge=18` validation (422 response)
5. Session creation API route — validates before starting a session

`"child"` and `"teen"` removed from `AGE_GROUPS` physical descriptors.

---

## Codebase Metrics

| Metric                 | Value      |
|------------------------|------------|
| Source files            | 114        |
| Test files              | 112        |
| Source lines            | 32,801     |
| Test lines              | 22,090     |
| Test-to-source ratio    | 0.67:1     |
| Total tests             | 1,924      |
| Test density            | 16.9 tests/source file |
| Python version target   | 3.10+      |

---

## How to Run

```bash
# All checks
pytest                                    # Test suite
pytest --cov=personaut --cov-report=term  # Coverage
mypy src/personaut                        # Type checking
ruff check src/ tests/                    # Linting
ruff format --check src/ tests/           # Format check

# Quick quality gate
pytest -q && mypy src/personaut && ruff check src/ tests/ && ruff format --check src/ tests/
```

---

## Improvement Opportunities

| Area            | Current | Target | Action                                         |
|-----------------|---------|--------|-------------------------------------------------|
| Test Coverage   | 80.5%   | 85%    | Add server/UI view tests (currently 44–55%)      |
| Complexity      | 73 long | < 40   | Refactor top 5 longest functions                 |
| Tech Debt       | 1 TODO  | 0      | Implement mask tracking in `live.py`             |
