"""Situation context management for Personaut PDK.

This module provides the SituationContext class for structured context
data management with validation and type safety.

Example:
    >>> from personaut.situations import SituationContext
    >>>
    >>> ctx = SituationContext()
    >>> ctx.set("environment.lighting", "dim")
    >>> ctx.set("atmosphere", "tense")
    >>> ctx.validate()  # Raises if invalid
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContextCategory(Enum):
    """Categories for situational context."""

    ENVIRONMENT = "environment"
    SOCIAL = "social"
    TEMPORAL = "temporal"
    EMOTIONAL = "emotional"
    PHYSICAL = "physical"
    ACTIVITY = "activity"
    RELATIONSHIP = "relationship"
    METADATA = "metadata"


# Schema definitions for context validation
CONTEXT_SCHEMA: dict[str, dict[str, Any]] = {
    "environment": {
        "type": "object",
        "properties": {
            "lighting": {"type": "string", "enum": ["bright", "dim", "dark", "natural", "artificial"]},
            "noise_level": {"type": "string", "enum": ["quiet", "moderate", "loud", "very_loud"]},
            "temperature": {"type": "string", "enum": ["cold", "cool", "comfortable", "warm", "hot"]},
            "space": {"type": "string", "enum": ["cramped", "cozy", "open", "spacious"]},
            "indoor": {"type": "boolean"},
            "private": {"type": "boolean"},
        },
    },
    "social": {
        "type": "object",
        "properties": {
            "crowd_level": {"type": "string", "enum": ["empty", "sparse", "moderate", "crowded", "packed"]},
            "formality": {"type": "string", "enum": ["casual", "informal", "neutral", "formal", "very_formal"]},
            "audience": {"type": "boolean"},
            "observers": {"type": "integer", "minimum": 0},
        },
    },
    "temporal": {
        "type": "object",
        "properties": {
            "time_of_day": {"type": "string", "enum": ["morning", "afternoon", "evening", "night", "late_night"]},
            "day_of_week": {"type": "string"},
            "urgency": {"type": "string", "enum": ["none", "low", "moderate", "high", "critical"]},
            "duration_expected": {"type": "string", "enum": ["brief", "short", "moderate", "long", "extended"]},
        },
    },
    "atmosphere": {
        "type": "string",
        "enum": ["relaxed", "tense", "professional", "casual", "intimate", "hostile", "neutral"],
    },
}


@dataclass
class ValidationError:
    """A validation error for context data.

    Attributes:
        path: The path to the invalid value (e.g., "environment.lighting").
        message: Description of the error.
        value: The invalid value.
    """

    path: str
    message: str
    value: Any = None

    def __str__(self) -> str:
        return f"{self.path}: {self.message} (got {self.value!r})"


@dataclass
class ValidationResult:
    """Result of context validation.

    Attributes:
        valid: Whether the context is valid.
        errors: List of validation errors.
        warnings: List of validation warnings.
    """

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class SituationContext:
    """Structured context data for a situation.

    Provides a type-safe way to manage contextual information about
    a situation, with support for nested values and validation.

    Attributes:
        data: The raw context data dictionary.
        validators: Custom validation functions.

    Example:
        >>> ctx = SituationContext()
        >>> ctx.set("environment.lighting", "dim")
        >>> ctx.set("atmosphere", "tense")
        >>> ctx.get("environment.lighting")
        "dim"
    """

    data: dict[str, Any] = field(default_factory=dict)
    validators: list[Callable[[dict[str, Any]], list[ValidationError]]] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from context.

        Args:
            key: The key to look up. Supports dot notation.
            default: Value to return if not found.

        Returns:
            The value at the key, or default.

        Example:
            >>> ctx.get("environment.lighting")
            "dim"
        """
        if "." not in key:
            return self.data.get(key, default)

        parts = key.split(".")
        current: Any = self.data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a value in context.

        Args:
            key: The key to set. Supports dot notation.
            value: The value to set.

        Example:
            >>> ctx.set("environment.lighting", "bright")
        """
        if "." not in key:
            self.data[key] = value
            return

        parts = key.split(".")
        current = self.data
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def has(self, key: str) -> bool:
        """Check if a key exists.

        Args:
            key: The key to check.

        Returns:
            True if the key exists.
        """
        return self.get(key) is not None

    def remove(self, key: str) -> bool:
        """Remove a key from context.

        Args:
            key: The key to remove.

        Returns:
            True if the key was removed, False if not found.
        """
        if "." not in key:
            if key in self.data:
                del self.data[key]
                return True
            return False

        parts = key.split(".")
        current = self.data
        for part in parts[:-1]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False

        if isinstance(current, dict) and parts[-1] in current:
            del current[parts[-1]]
            return True
        return False

    def merge(self, other: dict[str, Any]) -> None:
        """Merge another dictionary into this context.

        Args:
            other: Dictionary to merge in.
        """
        self._deep_merge(self.data, other)

    def _deep_merge(self, base: dict[str, Any], update: dict[str, Any]) -> None:
        """Recursively merge dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get_category(self, category: ContextCategory | str) -> dict[str, Any]:
        """Get all values for a category.

        Args:
            category: The category to get.

        Returns:
            Dict of values in that category.
        """
        if isinstance(category, ContextCategory):
            category = category.value
        result: Any = self.data.get(category, {})
        if isinstance(result, dict):
            return result
        return {}

    def set_category(self, category: ContextCategory | str, values: dict[str, Any]) -> None:
        """Set all values for a category.

        Args:
            category: The category to set.
            values: The values to set.
        """
        if isinstance(category, ContextCategory):
            category = category.value
        self.data[category] = values

    def validate(self, strict: bool = False) -> ValidationResult:
        """Validate the context data.

        Args:
            strict: If True, unknown keys are treated as errors.

        Returns:
            ValidationResult with any errors or warnings.
        """
        errors: list[ValidationError] = []
        warnings: list[str] = []

        # Run schema validation
        for key, value in self.data.items():
            if key in CONTEXT_SCHEMA:
                schema = CONTEXT_SCHEMA[key]
                self._validate_against_schema(key, value, schema, errors)
            elif strict:
                errors.append(ValidationError(key, "Unknown context key"))
            else:
                warnings.append(f"Unknown context key: {key}")

        # Run custom validators
        for validator in self.validators:
            errors.extend(validator(self.data))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_against_schema(
        self,
        path: str,
        value: Any,
        schema: dict[str, Any],
        errors: list[ValidationError],
    ) -> None:
        """Validate a value against a schema."""
        schema_type = schema.get("type", "any")

        if schema_type == "string":
            if not isinstance(value, str):
                errors.append(ValidationError(path, f"Expected string, got {type(value).__name__}", value))
            elif "enum" in schema and value not in schema["enum"]:
                errors.append(ValidationError(path, f"Value must be one of {schema['enum']}", value))

        elif schema_type == "boolean":
            if not isinstance(value, bool):
                errors.append(ValidationError(path, f"Expected boolean, got {type(value).__name__}", value))

        elif schema_type == "integer":
            if not isinstance(value, int):
                errors.append(ValidationError(path, f"Expected integer, got {type(value).__name__}", value))
            else:
                if "minimum" in schema and value < schema["minimum"]:
                    errors.append(ValidationError(path, f"Value must be >= {schema['minimum']}", value))
                if "maximum" in schema and value > schema["maximum"]:
                    errors.append(ValidationError(path, f"Value must be <= {schema['maximum']}", value))

        elif schema_type == "object":
            if not isinstance(value, dict):
                errors.append(ValidationError(path, f"Expected object, got {type(value).__name__}", value))
            elif "properties" in schema:
                for prop_key, prop_value in value.items():
                    if prop_key in schema["properties"]:
                        self._validate_against_schema(
                            f"{path}.{prop_key}",
                            prop_value,
                            schema["properties"][prop_key],
                            errors,
                        )

    def add_validator(self, validator: Callable[[dict[str, Any]], list[ValidationError]]) -> None:
        """Add a custom validator.

        Args:
            validator: Function that takes context data and returns errors.
        """
        self.validators.append(validator)

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dictionary."""
        return dict(self.data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SituationContext:
        """Create from dictionary."""
        return cls(data=dict(data))

    def copy(self) -> SituationContext:
        """Create a deep copy."""
        import copy

        return SituationContext(data=copy.deepcopy(self.data))

    def __len__(self) -> int:
        """Get number of top-level keys."""
        return len(self.data)

    def __bool__(self) -> bool:
        """Check if context has any data."""
        return len(self.data) > 0


def create_context(**kwargs: Any) -> SituationContext:
    """Create a situation context from keyword arguments.

    Args:
        **kwargs: Key-value pairs for the context.

    Returns:
        A new SituationContext instance.

    Example:
        >>> ctx = create_context(
        ...     atmosphere="relaxed",
        ...     environment={"lighting": "dim", "noise_level": "quiet"},
        ... )
    """
    return SituationContext(data=dict(kwargs))


def create_environment_context(
    lighting: str = "natural",
    noise_level: str = "moderate",
    temperature: str = "comfortable",
    space: str = "comfortable",
    indoor: bool = True,
    private: bool = False,
) -> SituationContext:
    """Create a context focused on physical environment.

    Args:
        lighting: Lighting conditions.
        noise_level: Ambient noise level.
        temperature: Temperature conditions.
        space: Space feeling.
        indoor: Whether indoors.
        private: Whether private.

    Returns:
        A new SituationContext with environment data.
    """
    return SituationContext(
        data={
            "environment": {
                "lighting": lighting,
                "noise_level": noise_level,
                "temperature": temperature,
                "space": space,
                "indoor": indoor,
                "private": private,
            }
        }
    )


def create_social_context(
    crowd_level: str = "moderate",
    formality: str = "neutral",
    audience: bool = False,
    observers: int = 0,
) -> SituationContext:
    """Create a context focused on social environment.

    Args:
        crowd_level: How crowded the space is.
        formality: Formality level of the situation.
        audience: Whether there's an audience.
        observers: Number of observers.

    Returns:
        A new SituationContext with social data.
    """
    return SituationContext(
        data={
            "social": {
                "crowd_level": crowd_level,
                "formality": formality,
                "audience": audience,
                "observers": observers,
            }
        }
    )


__all__ = [
    "CONTEXT_SCHEMA",
    "ContextCategory",
    "SituationContext",
    "ValidationError",
    "ValidationResult",
    "create_context",
    "create_environment_context",
    "create_social_context",
]
