"""Tests for SituationContext class."""

from __future__ import annotations

from personaut.situations import (
    ContextCategory,
    SituationContext,
    ValidationError,
    create_context,
    create_environment_context,
    create_social_context,
)


class TestSituationContext:
    """Tests for SituationContext class."""

    def test_create_empty_context(self) -> None:
        """Should create empty context."""
        ctx = SituationContext()

        assert len(ctx) == 0

    def test_create_with_data(self) -> None:
        """Should create with initial data."""
        ctx = SituationContext(data={"atmosphere": "relaxed"})

        assert ctx.get("atmosphere") == "relaxed"


class TestContextGetSet:
    """Tests for get/set operations."""

    def test_get_simple(self) -> None:
        """Should get simple value."""
        ctx = SituationContext(data={"mood": "happy"})

        assert ctx.get("mood") == "happy"

    def test_get_nested(self) -> None:
        """Should get nested value."""
        ctx = SituationContext(data={"environment": {"lighting": "dim", "noise": "quiet"}})

        assert ctx.get("environment.lighting") == "dim"
        assert ctx.get("environment.noise") == "quiet"

    def test_get_default(self) -> None:
        """Should return default for missing key."""
        ctx = SituationContext()

        assert ctx.get("missing") is None
        assert ctx.get("missing", "default") == "default"

    def test_get_nested_missing(self) -> None:
        """Should return default for missing nested key."""
        ctx = SituationContext(data={"environment": {}})

        assert ctx.get("environment.missing", "default") == "default"

    def test_set_simple(self) -> None:
        """Should set simple value."""
        ctx = SituationContext()

        ctx.set("atmosphere", "tense")

        assert ctx.data["atmosphere"] == "tense"

    def test_set_nested(self) -> None:
        """Should set nested value creating intermediate dicts."""
        ctx = SituationContext()

        ctx.set("environment.lighting", "bright")

        assert ctx.data["environment"]["lighting"] == "bright"

    def test_set_deeply_nested(self) -> None:
        """Should set deeply nested value."""
        ctx = SituationContext()

        ctx.set("a.b.c.d", "deep")

        assert ctx.data["a"]["b"]["c"]["d"] == "deep"

    def test_has(self) -> None:
        """Should check if key exists."""
        ctx = SituationContext(data={"key": "value"})

        assert ctx.has("key") is True
        assert ctx.has("missing") is False


class TestContextRemove:
    """Tests for remove operations."""

    def test_remove_simple(self) -> None:
        """Should remove simple key."""
        ctx = SituationContext(data={"a": 1, "b": 2})

        result = ctx.remove("a")

        assert result is True
        assert "a" not in ctx.data
        assert "b" in ctx.data

    def test_remove_missing(self) -> None:
        """Should return False for missing key."""
        ctx = SituationContext()

        result = ctx.remove("missing")

        assert result is False

    def test_remove_nested(self) -> None:
        """Should remove nested key."""
        ctx = SituationContext(data={"env": {"light": "dim", "noise": "quiet"}})

        result = ctx.remove("env.light")

        assert result is True
        assert "light" not in ctx.data["env"]
        assert "noise" in ctx.data["env"]


class TestContextMerge:
    """Tests for merge operations."""

    def test_merge_simple(self) -> None:
        """Should merge simple dictionaries."""
        ctx = SituationContext(data={"a": 1})

        ctx.merge({"b": 2})

        assert ctx.data["a"] == 1
        assert ctx.data["b"] == 2

    def test_merge_nested(self) -> None:
        """Should deep merge nested dictionaries."""
        ctx = SituationContext(data={"env": {"light": "dim"}})

        ctx.merge({"env": {"noise": "quiet"}})

        assert ctx.data["env"]["light"] == "dim"
        assert ctx.data["env"]["noise"] == "quiet"

    def test_merge_overwrites(self) -> None:
        """Should overwrite on conflict."""
        ctx = SituationContext(data={"a": 1})

        ctx.merge({"a": 2})

        assert ctx.data["a"] == 2


class TestContextCategories:
    """Tests for category operations."""

    def test_get_category(self) -> None:
        """Should get category data."""
        ctx = SituationContext(data={"environment": {"lighting": "dim"}})

        env = ctx.get_category(ContextCategory.ENVIRONMENT)

        assert env["lighting"] == "dim"

    def test_get_category_string(self) -> None:
        """Should get category by string."""
        ctx = SituationContext(data={"social": {"formality": "casual"}})

        social = ctx.get_category("social")

        assert social["formality"] == "casual"

    def test_set_category(self) -> None:
        """Should set category data."""
        ctx = SituationContext()

        ctx.set_category(ContextCategory.ENVIRONMENT, {"lighting": "bright"})

        assert ctx.data["environment"]["lighting"] == "bright"


class TestContextValidation:
    """Tests for context validation."""

    def test_validate_valid_context(self) -> None:
        """Should validate valid context."""
        ctx = SituationContext(
            data={
                "atmosphere": "relaxed",
                "environment": {"lighting": "dim"},
            }
        )

        result = ctx.validate()

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_invalid_enum(self) -> None:
        """Should catch invalid enum value."""
        ctx = SituationContext(data={"atmosphere": "invalid_value"})

        result = ctx.validate()

        assert result.valid is False
        assert len(result.errors) == 1
        assert "atmosphere" in result.errors[0].path

    def test_validate_invalid_type(self) -> None:
        """Should catch invalid type."""
        ctx = SituationContext(
            data={"environment": {"indoor": "yes"}}  # Should be boolean
        )

        result = ctx.validate()

        assert result.valid is False
        assert any("indoor" in e.path for e in result.errors)

    def test_validate_unknown_key_warning(self) -> None:
        """Should warn about unknown keys."""
        ctx = SituationContext(data={"unknown_key": "value"})

        result = ctx.validate(strict=False)

        assert result.valid is True
        assert len(result.warnings) > 0

    def test_validate_unknown_key_strict(self) -> None:
        """Should error on unknown keys in strict mode."""
        ctx = SituationContext(data={"unknown_key": "value"})

        result = ctx.validate(strict=True)

        assert result.valid is False

    def test_custom_validator(self) -> None:
        """Should run custom validators."""

        def require_atmosphere(data: dict) -> list[ValidationError]:
            if "atmosphere" not in data:
                return [ValidationError("atmosphere", "Atmosphere is required")]
            return []

        ctx = SituationContext()
        ctx.add_validator(require_atmosphere)

        result = ctx.validate()

        assert result.valid is False
        assert any("Atmosphere is required" in e.message for e in result.errors)


class TestContextSerialization:
    """Tests for context serialization."""

    def test_to_dict(self) -> None:
        """Should convert to plain dict."""
        ctx = SituationContext(data={"a": 1, "b": {"c": 2}})

        data = ctx.to_dict()

        assert data == {"a": 1, "b": {"c": 2}}

    def test_from_dict(self) -> None:
        """Should create from dict."""
        data = {"mood": "happy", "env": {"temp": "warm"}}

        ctx = SituationContext.from_dict(data)

        assert ctx.get("mood") == "happy"
        assert ctx.get("env.temp") == "warm"

    def test_copy(self) -> None:
        """Should create deep copy."""
        ctx = SituationContext(data={"a": {"b": 1}})

        copied = ctx.copy()
        copied.set("a.b", 2)

        assert ctx.get("a.b") == 1  # Original unchanged
        assert copied.get("a.b") == 2


class TestContextDunderMethods:
    """Tests for dunder methods."""

    def test_len(self) -> None:
        """Should return number of top-level keys."""
        ctx = SituationContext(data={"a": 1, "b": 2})

        assert len(ctx) == 2

    def test_bool_empty(self) -> None:
        """Should be falsy when empty."""
        ctx = SituationContext()

        assert bool(ctx) is False

    def test_bool_not_empty(self) -> None:
        """Should be truthy when has data."""
        ctx = SituationContext(data={"a": 1})

        assert bool(ctx) is True


class TestContextFactories:
    """Tests for context factory functions."""

    def test_create_context(self) -> None:
        """Should create context from kwargs."""
        ctx = create_context(
            atmosphere="relaxed",
            mood="happy",
        )

        assert ctx.get("atmosphere") == "relaxed"
        assert ctx.get("mood") == "happy"

    def test_create_environment_context(self) -> None:
        """Should create environment-focused context."""
        ctx = create_environment_context(
            lighting="dim",
            noise_level="quiet",
            indoor=True,
        )

        assert ctx.get("environment.lighting") == "dim"
        assert ctx.get("environment.noise_level") == "quiet"
        assert ctx.get("environment.indoor") is True

    def test_create_social_context(self) -> None:
        """Should create social-focused context."""
        ctx = create_social_context(
            crowd_level="sparse",
            formality="casual",
            audience=False,
        )

        assert ctx.get("social.crowd_level") == "sparse"
        assert ctx.get("social.formality") == "casual"
        assert ctx.get("social.audience") is False
