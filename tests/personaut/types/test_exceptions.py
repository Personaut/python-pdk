"""Tests for exception classes."""

from __future__ import annotations

import pytest

from personaut.types.exceptions import (
    ConfigurationError,
    EmotionNotFoundError,
    EmotionValueError,
    MemoryError,
    ModelError,
    PersonautError,
    SimulationError,
    TraitNotFoundError,
    TraitValueError,
    TrustThresholdError,
    ValidationError,
)


class TestPersonautError:
    """Tests for PersonautError base class."""

    def test_is_exception(self) -> None:
        """PersonautError should be an Exception."""
        error = PersonautError("Test error")
        assert isinstance(error, Exception)

    def test_message(self) -> None:
        """PersonautError should store error message."""
        error = PersonautError("Test message")
        assert str(error) == "Test message"


class TestValidationError:
    """Tests for ValidationError."""

    def test_inherits_from_personaut_error(self) -> None:
        """ValidationError should inherit from PersonautError."""
        error = ValidationError("Invalid input")
        assert isinstance(error, PersonautError)

    def test_simple_message(self) -> None:
        """ValidationError should work with just a message."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"

    def test_includes_field_in_message(self) -> None:
        """ValidationError should include field name in message."""
        error = ValidationError("cannot be empty", field="name")
        assert "name" in str(error)
        assert "cannot be empty" in str(error)

    def test_stores_field_and_value(self) -> None:
        """ValidationError should store field and value attributes."""
        error = ValidationError("Invalid", field="age", value=-1)
        assert error.field == "age"
        assert error.value == -1


class TestEmotionValueError:
    """Tests for EmotionValueError."""

    def test_inherits_from_validation_error(self) -> None:
        """EmotionValueError should inherit from ValidationError."""
        error = EmotionValueError("anxious", 1.5)
        assert isinstance(error, ValidationError)
        assert isinstance(error, PersonautError)

    def test_error_message_format(self) -> None:
        """EmotionValueError should format message with emotion and value."""
        error = EmotionValueError("anxious", 1.5)
        assert "anxious" in str(error)
        assert "1.5" in str(error)
        assert "0.0" in str(error)
        assert "1.0" in str(error)

    def test_stores_emotion_attribute(self) -> None:
        """EmotionValueError should store emotion name."""
        error = EmotionValueError("hopeful", -0.5)
        assert error.emotion == "hopeful"

    @pytest.mark.parametrize(
        ("emotion", "value"),
        [
            ("angry", 1.1),
            ("sad", -0.1),
            ("fearful", 2.0),
            ("joyful", 100.0),
        ],
    )
    def test_various_invalid_values(self, emotion: str, value: float) -> None:
        """EmotionValueError should work with various invalid values."""
        error = EmotionValueError(emotion, value)
        assert error.emotion == emotion
        assert str(value) in str(error)


class TestEmotionNotFoundError:
    """Tests for EmotionNotFoundError."""

    def test_inherits_from_personaut_error(self) -> None:
        """EmotionNotFoundError should inherit from PersonautError."""
        error = EmotionNotFoundError("happiness")
        assert isinstance(error, PersonautError)

    def test_error_message(self) -> None:
        """EmotionNotFoundError should include emotion name in message."""
        error = EmotionNotFoundError("happiness")
        assert "happiness" in str(error)
        assert "Unknown emotion" in str(error)

    def test_with_available_emotions(self) -> None:
        """EmotionNotFoundError should include available emotions if provided."""
        error = EmotionNotFoundError("happiness", available=["anxious", "hopeful"])
        assert "anxious" in str(error)


class TestTraitNotFoundError:
    """Tests for TraitNotFoundError."""

    def test_inherits_from_personaut_error(self) -> None:
        """TraitNotFoundError should inherit from PersonautError."""
        error = TraitNotFoundError("bravery")
        assert isinstance(error, PersonautError)

    def test_error_message(self) -> None:
        """TraitNotFoundError should include trait name in message."""
        error = TraitNotFoundError("bravery")
        assert "bravery" in str(error)
        assert "Unknown trait" in str(error)

    def test_stores_trait_attribute(self) -> None:
        """TraitNotFoundError should store trait name."""
        error = TraitNotFoundError("courage")
        assert error.trait == "courage"


class TestTraitValueError:
    """Tests for TraitValueError."""

    def test_inherits_from_validation_error(self) -> None:
        """TraitValueError should inherit from ValidationError."""
        error = TraitValueError("warmth", 1.5)
        assert isinstance(error, ValidationError)

    def test_error_message_format(self) -> None:
        """TraitValueError should format message correctly."""
        error = TraitValueError("warmth", -0.5)
        assert "warmth" in str(error)
        assert "-0.5" in str(error)


class TestTrustThresholdError:
    """Tests for TrustThresholdError."""

    def test_inherits_from_personaut_error(self) -> None:
        """TrustThresholdError should inherit from PersonautError."""
        error = TrustThresholdError(required=0.8, actual=0.5)
        assert isinstance(error, PersonautError)

    def test_error_message_includes_levels(self) -> None:
        """TrustThresholdError should include both trust levels."""
        error = TrustThresholdError(required=0.8, actual=0.5)
        assert "0.8" in str(error)
        assert "0.5" in str(error)

    def test_includes_resource_if_provided(self) -> None:
        """TrustThresholdError should include resource name if provided."""
        error = TrustThresholdError(required=0.8, actual=0.5, resource="private memory")
        assert "private memory" in str(error)

    def test_stores_attributes(self) -> None:
        """TrustThresholdError should store all attributes."""
        error = TrustThresholdError(required=0.9, actual=0.3, resource="secret")
        assert error.required == 0.9
        assert error.actual == 0.3
        assert error.resource == "secret"


class TestSimulationError:
    """Tests for SimulationError."""

    def test_inherits_from_personaut_error(self) -> None:
        """SimulationError should inherit from PersonautError."""
        error = SimulationError("Timeout")
        assert isinstance(error, PersonautError)

    def test_simple_message(self) -> None:
        """SimulationError should work with just a message."""
        error = SimulationError("Timeout")
        assert "Timeout" in str(error)

    def test_includes_simulation_id(self) -> None:
        """SimulationError should include simulation ID if provided."""
        error = SimulationError("Failed", simulation_id="sim_123")
        assert "sim_123" in str(error)

    def test_includes_phase(self) -> None:
        """SimulationError should include phase if provided."""
        error = SimulationError("Error", phase="generation")
        assert "generation" in str(error)


class TestModelError:
    """Tests for ModelError."""

    def test_inherits_from_personaut_error(self) -> None:
        """ModelError should inherit from PersonautError."""
        error = ModelError("Rate limit", provider="gemini")
        assert isinstance(error, PersonautError)

    def test_includes_provider(self) -> None:
        """ModelError should include provider in message."""
        error = ModelError("Rate limit", provider="gemini")
        assert "gemini" in str(error)

    def test_includes_model(self) -> None:
        """ModelError should include model if provided."""
        error = ModelError("Error", provider="bedrock", model="claude-3")
        assert "bedrock" in str(error)
        assert "claude-3" in str(error)

    def test_retryable_attribute(self) -> None:
        """ModelError should store retryable flag."""
        error = ModelError("Rate limit", provider="gemini", retryable=True)
        assert error.retryable is True


class TestMemoryError:
    """Tests for MemoryError."""

    def test_inherits_from_personaut_error(self) -> None:
        """MemoryError should inherit from PersonautError."""
        error = MemoryError("Connection failed")
        assert isinstance(error, PersonautError)

    def test_includes_operation(self) -> None:
        """MemoryError should include operation if provided."""
        error = MemoryError("Failed", operation="search")
        assert "search" in str(error)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_inherits_from_personaut_error(self) -> None:
        """ConfigurationError should inherit from PersonautError."""
        error = ConfigurationError("Missing value")
        assert isinstance(error, PersonautError)

    def test_includes_key(self) -> None:
        """ConfigurationError should include key if provided."""
        error = ConfigurationError("Missing", key="API_KEY")
        assert "API_KEY" in str(error)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_catch_all_with_personaut_error(self) -> None:
        """All custom exceptions should be catchable with PersonautError."""
        exceptions = [
            ValidationError("test"),
            EmotionValueError("test", 1.5),
            TraitNotFoundError("test"),
            TrustThresholdError(required=0.8, actual=0.5),
            SimulationError("test"),
            ModelError("test", provider="test"),
            MemoryError("test"),
            ConfigurationError("test"),
        ]

        for exc in exceptions:
            with pytest.raises(PersonautError):
                raise exc
