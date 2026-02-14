# Contributing to Personaut PDK

Thank you for your interest in contributing to the Personaut PDK! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Making Changes](#making-changes)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Documentation](#documentation)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [Hatch](https://hatch.pypa.io/) for project management

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/personaut/python-pdk.git
   cd python-pdk
   ```

2. Install development dependencies:
   ```bash
   pip install hatch
   hatch shell
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install -t pre-commit -t commit-msg
   ```

4. Verify the setup:
   ```bash
   hatch test
   hatch fmt
   ```

## Code Style

We follow strict code style guidelines to maintain consistency. See [docs/STYLE_GUIDE.md](docs/STYLE_GUIDE.md) for complete details.

### Key Points

- **Formatter**: ruff (line-length: 120)
- **Type Checking**: mypy in strict mode
- **Docstrings**: Google-style
- **Python Version**: 3.10+ features (union types with `|`, built-in generics)

### Running Formatters

```bash
# Format and lint
hatch fmt

# Type check
hatch run type
```

### Logging Format

Use structured logging with field-value pairs:

```python
logger.debug("individual_id=<%s>, emotion=<%s> | updating emotional state", id, emotion)
```

## Testing

### Running Tests

```bash
# Run all unit tests
hatch test

# Run with coverage
hatch test-cov

# Run specific test file
hatch test tests/personaut/emotions/test_state.py

# Run integration tests
hatch run test-integ
```

### Test Structure

Tests mirror the source structure:

```
tests/
├── personaut/
│   ├── emotions/
│   │   └── test_state.py
│   ├── traits/
│   │   └── test_trait.py
│   └── ...
└── conftest.py
```

### Writing Tests

Follow the testing patterns in [docs/STYLE_GUIDE.md](docs/STYLE_GUIDE.md):

```python
class TestEmotionalStateCreation:
    """Tests for EmotionalState initialization."""

    def test_create_default_state(self) -> None:
        """Creating state without arguments includes all emotions."""
        state = EmotionalState()
        assert len(state.emotions) == 36
```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feat/add-emotion-categories` - New features
- `fix/emotion-value-validation` - Bug fixes
- `docs/update-style-guide` - Documentation
- `refactor/simplify-state-calculator` - Refactoring

### Workflow

1. Create a branch from `main`
2. Make your changes
3. Ensure tests pass: `hatch test`
4. Ensure linting passes: `hatch fmt`
5. Ensure types check: `hatch run type`
6. Commit using conventional commits
7. Push and create a pull request

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/). Commitizen enforces this via pre-commit hook.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting (no code change) |
| `refactor` | Code restructuring |
| `test` | Adding tests |
| `chore` | Maintenance tasks |

### Examples

```
feat(emotions): add EmotionalState class with 36 emotions

fix(traits): correct coefficient calculation for warmth trait

docs(readme): add installation instructions

test(emotions): add boundary value tests for change_emotion
```

## Pull Requests

### Before Submitting

1. ✅ Tests pass locally
2. ✅ Linting passes
3. ✅ Type checking passes
4. ✅ Documentation updated (if applicable)
5. ✅ Commit messages follow conventional commits

### PR Template

When creating a PR, include:

- **Summary**: What does this PR do?
- **Related Issues**: Link any related issues
- **Testing**: How was this tested?
- **Breaking Changes**: Any breaking changes?

### Review Process

1. Automated checks must pass
2. At least one approval required
3. Address all feedback
4. Squash merge to main

## Documentation

### Code Documentation

All public APIs must have Google-style docstrings:

```python
def create_trait(trait: str, value: float, response: str | None = None) -> Trait:
    """Create a trait instance for an individual.

    Args:
        trait: The trait type constant (e.g., WARMTH, DOMINANCE).
        value: Trait value between 0.0 and 1.0.
        response: Optional custom behavioral response description.

    Returns:
        A configured Trait instance.

    Raises:
        ValidationError: When value is outside valid range.

    Example:
        >>> trait = create_trait(trait=WARMTH, value=0.8)
    """
```

### Documentation Files

| File | Purpose |
|------|---------|
| `PERSONAS.md` | Main agent guidelines |
| `docs/EMOTIONS.md` | Emotion system |
| `docs/TRAITS.md` | Trait system |
| `docs/PROMPTS.md` | Prompt generation |
| `docs/SIMULATIONS.md` | Simulations |
| `docs/LIVE_INTERACTIONS.md` | Live server |
| `docs/STYLE_GUIDE.md` | Code style |
| `docs/TASKS.md` | Implementation tasks |

## Questions?

If you have questions, feel free to:

- Open an issue with the `question` label
- Check existing documentation
- Review closed issues for similar questions

Thank you for contributing! 🎉
