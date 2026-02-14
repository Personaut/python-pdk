"""Custom exception classes for Personaut PDK.

This module defines the exception hierarchy used throughout the Personaut PDK.
All custom exceptions inherit from PersonautError, allowing for broad exception
handling while still enabling specific exception catching when needed.

Example:
    >>> from personaut.types.exceptions import EmotionValueError
    >>> raise EmotionValueError("anxious", 1.5)
    EmotionValueError: Emotion 'anxious' value 1.5 is outside valid range [0.0, 1.0]
"""

from __future__ import annotations


class PersonautError(Exception):
    """Base exception for all Personaut PDK errors.

    All custom exceptions in the Personaut PDK inherit from this class,
    allowing users to catch all Personaut-specific errors with a single
    except clause while still enabling more specific exception handling.

    Example:
        >>> try:
        ...     # Personaut operations
        ... except PersonautError as e:
        ...     print(f"Personaut error: {e}")
    """


class ValidationError(PersonautError):
    """Raised when input validation fails.

    This is the base class for all validation-related errors, including
    invalid emotion values, trait values, and other input constraints.

    Args:
        message: Description of the validation failure.
        field: Optional name of the field that failed validation.
        value: Optional value that caused the validation failure.

    Example:
        >>> raise ValidationError("Invalid input", field="name", value="")
    """

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        value: object = None,
    ) -> None:
        """Initialize ValidationError with context.

        Args:
            message: Description of the validation failure.
            field: Optional name of the field that failed validation.
            value: Optional value that caused the validation failure.
        """
        self.field = field
        self.value = value
        if field is not None:
            message = f"{field}: {message}"
        super().__init__(message)


class EmotionValueError(ValidationError):
    """Raised when an emotion value is outside the valid range [0.0, 1.0].

    Emotion values must be between 0.0 and 1.0, inclusive. This exception
    is raised when attempting to set an emotion to a value outside this range.

    Args:
        emotion: Name of the emotion.
        value: Invalid value that was provided.

    Example:
        >>> raise EmotionValueError("anxious", 1.5)
        EmotionValueError: Emotion 'anxious' value 1.5 is outside valid range [0.0, 1.0]
    """

    def __init__(self, emotion: str, value: float) -> None:
        """Initialize EmotionValueError with emotion name and invalid value.

        Args:
            emotion: Name of the emotion.
            value: Invalid value that was provided.
        """
        self.emotion = emotion
        message = f"Emotion '{emotion}' value {value} is outside valid range [0.0, 1.0]"
        super().__init__(message, field="emotion", value=value)


class EmotionNotFoundError(PersonautError):
    """Raised when referencing an unknown emotion.

    This exception is raised when attempting to access or modify an emotion
    that does not exist in the emotional state.

    Args:
        emotion: Name of the unknown emotion.
        available: Optional list of valid emotion names.

    Example:
        >>> raise EmotionNotFoundError("happiness")
        EmotionNotFoundError: Unknown emotion 'happiness'
    """

    def __init__(self, emotion: str, available: list[str] | None = None) -> None:
        """Initialize EmotionNotFoundError with emotion name.

        Args:
            emotion: Name of the unknown emotion.
            available: Optional list of valid emotion names.
        """
        self.emotion = emotion
        self.available = available
        message = f"Unknown emotion '{emotion}'"
        if available:
            message += f". Available emotions: {', '.join(sorted(available)[:5])}..."
        super().__init__(message)


class TraitNotFoundError(PersonautError):
    """Raised when referencing an unknown personality trait.

    This exception is raised when attempting to access or modify a trait
    that is not defined in the trait system.

    Args:
        trait: Name of the unknown trait.
        available: Optional list of valid trait names.

    Example:
        >>> raise TraitNotFoundError("bravery")
        TraitNotFoundError: Unknown trait 'bravery'
    """

    def __init__(self, trait: str, available: list[str] | None = None) -> None:
        """Initialize TraitNotFoundError with trait name.

        Args:
            trait: Name of the unknown trait.
            available: Optional list of valid trait names.
        """
        self.trait = trait
        self.available = available
        message = f"Unknown trait '{trait}'"
        if available:
            message += f". Available traits: {', '.join(sorted(available)[:5])}..."
        super().__init__(message)


class TraitValueError(ValidationError):
    """Raised when a trait value is outside the valid range [0.0, 1.0].

    Trait values must be between 0.0 and 1.0, inclusive. This exception
    is raised when attempting to set a trait to a value outside this range.

    Args:
        trait: Name of the trait.
        value: Invalid value that was provided.

    Example:
        >>> raise TraitValueError("warmth", -0.5)
        TraitValueError: Trait 'warmth' value -0.5 is outside valid range [0.0, 1.0]
    """

    def __init__(self, trait: str, value: float) -> None:
        """Initialize TraitValueError with trait name and invalid value.

        Args:
            trait: Name of the trait.
            value: Invalid value that was provided.
        """
        self.trait = trait
        message = f"Trait '{trait}' value {value} is outside valid range [0.0, 1.0]"
        super().__init__(message, field="trait", value=value)


class TrustThresholdError(PersonautError):
    """Raised when access is denied due to insufficient trust level.

    This exception is raised when attempting to access trust-gated content
    (such as private memories) without sufficient trust level.

    Args:
        required: Required trust level for access.
        actual: Actual trust level of the requesting individual.
        resource: Optional description of the resource being accessed.

    Example:
        >>> raise TrustThresholdError(required=0.8, actual=0.5, resource="private memory")
        TrustThresholdError: Insufficient trust level 0.5 for 'private memory' (requires 0.8)
    """

    def __init__(
        self,
        *,
        required: float,
        actual: float,
        resource: str | None = None,
    ) -> None:
        """Initialize TrustThresholdError with trust levels.

        Args:
            required: Required trust level for access.
            actual: Actual trust level of the requesting individual.
            resource: Optional description of the resource being accessed.
        """
        self.required = required
        self.actual = actual
        self.resource = resource
        resource_str = f" for '{resource}'" if resource else ""
        message = f"Insufficient trust level {actual}{resource_str} (requires {required})"
        super().__init__(message)


class SimulationError(PersonautError):
    """Raised when a simulation fails to execute properly.

    This exception is raised for errors during simulation execution,
    including configuration errors, runtime failures, and model errors.

    Args:
        message: Description of the simulation error.
        simulation_id: Optional ID of the failed simulation.
        phase: Optional phase where the error occurred.

    Example:
        >>> raise SimulationError(
        ...     "Model timeout", simulation_id="sim_123", phase="generation"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        simulation_id: str | None = None,
        phase: str | None = None,
    ) -> None:
        """Initialize SimulationError with context.

        Args:
            message: Description of the simulation error.
            simulation_id: Optional ID of the failed simulation.
            phase: Optional phase where the error occurred.
        """
        self.simulation_id = simulation_id
        self.phase = phase
        context_parts = []
        if simulation_id:
            context_parts.append(f"simulation={simulation_id}")
        if phase:
            context_parts.append(f"phase={phase}")
        if context_parts:
            message = f"[{', '.join(context_parts)}] {message}"
        super().__init__(message)


class ModelError(PersonautError):
    """Raised when a model provider encounters an error.

    This exception is raised for errors related to LLM model providers,
    including API errors, authentication failures, and rate limits.

    Args:
        message: Description of the model error.
        provider: Name of the model provider (e.g., "gemini", "bedrock").
        model: Optional model identifier.
        retryable: Whether the error is potentially retryable.

    Example:
        >>> raise ModelError("Rate limit exceeded", provider="gemini", retryable=True)
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        model: str | None = None,
        retryable: bool = False,
    ) -> None:
        """Initialize ModelError with provider context.

        Args:
            message: Description of the model error.
            provider: Name of the model provider.
            model: Optional model identifier.
            retryable: Whether the error is potentially retryable.
        """
        self.provider = provider
        self.model = model
        self.retryable = retryable
        context = f"[{provider}"
        if model:
            context += f"/{model}"
        context += "]"
        super().__init__(f"{context} {message}")


class MemoryError(PersonautError):
    """Raised when the memory system encounters an error.

    This exception is raised for errors in the memory storage and retrieval
    system, including database errors and embedding failures.

    Args:
        message: Description of the memory error.
        operation: Optional operation that failed (e.g., "store", "search").
        memory_id: Optional ID of the affected memory.

    Example:
        >>> raise MemoryError("Vector store connection failed", operation="search")
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        memory_id: str | None = None,
    ) -> None:
        """Initialize MemoryError with context.

        Args:
            message: Description of the memory error.
            operation: Optional operation that failed.
            memory_id: Optional ID of the affected memory.
        """
        self.operation = operation
        self.memory_id = memory_id
        context_parts = []
        if operation:
            context_parts.append(f"operation={operation}")
        if memory_id:
            context_parts.append(f"memory_id={memory_id}")
        if context_parts:
            message = f"[{', '.join(context_parts)}] {message}"
        super().__init__(message)


# ── Age safety ──────────────────────────────────────────────────────────
# Remember what Uncle Ben said: "With great power comes great
# responsibility." Don't be a creep!
MINIMUM_SIMULATION_AGE: int = 18
"""The minimum age (in years) for any simulated individual."""


class AgeRestrictionError(ValidationError):
    """Raised when attempting to simulate an individual under 18.

    All simulated individuals must be at least 18 years old.
    This restriction exists to ensure responsible and ethical use
    of persona simulation technology.

    Args:
        age: The age that was provided.
        name: Optional name of the individual.

    Example:
        >>> raise AgeRestrictionError(15, name="Test")
        AgeRestrictionError: age: Individual 'Test' must be at least 18 years old (got 15).
    """

    def __init__(self, age: int, *, name: str | None = None) -> None:
        """Initialize AgeRestrictionError.

        Args:
            age: The age that was provided.
            name: Optional name of the individual.
        """
        self.age = age
        who = f"Individual '{name}'" if name else "Individual"
        message = (
            f"{who} must be at least {MINIMUM_SIMULATION_AGE} years old (got {age}). "
            f"All simulated personas must represent adults."
        )
        super().__init__(message, field="age", value=age)


class ConfigurationError(PersonautError):
    """Raised when configuration is invalid or missing.

    This exception is raised for configuration-related errors, including
    missing required settings and invalid configuration values.

    Args:
        message: Description of the configuration error.
        key: Optional configuration key that is problematic.

    Example:
        >>> raise ConfigurationError("Missing API key", key="GEMINI_API_KEY")
    """

    def __init__(self, message: str, *, key: str | None = None) -> None:
        """Initialize ConfigurationError with context.

        Args:
            message: Description of the configuration error.
            key: Optional configuration key that is problematic.
        """
        self.key = key
        if key:
            message = f"Configuration '{key}': {message}"
        super().__init__(message)


__all__ = [
    "AgeRestrictionError",
    "ConfigurationError",
    "EmotionNotFoundError",
    "EmotionValueError",
    "MINIMUM_SIMULATION_AGE",
    "MemoryError",
    "ModelError",
    "PersonautError",
    "SimulationError",
    "TraitNotFoundError",
    "TraitValueError",
    "TrustThresholdError",
    "ValidationError",
]
