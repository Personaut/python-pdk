"""Tests for Situation class."""

from __future__ import annotations

from datetime import datetime

from personaut.situations import (
    Situation,
    create_situation,
)
from personaut.types.modality import Modality


class TestSituation:
    """Tests for Situation class."""

    def test_create_situation(self) -> None:
        """Should create a situation with basic attributes."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Team meeting",
        )

        assert situation.modality == Modality.IN_PERSON
        assert situation.description == "Team meeting"
        assert situation.id is not None

    def test_situation_with_time_and_location(self) -> None:
        """Should create situation with time and location."""
        now = datetime.now()
        situation = Situation(
            modality=Modality.VIDEO_CALL,
            description="Remote standup",
            time=now,
            location="Virtual",
        )

        assert situation.time == now
        assert situation.location == "Virtual"

    def test_situation_with_context(self) -> None:
        """Should create situation with context."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Coffee chat",
            context={
                "atmosphere": "relaxed",
                "environment": {"lighting": "natural"},
            },
        )

        assert situation.context["atmosphere"] == "relaxed"
        assert situation.context["environment"]["lighting"] == "natural"


class TestContextAccess:
    """Tests for context value access."""

    def test_get_context_value(self) -> None:
        """Should get simple context value."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
            context={"atmosphere": "tense"},
        )

        assert situation.get_context_value("atmosphere") == "tense"

    def test_get_context_value_nested(self) -> None:
        """Should get nested context value."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
            context={"environment": {"lighting": "dim"}},
        )

        assert situation.get_context_value("environment.lighting") == "dim"

    def test_get_context_value_default(self) -> None:
        """Should return default for missing key."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
        )

        assert situation.get_context_value("missing", "default") == "default"

    def test_set_context_value(self) -> None:
        """Should set context value."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
        )

        situation.set_context_value("mood", "happy")

        assert situation.context["mood"] == "happy"

    def test_set_context_value_nested(self) -> None:
        """Should set nested context value."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
        )

        situation.set_context_value("environment.lighting", "bright")

        assert situation.context["environment"]["lighting"] == "bright"

    def test_has_context(self) -> None:
        """Should check if context key exists."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
            context={"atmosphere": "relaxed"},
        )

        assert situation.has_context("atmosphere") is True
        assert situation.has_context("missing") is False


class TestParticipants:
    """Tests for participant management."""

    def test_add_participant(self) -> None:
        """Should add participant."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
        )

        situation.add_participant("alice")

        assert "alice" in situation.participants

    def test_add_participant_no_duplicates(self) -> None:
        """Should not add duplicate participant."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
        )

        situation.add_participant("alice")
        situation.add_participant("alice")

        assert situation.participants.count("alice") == 1

    def test_remove_participant(self) -> None:
        """Should remove participant."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
            participants=["alice", "bob"],
        )

        situation.remove_participant("alice")

        assert "alice" not in situation.participants
        assert "bob" in situation.participants

    def test_has_participant(self) -> None:
        """Should check if participant exists."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
            participants=["alice"],
        )

        assert situation.has_participant("alice") is True
        assert situation.has_participant("bob") is False


class TestTags:
    """Tests for tag management."""

    def test_add_tag(self) -> None:
        """Should add tag."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
        )

        situation.add_tag("formal")

        assert "formal" in situation.tags

    def test_has_tag(self) -> None:
        """Should check if tag exists."""
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Test",
            tags=["casual"],
        )

        assert situation.has_tag("casual") is True
        assert situation.has_tag("formal") is False


class TestModalityQueries:
    """Tests for modality query methods."""

    def test_is_in_person(self) -> None:
        """Should detect in-person situation."""
        situation = Situation(modality=Modality.IN_PERSON, description="Test")
        assert situation.is_in_person() is True

        situation2 = Situation(modality=Modality.VIDEO_CALL, description="Test")
        assert situation2.is_in_person() is False

    def test_is_remote(self) -> None:
        """Should detect remote situations."""
        for modality in [Modality.VIDEO_CALL, Modality.PHONE_CALL, Modality.TEXT_MESSAGE, Modality.EMAIL]:
            situation = Situation(modality=modality, description="Test")
            assert situation.is_remote() is True

        situation = Situation(modality=Modality.IN_PERSON, description="Test")
        assert situation.is_remote() is False

    def test_is_synchronous(self) -> None:
        """Should detect synchronous modalities."""
        for modality in [Modality.IN_PERSON, Modality.VIDEO_CALL, Modality.PHONE_CALL]:
            situation = Situation(modality=modality, description="Test")
            assert situation.is_synchronous() is True

        for modality in [Modality.TEXT_MESSAGE, Modality.EMAIL]:
            situation = Situation(modality=modality, description="Test")
            assert situation.is_synchronous() is False

    def test_is_asynchronous(self) -> None:
        """Should detect asynchronous modalities."""
        for modality in [Modality.TEXT_MESSAGE, Modality.EMAIL]:
            situation = Situation(modality=modality, description="Test")
            assert situation.is_asynchronous() is True

    def test_get_modality_traits(self) -> None:
        """Should return modality traits."""
        situation = Situation(modality=Modality.IN_PERSON, description="Test")
        traits = situation.get_modality_traits()

        assert traits["visual_cues"] is True
        assert traits["physical_presence"] is True
        assert traits["real_time"] is True


class TestSituationSerialization:
    """Tests for situation serialization."""

    def test_to_dict(self) -> None:
        """Should serialize to dictionary."""
        now = datetime.now()
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Team meeting",
            time=now,
            location="Office",
            context={"atmosphere": "focused"},
            participants=["alice"],
            tags=["work"],
        )

        data = situation.to_dict()

        assert data["modality"] == "in_person"
        assert data["description"] == "Team meeting"
        assert data["time"] == now.isoformat()
        assert data["location"] == "Office"
        assert data["context"]["atmosphere"] == "focused"
        assert "alice" in data["participants"]
        assert "work" in data["tags"]

    def test_from_dict(self) -> None:
        """Should deserialize from dictionary."""
        now = datetime.now()
        data = {
            "id": "sit_123",
            "modality": "in_person",
            "description": "Coffee chat",
            "time": now.isoformat(),
            "location": "Cafe",
            "context": {"atmosphere": "relaxed"},
            "participants": ["alice", "bob"],
            "tags": ["casual"],
        }

        situation = Situation.from_dict(data)

        assert situation.id == "sit_123"
        assert situation.modality == Modality.IN_PERSON
        assert situation.description == "Coffee chat"
        assert situation.location == "Cafe"

    def test_str(self) -> None:
        """Should have readable string representation."""
        now = datetime(2024, 6, 15, 14, 30)
        situation = Situation(
            modality=Modality.IN_PERSON,
            description="Team meeting",
            time=now,
            location="Office",
        )

        s = str(situation)

        assert "in_person" in s
        assert "Team meeting" in s
        assert "Office" in s
        assert "2024-06-15" in s


class TestCreateSituation:
    """Tests for create_situation factory."""

    def test_create_with_modality_enum(self) -> None:
        """Should create with Modality enum."""
        situation = create_situation(
            modality=Modality.IN_PERSON,
            description="Test meeting",
        )

        assert situation.modality == Modality.IN_PERSON

    def test_create_with_modality_string(self) -> None:
        """Should create with modality string."""
        situation = create_situation(
            modality="video_call",
            description="Remote meeting",
        )

        assert situation.modality == Modality.VIDEO_CALL

    def test_create_with_all_parameters(self) -> None:
        """Should create with all parameters."""
        now = datetime.now()
        situation = create_situation(
            modality=Modality.IN_PERSON,
            description="Full test",
            time=now,
            location="Here",
            context={"key": "value"},
            participants=["alice"],
            tags=["test"],
        )

        assert situation.time == now
        assert situation.location == "Here"
        assert situation.context["key"] == "value"
        assert "alice" in situation.participants
        assert "test" in situation.tags

    def test_create_with_defaults(self) -> None:
        """Should create with sensible defaults."""
        situation = create_situation(
            modality=Modality.IN_PERSON,
            description="Minimal",
        )

        assert situation.time is None
        assert situation.location is None
        assert situation.context == {}
        assert situation.participants == []
        assert situation.tags == []
