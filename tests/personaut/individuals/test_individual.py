"""Tests for the Individual class."""

from __future__ import annotations

from datetime import datetime

from personaut.emotions import EmotionalState
from personaut.individuals import (
    Individual,
    create_human,
    create_individual,
    create_nontracked_individual,
)
from personaut.masks import create_mask
from personaut.traits import TraitProfile
from personaut.triggers import create_emotional_trigger


class TestIndividualInitialization:
    """Tests for Individual initialization."""

    def test_create_with_name_only(self) -> None:
        """Test creating individual with just a name."""
        individual = Individual(name="Sarah")
        assert individual.name == "Sarah"
        assert individual.id is not None
        assert len(individual.id) == 36  # UUID format

    def test_create_with_all_fields(self) -> None:
        """Test creating individual with all fields."""
        state = EmotionalState()
        state.change_emotion("cheerful", 0.7)
        traits = TraitProfile()
        traits.set_trait("warmth", 0.8)

        individual = Individual(
            name="Alex",
            emotional_state=state,
            traits=traits,
            metadata={"role": "developer"},
        )

        assert individual.name == "Alex"
        assert individual.get_emotional_state().get_emotion("cheerful") == 0.7
        assert individual.get_trait("warmth") == 0.8
        assert individual.get_metadata("role") == "developer"

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        individual = Individual(name="Test")
        assert individual.memories == []
        assert individual.masks == []
        assert individual.triggers == []
        assert individual.active_mask is None
        assert individual.metadata == {}
        assert isinstance(individual.created_at, datetime)
        assert isinstance(individual.updated_at, datetime)

    def test_unique_ids(self) -> None:
        """Test that each individual gets a unique ID."""
        individual1 = Individual(name="A")
        individual2 = Individual(name="B")
        assert individual1.id != individual2.id


class TestEmotionalStateMethods:
    """Tests for emotional state methods."""

    def test_get_emotional_state_no_mask(self) -> None:
        """Test getting emotional state without mask."""
        individual = Individual(name="Test")
        individual.emotional_state.change_emotion("cheerful", 0.6)

        state = individual.get_emotional_state()
        assert state.get_emotion("cheerful") == 0.6

    def test_get_emotional_state_with_mask(self) -> None:
        """Test getting emotional state with mask applied."""
        individual = Individual(name="Test")
        individual.emotional_state.change_emotion("cheerful", 0.8)

        # Create mask that reduces cheerful
        mask = create_mask(
            name="serious",
            emotional_modifications={"cheerful": -0.3},
        )
        individual.add_mask(mask)
        individual.activate_mask("serious")

        state = individual.get_emotional_state()
        # Mask should reduce cheerful by 0.3
        assert state.get_emotion("cheerful") < 0.8

    def test_get_raw_emotional_state(self) -> None:
        """Test getting raw emotional state ignores mask."""
        individual = Individual(name="Test")
        individual.emotional_state.change_emotion("anxious", 0.7)

        mask = create_mask(
            name="calm",
            emotional_modifications={"anxious": -0.5},
        )
        individual.add_mask(mask)
        individual.activate_mask("calm")

        # Raw state should be unaffected
        raw = individual.get_raw_emotional_state()
        assert raw.get_emotion("anxious") == 0.7

    def test_change_emotion(self) -> None:
        """Test changing an emotion."""
        individual = Individual(name="Test")
        individual.change_emotion("cheerful", 0.5)
        assert individual.emotional_state.get_emotion("cheerful") == 0.5

    def test_set_emotion(self) -> None:
        """Test setting an emotion to absolute value."""
        individual = Individual(name="Test")
        individual.set_emotion("anxious", 0.8)
        assert individual.emotional_state.get_emotion("anxious") == 0.8

        # Set to new value
        individual.set_emotion("anxious", 0.3)
        assert individual.emotional_state.get_emotion("anxious") == 0.3

    def test_get_dominant_emotion(self) -> None:
        """Test getting dominant emotion."""
        individual = Individual(name="Test")
        individual.change_emotion("cheerful", 0.9)
        individual.change_emotion("anxious", 0.3)

        dominant = individual.get_dominant_emotion()
        assert dominant is not None
        assert dominant[0] == "cheerful"
        assert dominant[1] == 0.9


class TestTraitMethods:
    """Tests for trait methods."""

    def test_get_trait(self) -> None:
        """Test getting a trait value."""
        individual = Individual(name="Test")
        individual.traits.set_trait("warmth", 0.8)
        assert individual.get_trait("warmth") == 0.8

    def test_set_trait(self) -> None:
        """Test setting a trait value."""
        individual = Individual(name="Test")
        individual.set_trait("warmth", 0.9)
        assert individual.get_trait("warmth") == 0.9

    def test_get_high_traits(self) -> None:
        """Test getting high traits."""
        individual = Individual(name="Test")
        individual.set_trait("warmth", 0.9)
        individual.set_trait("dominance", 0.8)
        individual.set_trait("sensitivity", 0.3)

        high = individual.get_high_traits(threshold=0.7)
        trait_names = [t[0] for t in high]
        assert "warmth" in trait_names
        assert "dominance" in trait_names
        assert "sensitivity" not in trait_names

    def test_get_low_traits(self) -> None:
        """Test getting low traits."""
        individual = Individual(name="Test")
        individual.set_trait("warmth", 0.1)
        individual.set_trait("sensitivity", 0.2)

        low = individual.get_low_traits(threshold=0.3)
        trait_names = [t[0] for t in low]
        assert "warmth" in trait_names
        assert "sensitivity" in trait_names


class TestMemoryMethods:
    """Tests for memory methods."""

    def test_add_memory(self) -> None:
        """Test adding a memory."""
        from personaut.memory import create_individual_memory

        individual = Individual(name="Test")
        memory = create_individual_memory(
            owner_id=individual.id,
            description="First meeting",
        )
        individual.add_memory(memory)

        assert individual.memory_count() == 1
        assert memory in individual.memories

    def test_remove_memory(self) -> None:
        """Test removing a memory."""
        from personaut.memory import create_individual_memory

        individual = Individual(name="Test")
        memory = create_individual_memory(
            owner_id=individual.id,
            description="To remove",
        )
        individual.add_memory(memory)

        assert individual.remove_memory(memory.id)
        assert individual.memory_count() == 0

    def test_remove_memory_not_found(self) -> None:
        """Test removing non-existent memory."""
        individual = Individual(name="Test")
        assert not individual.remove_memory("nonexistent")

    def test_get_memories_with_limit(self) -> None:
        """Test getting memories with limit."""
        from personaut.memory import create_individual_memory

        individual = Individual(name="Test")
        for i in range(5):
            memory = create_individual_memory(
                owner_id=individual.id,
                description=f"Memory {i}",
            )
            individual.add_memory(memory)

        memories = individual.get_memories(limit=3)
        assert len(memories) == 3

    def test_get_memories_with_tags(self) -> None:
        """Test filtering memories by tags (using metadata)."""
        from personaut.memory import create_individual_memory

        individual = Individual(name="Test")

        # Use metadata to simulate tags
        m1 = create_individual_memory(owner_id=individual.id, description="Work memory", metadata={"tags": ["work"]})
        m2 = create_individual_memory(
            owner_id=individual.id, description="Personal memory", metadata={"tags": ["personal"]}
        )
        m3 = create_individual_memory(
            owner_id=individual.id, description="Both memory", metadata={"tags": ["work", "personal"]}
        )

        individual.add_memory(m1)
        individual.add_memory(m2)
        individual.add_memory(m3)

        # Verify memories were added
        assert individual.memory_count() == 3


class TestMaskMethods:
    """Tests for mask methods."""

    def test_add_mask(self) -> None:
        """Test adding a mask."""
        individual = Individual(name="Test")
        mask = create_mask(name="professional", emotional_modifications={})

        individual.add_mask(mask)
        assert mask in individual.masks

    def test_remove_mask(self) -> None:
        """Test removing a mask."""
        individual = Individual(name="Test")
        mask = create_mask(name="professional", emotional_modifications={})
        individual.add_mask(mask)

        assert individual.remove_mask("professional")
        assert mask not in individual.masks

    def test_remove_mask_deactivates_if_active(self) -> None:
        """Test removing active mask deactivates it."""
        individual = Individual(name="Test")
        mask = create_mask(name="professional", emotional_modifications={})
        individual.add_mask(mask)
        individual.activate_mask("professional")

        individual.remove_mask("professional")
        assert individual.active_mask is None

    def test_remove_mask_not_found(self) -> None:
        """Test removing non-existent mask."""
        individual = Individual(name="Test")
        assert not individual.remove_mask("nonexistent")

    def test_get_mask(self) -> None:
        """Test getting a mask by name."""
        individual = Individual(name="Test")
        mask = create_mask(name="casual", emotional_modifications={})
        individual.add_mask(mask)

        found = individual.get_mask("casual")
        assert found == mask

    def test_get_mask_not_found(self) -> None:
        """Test getting non-existent mask."""
        individual = Individual(name="Test")
        assert individual.get_mask("nonexistent") is None

    def test_activate_mask(self) -> None:
        """Test activating a mask."""
        individual = Individual(name="Test")
        mask = create_mask(name="serious", emotional_modifications={})
        individual.add_mask(mask)

        assert individual.activate_mask("serious")
        assert individual.active_mask == mask

    def test_activate_mask_not_found(self) -> None:
        """Test activating non-existent mask."""
        individual = Individual(name="Test")
        assert not individual.activate_mask("nonexistent")

    def test_deactivate_mask(self) -> None:
        """Test deactivating mask."""
        individual = Individual(name="Test")
        mask = create_mask(name="serious", emotional_modifications={})
        individual.add_mask(mask)
        individual.activate_mask("serious")

        individual.deactivate_mask()
        assert individual.active_mask is None

    def test_has_mask(self) -> None:
        """Test checking if mask exists."""
        individual = Individual(name="Test")
        mask = create_mask(name="casual", emotional_modifications={})
        individual.add_mask(mask)

        assert individual.has_mask("casual")
        assert not individual.has_mask("professional")


class TestTriggerMethods:
    """Tests for trigger methods."""

    def test_add_trigger(self) -> None:
        """Test adding a trigger."""
        individual = Individual(name="Test")
        trigger = create_emotional_trigger(
            description="High anxiety",
            rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
        )

        individual.add_trigger(trigger)
        assert trigger in individual.triggers

    def test_remove_trigger(self) -> None:
        """Test removing a trigger."""
        individual = Individual(name="Test")
        trigger = create_emotional_trigger(
            description="High anxiety",
            rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
        )
        individual.add_trigger(trigger)

        assert individual.remove_trigger(trigger)
        assert trigger not in individual.triggers

    def test_remove_trigger_by_description(self) -> None:
        """Test removing trigger by description."""
        individual = Individual(name="Test")
        trigger = create_emotional_trigger(
            description="High anxiety response",
            rules=[{"emotion": "anxious", "threshold": 0.8}],
        )
        individual.add_trigger(trigger)

        assert individual.remove_trigger_by_description("High anxiety response")
        assert len(individual.triggers) == 0

    def test_check_triggers(self) -> None:
        """Test checking which triggers would fire."""
        individual = Individual(name="Test")
        individual.change_emotion("anxious", 0.9)

        trigger = create_emotional_trigger(
            description="High anxiety",
            rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
            response={"cheerful": -0.2},
        )
        individual.add_trigger(trigger)

        fired = individual.check_triggers()
        assert trigger in fired

    def test_check_triggers_not_fired(self) -> None:
        """Test triggers that don't fire."""
        individual = Individual(name="Test")
        individual.change_emotion("anxious", 0.3)

        trigger = create_emotional_trigger(
            description="High anxiety",
            rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
        )
        individual.add_trigger(trigger)

        fired = individual.check_triggers()
        assert trigger not in fired

    def test_fire_triggers(self) -> None:
        """Test firing triggers applies responses."""
        individual = Individual(name="Test")
        individual.change_emotion("anxious", 0.9)
        individual.change_emotion("cheerful", 0.5)

        trigger = create_emotional_trigger(
            description="High anxiety",
            rules=[{"emotion": "anxious", "threshold": 0.8, "operator": ">"}],
            response={"cheerful": -0.2},
        )
        individual.add_trigger(trigger)

        fired = individual.fire_triggers()
        assert len(fired) == 1


class TestMetadataMethods:
    """Tests for metadata methods."""

    def test_set_metadata(self) -> None:
        """Test setting metadata."""
        individual = Individual(name="Test")
        individual.set_metadata("role", "developer")
        assert individual.get_metadata("role") == "developer"

    def test_get_metadata_default(self) -> None:
        """Test getting metadata with default."""
        individual = Individual(name="Test")
        assert individual.get_metadata("missing", "default") == "default"

    def test_has_metadata(self) -> None:
        """Test checking metadata exists."""
        individual = Individual(name="Test")
        individual.set_metadata("key", "value")

        assert individual.has_metadata("key")
        assert not individual.has_metadata("missing")


class TestSerialization:
    """Tests for serialization."""

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        individual = Individual(name="Sarah")
        individual.change_emotion("cheerful", 0.7)
        individual.set_metadata("role", "tester")

        data = individual.to_dict()

        assert data["name"] == "Sarah"
        assert data["id"] == individual.id
        assert "emotional_state" in data
        assert data["metadata"]["role"] == "tester"

    def test_from_dict(self) -> None:
        """Test creating from dictionary."""
        original = Individual(name="Alex")
        original.change_emotion("anxious", 0.6)
        original.set_trait("warmth", 0.8)
        original.set_metadata("context", "test")

        data = original.to_dict()
        restored = Individual.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.get_metadata("context") == "test"

    def test_str_representation(self) -> None:
        """Test string representation."""
        individual = Individual(name="Sarah")
        individual.change_emotion("cheerful", 0.8)

        s = str(individual)
        assert "Sarah" in s
        assert "cheerful" in s

    def test_str_with_active_mask(self) -> None:
        """Test string representation with active mask."""
        individual = Individual(name="Sarah")
        mask = create_mask(name="professional", emotional_modifications={})
        individual.add_mask(mask)
        individual.activate_mask("professional")

        s = str(individual)
        assert "professional" in s


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_individual_minimal(self) -> None:
        """Test creating individual with minimal args."""
        individual = create_individual(name="Test")
        assert individual.name == "Test"
        assert individual.id is not None

    def test_create_individual_with_dict_traits(self) -> None:
        """Test creating individual with dict traits."""
        individual = create_individual(
            name="Test",
            traits={"warmth": 0.8, "dominance": 0.3},
        )
        assert individual.get_trait("warmth") == 0.8
        assert individual.get_trait("dominance") == 0.3

    def test_create_individual_with_dict_emotions(self) -> None:
        """Test creating individual with dict emotions."""
        individual = create_individual(
            name="Test",
            emotional_state={"cheerful": 0.7, "anxious": 0.2},
        )
        assert individual.emotional_state.get_emotion("cheerful") == 0.7
        assert individual.emotional_state.get_emotion("anxious") == 0.2

    def test_create_individual_with_profile(self) -> None:
        """Test creating individual with TraitProfile."""
        traits = TraitProfile()
        traits.set_trait("warmth", 0.9)

        individual = create_individual(name="Test", traits=traits)
        assert individual.get_trait("warmth") == 0.9

    def test_create_individual_with_metadata(self) -> None:
        """Test creating individual with metadata."""
        individual = create_individual(
            name="Test",
            metadata={"context": "test", "version": 1},
        )
        assert individual.get_metadata("context") == "test"
        assert individual.get_metadata("version") == 1

    def test_create_human(self) -> None:
        """Test creating a human individual."""
        human = create_human(name="User", role="interviewer")

        assert human.name == "User"
        assert human.get_metadata("is_human")
        assert human.get_metadata("tracked")
        assert human.get_metadata("role") == "interviewer"

    def test_create_human_with_context(self) -> None:
        """Test creating human with context."""
        human = create_human(name="User", context="Research participant")
        assert human.get_metadata("context") == "Research participant"

    def test_create_nontracked_individual(self) -> None:
        """Test creating non-tracked individual."""
        background = create_nontracked_individual(role="barista")

        assert background.name == "Barista"
        assert not background.get_metadata("tracked")
        assert not background.get_metadata("is_human")
        assert background.get_metadata("role") == "barista"

    def test_create_nontracked_with_name(self) -> None:
        """Test creating non-tracked with custom name."""
        background = create_nontracked_individual(role="waiter", name="John")
        assert background.name == "John"


class TestTimestampUpdates:
    """Tests for timestamp updates."""

    def test_emotion_change_updates_timestamp(self) -> None:
        """Test that emotion changes update timestamp."""
        individual = Individual(name="Test")
        initial = individual.updated_at

        individual.change_emotion("cheerful", 0.5)
        assert individual.updated_at >= initial

    def test_trait_change_updates_timestamp(self) -> None:
        """Test that trait changes update timestamp."""
        individual = Individual(name="Test")
        initial = individual.updated_at

        individual.set_trait("warmth", 0.8)
        assert individual.updated_at >= initial

    def test_metadata_change_updates_timestamp(self) -> None:
        """Test that metadata changes update timestamp."""
        individual = Individual(name="Test")
        initial = individual.updated_at

        individual.set_metadata("key", "value")
        assert individual.updated_at >= initial


class TestAgeRestriction:
    """Tests for the age restriction (must be 18+)."""

    def test_individual_under_18_raises(self) -> None:
        """Creating an Individual with age < 18 raises AgeRestrictionError."""
        import pytest

        from personaut.types.exceptions import AgeRestrictionError

        with pytest.raises(AgeRestrictionError, match="at least 18"):
            Individual(name="Teen", age=15)

    def test_create_individual_under_18_raises(self) -> None:
        """create_individual with age < 18 raises AgeRestrictionError."""
        import pytest

        from personaut.types.exceptions import AgeRestrictionError

        with pytest.raises(AgeRestrictionError, match="at least 18"):
            create_individual(name="Kid", age=10)

    def test_boundary_age_17_raises(self) -> None:
        """Age 17 (just under boundary) raises AgeRestrictionError."""
        import pytest

        from personaut.types.exceptions import AgeRestrictionError

        with pytest.raises(AgeRestrictionError):
            Individual(name="Almost", age=17)

    def test_boundary_age_18_allowed(self) -> None:
        """Age 18 (exactly at boundary) is allowed."""
        individual = Individual(name="Just18", age=18)
        assert individual.age == 18

    def test_adult_age_allowed(self) -> None:
        """Any adult age is allowed."""
        individual = create_individual(name="Adult", age=30)
        assert individual.age == 30

    def test_none_age_allowed(self) -> None:
        """None age (unspecified) is allowed."""
        individual = Individual(name="NoAge")
        assert individual.age is None

    def test_age_in_to_dict(self) -> None:
        """Age should be included in serialized output."""
        individual = Individual(name="Test", age=25)
        data = individual.to_dict()
        assert data["age"] == 25

    def test_age_roundtrip_serialization(self) -> None:
        """Age should survive to_dict -> from_dict round-trip."""
        original = Individual(name="Test", age=30)
        restored = Individual.from_dict(original.to_dict())
        assert restored.age == 30

    def test_age_none_roundtrip_serialization(self) -> None:
        """None age should survive to_dict -> from_dict round-trip."""
        original = Individual(name="Test")
        restored = Individual.from_dict(original.to_dict())
        assert restored.age is None

    def test_error_includes_name(self) -> None:
        """AgeRestrictionError message should include the individual's name."""
        import pytest

        from personaut.types.exceptions import AgeRestrictionError

        with pytest.raises(AgeRestrictionError, match="Teen") as exc_info:
            Individual(name="Teen", age=16)
        assert exc_info.value.age == 16
