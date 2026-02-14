"""Tests for PromptManager."""

import pytest

from personaut.emotions.state import EmotionalState
from personaut.prompts.manager import PromptManager, ValidationResult
from personaut.situations.situation import create_situation
from personaut.traits.profile import TraitProfile
from personaut.types.modality import Modality


class MockIndividual:
    """Mock individual for testing."""

    def __init__(
        self,
        name: str,
        emotional_state: EmotionalState | None = None,
        traits: TraitProfile | None = None,
    ) -> None:
        self.id = f"{name.lower()}-1"
        self.name = name
        self.emotional_state = emotional_state or EmotionalState()
        self.traits = traits or TraitProfile()


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_default_is_valid(self) -> None:
        """Test that default result is valid."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_can_add_errors(self) -> None:
        """Test adding errors."""
        result = ValidationResult(is_valid=False, errors=["Test error"])
        assert result.is_valid is False
        assert "Test error" in result.errors

    def test_can_add_warnings(self) -> None:
        """Test adding warnings."""
        result = ValidationResult(warnings=["Test warning"])
        assert result.is_valid is True
        assert "Test warning" in result.warnings


class TestPromptManager:
    """Tests for PromptManager class."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        """Create a manager for testing."""
        return PromptManager()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        """Create Sarah individual."""
        state = EmotionalState()
        state.change_emotion("anxious", 0.6)

        traits = TraitProfile()
        traits.set_trait("warmth", 0.8)

        return MockIndividual("Sarah", state, traits)

    @pytest.fixture
    def situation(self):
        """Create a test situation."""
        return create_situation(
            modality=Modality.IN_PERSON,
            description="Meeting",
        )

    def test_generate_basic(
        self,
        manager: PromptManager,
        sarah: MockIndividual,
    ) -> None:
        """Test basic prompt generation."""
        prompt = manager.generate(sarah)
        assert "Sarah" in prompt

    def test_generate_with_situation(
        self,
        manager: PromptManager,
        sarah: MockIndividual,
        situation,
    ) -> None:
        """Test generation with situation."""
        prompt = manager.generate(sarah, situation)
        assert "Meeting" in prompt

    def test_generate_conversation(
        self,
        manager: PromptManager,
        sarah: MockIndividual,
    ) -> None:
        """Test conversation template."""
        prompt = manager.generate(sarah, template="conversation")
        assert "respond as" in prompt.lower()

    def test_generate_survey(
        self,
        manager: PromptManager,
        sarah: MockIndividual,
    ) -> None:
        """Test survey template."""
        prompt = manager.generate(
            sarah,
            template="survey",
            questions=["Rate your satisfaction"],
        )
        assert "survey" in prompt.lower()

    def test_generate_outcome(
        self,
        manager: PromptManager,
        sarah: MockIndividual,
    ) -> None:
        """Test outcome template."""
        prompt = manager.generate(
            sarah,
            template="outcome",
            target_outcome="Close the deal",
        )
        assert "analyze" in prompt.lower()

    def test_validate_valid_prompt(self, manager: PromptManager) -> None:
        """Test validation of valid prompt."""
        prompt = "You are roleplaying as Sarah. Respond naturally."
        result = manager.validate(prompt)
        assert result.is_valid is True

    def test_validate_empty_prompt(self, manager: PromptManager) -> None:
        """Test validation of empty prompt."""
        result = manager.validate("")
        assert result.is_valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_validate_long_prompt_warning(self, manager: PromptManager) -> None:
        """Test validation warns on long prompts."""
        long_prompt = "x" * 10000  # Very long
        result = manager.validate(long_prompt)
        assert any("long" in w.lower() for w in result.warnings)

    def test_get_builder(self, manager: PromptManager) -> None:
        """Test getting a builder from manager."""
        builder = manager.get_builder()
        assert builder is not None

    def test_default_settings(self) -> None:
        """Test default manager settings."""
        manager = PromptManager()
        assert manager.intensity_threshold == 0.3
        assert manager.max_memories == 5
        assert manager.default_template == "conversation"

    def test_custom_settings(self) -> None:
        """Test custom manager settings."""
        manager = PromptManager(
            intensity_threshold=0.5,
            max_memories=3,
            default_template="survey",
        )
        assert manager.intensity_threshold == 0.5
        assert manager.max_memories == 3
        assert manager.default_template == "survey"

    def test_preview_mode(
        self,
        manager: PromptManager,
        sarah: MockIndividual,
    ) -> None:
        """Test preview mode."""
        prompt = manager.generate(sarah, preview=True)
        assert "Sarah" in prompt  # Still generates prompt
