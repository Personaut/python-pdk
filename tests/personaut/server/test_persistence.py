"""Tests for Persistence layer — targeting 0% → ~90% coverage."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from personaut.server.api.persistence import Persistence


NOW = datetime.now()


@pytest.fixture
def db(tmp_path: Path) -> Persistence:
    """Create a Persistence instance with a temp database."""
    return Persistence(tmp_path / "test.db")


def _ind(id: str = "ind_1", name: str = "Sarah", **extra: Any) -> dict[str, Any]:
    """Create an individual dict with required fields."""
    d: dict[str, Any] = {"id": id, "name": name, "created_at": NOW}
    d.update(extra)
    return d


def _sit(id: str = "sit_1", desc: str = "Test situation", **extra: Any) -> dict[str, Any]:
    """Create a situation dict with required fields."""
    d: dict[str, Any] = {"id": id, "description": desc, "created_at": NOW}
    d.update(extra)
    return d


class TestHelpers:
    """Tests for datetime conversion helpers."""

    def test_dt_to_str_none(self) -> None:
        assert Persistence._dt_to_str(None) is None

    def test_dt_to_str_datetime(self) -> None:
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = Persistence._dt_to_str(dt)
        assert result is not None
        assert "2025-01-15" in result

    def test_dt_to_str_string(self) -> None:
        assert Persistence._dt_to_str("2025-01-15") == "2025-01-15"

    def test_str_to_dt_none(self) -> None:
        assert Persistence._str_to_dt(None) is None

    def test_str_to_dt_datetime_passthrough(self) -> None:
        dt = datetime(2025, 1, 15)
        assert Persistence._str_to_dt(dt) is dt

    def test_str_to_dt_valid_string(self) -> None:
        result = Persistence._str_to_dt("2025-01-15T10:30:00")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1

    def test_str_to_dt_invalid_string(self) -> None:
        assert Persistence._str_to_dt("not-a-date") is None


class TestIndividuals:
    """Tests for individual CRUD operations."""

    def test_save_individual(self, db: Persistence) -> None:
        result = db.save_individual(_ind())
        assert result == "ind_1"

    def test_save_individual_with_extras(self, db: Persistence) -> None:
        ind = _ind(
            id="ind_2",
            name="Mike",
            portrait_url="http://example.com/portrait.png",
            physical_features={"build": "athletic"},
        )
        db.save_individual(ind)
        loaded = db.load_individuals()
        assert len(loaded) == 1
        assert loaded[0]["portrait_url"] == "http://example.com/portrait.png"
        assert loaded[0]["physical_features"] == {"build": "athletic"}

    def test_load_individuals_empty(self, db: Persistence) -> None:
        assert db.load_individuals() == []

    def test_load_individuals_roundtrip(self, db: Persistence) -> None:
        ind = _ind(
            trait_profile={"warmth": 0.8},
            emotional_state={"proud": 0.5},
        )
        db.save_individual(ind)
        loaded = db.load_individuals()
        assert len(loaded) == 1
        assert loaded[0]["name"] == "Sarah"
        assert loaded[0]["id"] == "ind_1"

    def test_delete_individual(self, db: Persistence) -> None:
        db.save_individual(_ind())
        result = db.delete_individual("ind_1")
        assert result is True
        assert db.load_individuals() == []


class TestSituations:
    """Tests for situation CRUD operations."""

    def test_save_situation(self, db: Persistence) -> None:
        sit = _sit(
            modality="in_person",
            location="Starbucks",
            context={"time_of_day": "morning"},
        )
        result = db.save_situation(sit)
        assert result == "sit_1"

    def test_load_situations_roundtrip(self, db: Persistence) -> None:
        sit = _sit(modality="in_person", location="Starbucks")
        db.save_situation(sit)
        loaded = db.load_situations()
        assert len(loaded) == 1
        assert loaded[0]["description"] == "Test situation"
        assert loaded[0]["modality"] == "in_person"

    def test_load_situations_empty(self, db: Persistence) -> None:
        assert db.load_situations() == []

    def test_delete_situation(self, db: Persistence) -> None:
        db.save_situation(_sit())
        result = db.delete_situation("sit_1")
        assert result is True


class TestSessions:
    """Tests for session CRUD operations."""

    def _setup(self, db: Persistence) -> None:
        db.save_individual(_ind())
        db.save_situation(_sit())

    def test_save_session(self, db: Persistence) -> None:
        self._setup(db)
        sess = {
            "id": "sess_1",
            "situation_id": "sit_1",
            "individual_ids": ["ind_1"],
            "active": True,
            "created_at": NOW,
        }
        result = db.save_session(sess)
        assert result == "sess_1"

    def test_save_session_with_extras(self, db: Persistence) -> None:
        self._setup(db)
        sess = {
            "id": "sess_2",
            "situation_id": "sit_1",
            "individual_ids": ["ind_1"],
            "video_url": "http://example.com/video.mp4",
            "human_id": "human_1",
            "created_at": NOW,
        }
        db.save_session(sess)
        loaded = db.load_sessions()
        assert len(loaded) == 1
        assert loaded[0]["video_url"] == "http://example.com/video.mp4"
        assert loaded[0]["human_id"] == "human_1"

    def test_load_sessions_empty(self, db: Persistence) -> None:
        assert db.load_sessions() == []

    def test_load_sessions_roundtrip(self, db: Persistence) -> None:
        self._setup(db)
        sess = {
            "id": "sess_1",
            "situation_id": "sit_1",
            "individual_ids": ["ind_1"],
            "created_at": NOW,
        }
        db.save_session(sess)
        loaded = db.load_sessions()
        assert len(loaded) == 1
        assert loaded[0]["id"] == "sess_1"
        assert loaded[0]["individual_ids"] == ["ind_1"]

    def test_delete_session(self, db: Persistence) -> None:
        self._setup(db)
        db.save_session(
            {
                "id": "sess_1",
                "situation_id": "sit_1",
                "individual_ids": ["ind_1"],
                "created_at": NOW,
            }
        )
        db.delete_session("sess_1")
        loaded = db.load_sessions()
        assert all(not s.get("active") for s in loaded if s["id"] == "sess_1") or len(loaded) == 0


class TestMessages:
    """Tests for message persistence."""

    def _setup(self, db: Persistence) -> None:
        db.save_individual(_ind())
        db.save_situation(_sit())
        db.save_session(
            {
                "id": "sess_1",
                "situation_id": "sit_1",
                "individual_ids": ["ind_1"],
                "created_at": NOW,
            }
        )

    def test_save_message(self, db: Persistence) -> None:
        self._setup(db)
        msg = {
            "id": "msg_1",
            "sender_name": "Sarah",
            "content": "Hello!",
            "sender_id": "ind_1",
            "timestamp": NOW,
        }
        result = db.save_message("sess_1", msg)
        assert isinstance(result, str)

    def test_save_message_with_extras(self, db: Persistence) -> None:
        self._setup(db)
        msg = {
            "id": "msg_2",
            "sender_name": "Sarah",
            "content": "Hello!",
            "sender_id": "ind_1",
            "action": "waves",
            "emotional_state": {"proud": 0.8},
            "timestamp": NOW,
        }
        db.save_message("sess_1", msg)
        loaded = db.load_sessions()
        assert len(loaded) == 1
        assert len(loaded[0]["messages"]) == 1
        assert loaded[0]["messages"][0]["action"] == "waves"

    def test_messages_loaded_with_session(self, db: Persistence) -> None:
        self._setup(db)
        db.save_message(
            "sess_1",
            {
                "id": "msg_1",
                "sender_name": "Sarah",
                "content": "Hi!",
                "timestamp": NOW,
            },
        )
        db.save_message(
            "sess_1",
            {
                "id": "msg_2",
                "sender_name": "Mike",
                "content": "Hey!",
                "timestamp": NOW,
            },
        )
        loaded = db.load_sessions()
        assert len(loaded[0]["messages"]) == 2


class TestRelationships:
    """Tests for relationship CRUD operations."""

    def _setup(self, db: Persistence) -> None:
        db.save_individual(_ind(id="ind_1", name="Sarah"))
        db.save_individual(_ind(id="ind_2", name="Mike"))

    def test_save_relationship(self, db: Persistence) -> None:
        self._setup(db)
        rel = {
            "id": "rel_1",
            "individual_a": "ind_1",
            "individual_b": "ind_2",
            "relationship_type": "friend",
            "trust_levels": {"ind_1": 0.8, "ind_2": 0.7},
            "created_at": NOW,
        }
        result = db.save_relationship(rel)
        assert result == "rel_1"

    def test_load_relationships_roundtrip(self, db: Persistence) -> None:
        self._setup(db)
        rel = {
            "id": "rel_1",
            "individual_a": "ind_1",
            "individual_b": "ind_2",
            "relationship_type": "friend",
            "trust_levels": {"ind_1": 0.8},
            "created_at": NOW,
        }
        db.save_relationship(rel)
        loaded = db.load_relationships()
        assert len(loaded) == 1
        assert loaded[0]["id"] == "rel_1"
        assert loaded[0]["individual_ids"] == ["ind_1", "ind_2"]
        assert loaded[0]["relationship_type"] == "friend"

    def test_load_relationships_empty(self, db: Persistence) -> None:
        assert db.load_relationships() == []

    def test_delete_relationship(self, db: Persistence) -> None:
        self._setup(db)
        db.save_relationship(
            {
                "id": "rel_1",
                "individual_a": "ind_1",
                "individual_b": "ind_2",
                "created_at": NOW,
            }
        )
        result = db.delete_relationship("rel_1")
        assert result is True


class TestClose:
    """Tests for close method."""

    def test_close_db(self, db: Persistence) -> None:
        db.close()
