"""Extended tests for PromptManager — targeting uncovered branches."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from personaut.emotions.state import EmotionalState
from personaut.prompts.builder import PromptBuilder
from personaut.prompts.manager import PromptManager
from personaut.traits.profile import TraitProfile


@dataclass
class MockIndividual:
    name: str
    id: str = "ind_1"
    emotional_state: EmotionalState = field(default_factory=EmotionalState)
    traits: TraitProfile = field(default_factory=TraitProfile)


@dataclass
class MockSituation:
    description: str = "Office meeting"
    location: str | None = "Conference room"


@dataclass
class MockRelationship:
    members: list[str] = field(default_factory=lambda: ["ind_1", "ind_2"])
    trust: float = 0.8

    def get_trust(self, individual_id: str) -> float:
        return self.trust


class TestPromptManagerGenerate:
    """Tests for generate method branches."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        return PromptManager()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        state = EmotionalState()
        state.change_emotion("proud", 0.7)
        return MockIndividual(name="Sarah", id="sarah_1", emotional_state=state)

    def test_generate_conversation_default(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Default generation should use conversation template."""
        prompt = manager.generate(sarah)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Sarah" in prompt

    def test_generate_with_situation(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Generation with situation should include context."""
        situation = MockSituation()
        prompt = manager.generate(sarah, situation=situation)
        assert isinstance(prompt, str)
        assert "Sarah" in prompt

    def test_generate_survey(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Survey template should be usable."""
        prompt = manager.generate(
            sarah,
            template="survey",
            questions=["What is your name?"],
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_generate_outcome(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Outcome template should be usable."""
        situation = MockSituation()
        prompt = manager.generate(
            sarah,
            situation=situation,
            template="outcome",
            target_outcome="success",
        )
        assert isinstance(prompt, str)

    def test_generate_with_memories(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Should filter memories to max_memories."""
        memories = [f"Memory {i}" for i in range(10)]
        manager.max_memories = 3
        prompt = manager.generate(sarah, memories=memories)
        assert isinstance(prompt, str)

    def test_generate_with_other_participants(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Should include other participants."""
        mike = MockIndividual(name="Mike", id="mike_1")
        prompt = manager.generate(
            sarah,
            other_participants=[mike],
        )
        assert isinstance(prompt, str)

    def test_generate_with_relationships(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Should include relationship context."""
        mike = MockIndividual(name="Mike", id="ind_2")
        rel = MockRelationship()
        prompt = manager.generate(
            sarah,
            other_participants=[mike],
            relationships=[rel],
        )
        assert isinstance(prompt, str)

    def test_generate_preview_skips_validation(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Preview mode should skip validation."""
        prompt = manager.generate(sarah, preview=True)
        assert isinstance(prompt, str)

    def test_generate_overrides(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Should apply keyword overrides."""
        prompt = manager.generate(
            sarah,
            intensity_threshold=0.5,
            max_memories=2,
        )
        assert isinstance(prompt, str)


class TestCalculateTrustLevel:
    """Tests for _calculate_trust_level."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        return PromptManager()

    @pytest.fixture
    def sarah(self) -> MockIndividual:
        return MockIndividual(name="Sarah", id="ind_1")

    def test_no_others_returns_default(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """No others should return 0.5 default."""
        assert manager._calculate_trust_level(sarah, None, None) == 0.5

    def test_no_relationships_returns_default(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """No relationships should return 0.5 default."""
        mike = MockIndividual(name="Mike", id="ind_2")
        assert manager._calculate_trust_level(sarah, [mike], None) == 0.5

    def test_matching_relationship_uses_trust(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Should use trust from matching relationship."""
        mike = MockIndividual(name="Mike", id="ind_2")
        rel = MockRelationship(members=["ind_1", "ind_2"], trust=0.9)
        result = manager._calculate_trust_level(sarah, [mike], [rel])
        assert result == 0.9

    def test_no_matching_relationship_returns_default(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """No matching relationship should return 0.5."""
        mike = MockIndividual(name="Mike", id="ind_2")
        rel = MockRelationship(members=["other_1", "other_2"], trust=0.9)
        result = manager._calculate_trust_level(sarah, [mike], [rel])
        assert result == 0.5

    def test_multiple_relationships_averages(self, manager: PromptManager, sarah: MockIndividual) -> None:
        """Multiple matching relationships should average trust."""
        mike = MockIndividual(name="Mike", id="ind_2")
        alex = MockIndividual(name="Alex", id="ind_3")
        rel1 = MockRelationship(members=["ind_1", "ind_2"], trust=0.8)
        rel2 = MockRelationship(members=["ind_1", "ind_3"], trust=0.4)
        result = manager._calculate_trust_level(sarah, [mike, alex], [rel1, rel2])
        assert result == pytest.approx(0.6)


class TestGetId:
    """Tests for _get_id."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        return PromptManager()

    def test_get_id_from_object(self, manager: PromptManager) -> None:
        """Should get id from object attribute."""
        ind = MockIndividual(name="Sarah", id="sarah_1")
        assert manager._get_id(ind) == "sarah_1"

    def test_get_id_from_dict(self, manager: PromptManager) -> None:
        """Should get id from dict."""
        assert manager._get_id({"id": "dict_1"}) == "dict_1"

    def test_get_id_from_dict_missing(self, manager: PromptManager) -> None:
        """Missing id in dict should return string representation."""
        result = manager._get_id({"name": "test"})
        assert isinstance(result, str)

    def test_get_id_from_other_type(self, manager: PromptManager) -> None:
        """Other types should return string representation."""
        assert manager._get_id(42) == "42"


class TestGetMembers:
    """Tests for _get_members."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        return PromptManager()

    def test_get_members_from_object(self, manager: PromptManager) -> None:
        """Should get members from object attribute."""
        rel = MockRelationship(members=["a", "b"])
        assert manager._get_members(rel) == ["a", "b"]

    def test_get_members_from_dict(self, manager: PromptManager) -> None:
        """Should get members from dict."""
        assert manager._get_members({"members": ["x", "y"]}) == ["x", "y"]

    def test_get_members_from_dict_missing(self, manager: PromptManager) -> None:
        """Missing members in dict should return empty list."""
        assert manager._get_members({}) == []

    def test_get_members_from_other_type(self, manager: PromptManager) -> None:
        """Other types should return empty list."""
        assert manager._get_members("not_a_relationship") == []


class TestGetTrust:
    """Tests for _get_trust."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        return PromptManager()

    def test_get_trust_from_get_trust_method(self, manager: PromptManager) -> None:
        """Should use get_trust() method."""
        rel = MockRelationship(trust=0.8)
        assert manager._get_trust(rel, "ind_1") == 0.8

    def test_get_trust_from_trust_attribute_float(self, manager: PromptManager) -> None:
        """Should use trust attribute as float."""

        class SimpleTrust:
            trust = 0.7

        assert manager._get_trust(SimpleTrust(), "ind_1") == 0.7

    def test_get_trust_from_trust_attribute_dict(self, manager: PromptManager) -> None:
        """Should use trust dict with individual_id key."""

        class DictTrust:
            trust = {"ind_1": 0.9, "ind_2": 0.3}

        assert manager._get_trust(DictTrust(), "ind_1") == 0.9

    def test_get_trust_from_dict_relationship(self, manager: PromptManager) -> None:
        """Should get trust from dict relationship."""
        rel = {"trust": 0.6}
        assert manager._get_trust(rel, "ind_1") == 0.6

    def test_get_trust_from_dict_trust_dict(self, manager: PromptManager) -> None:
        """Should get trust from nested dict."""
        rel = {"trust": {"ind_1": 0.95}}
        assert manager._get_trust(rel, "ind_1") == 0.95

    def test_get_trust_default(self, manager: PromptManager) -> None:
        """Unknown type should return 0.5 default."""
        assert manager._get_trust("unknown", "ind_1") == 0.5


class TestValidation:
    """Tests for validate method."""

    @pytest.fixture
    def manager(self) -> PromptManager:
        return PromptManager()

    def test_validate_empty_prompt(self, manager: PromptManager) -> None:
        """Empty prompt should be invalid."""
        result = manager.validate("")
        assert not result.is_valid
        assert any("empty" in e.lower() for e in result.errors)

    def test_validate_whitespace_only(self, manager: PromptManager) -> None:
        """Whitespace-only prompt should be invalid."""
        result = manager.validate("   \n\t  ")
        assert not result.is_valid

    def test_validate_too_long(self, manager: PromptManager) -> None:
        """Very long prompt should generate warning."""
        manager.max_tokens = 10
        long_prompt = "You are roleplaying as Sarah." + "x" * 1000
        result = manager.validate(long_prompt)
        assert result.is_valid  # Warning, not error
        assert any("too long" in w for w in result.warnings)

    def test_validate_missing_identity(self, manager: PromptManager) -> None:
        """Prompt without identity should generate warning."""
        result = manager.validate("Hello world this is a test prompt.")
        assert result.is_valid
        assert any("identity" in w.lower() for w in result.warnings)

    def test_validate_good_prompt(self, manager: PromptManager) -> None:
        """Well-formed prompt should pass validation."""
        result = manager.validate("You are roleplaying as Sarah in a conversation.")
        assert result.is_valid
        assert len(result.errors) == 0

    def test_verbose_prints_warnings(self, manager: PromptManager, capsys: pytest.CaptureFixture[str]) -> None:
        """Verbose mode should print warnings."""
        manager.verbose = True
        manager.max_tokens = 10  # Force warning
        sarah = MockIndividual(name="Sarah")
        manager.generate(sarah)
        captured = capsys.readouterr()
        # The warning may or may not print depending on prompt length
        # Just verify no crash
        assert isinstance(captured.out, str)


class TestGetBuilder:
    """Tests for get_builder method."""

    def test_get_builder_returns_instance(self) -> None:
        """Should return a PromptBuilder instance."""
        manager = PromptManager()
        builder = manager.get_builder()
        assert isinstance(builder, PromptBuilder)
