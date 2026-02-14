"""Shared fixtures for simulation tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from personaut.emotions.state import EmotionalState


@dataclass
class MockSituation:
    """Mock situation for testing."""

    description: str = "Test situation"
    location: str | None = None
    modality: str | None = None


@dataclass
class MockIndividual:
    """Mock individual for testing."""

    name: str
    emotional_state: EmotionalState = field(default_factory=EmotionalState)
    traits: dict[str, float] = field(default_factory=dict)
    is_human: bool = False
    individual_type: str = "ai"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "emotional_state": self.emotional_state.to_dict(),
            "traits": self.traits,
            "is_human": self.is_human,
        }


@pytest.fixture
def mock_situation() -> MockSituation:
    """Create a mock situation."""
    return MockSituation(
        description="Coffee shop conversation",
        location="Downtown Coffee House",
    )


@pytest.fixture
def mock_individual_sarah() -> MockIndividual:
    """Create Sarah mock individual."""
    state = EmotionalState()
    state.change_emotion("content", 0.7)
    state.change_emotion("trusting", 0.6)
    return MockIndividual(
        name="Sarah",
        emotional_state=state,
        traits={"warmth": 0.8, "openness": 0.7},
        is_human=False,
    )


@pytest.fixture
def mock_individual_mike() -> MockIndividual:
    """Create Mike mock individual."""
    state = EmotionalState()
    state.change_emotion("hopeful", 0.8)  # Changed from 'curious'
    state.change_emotion("trusting", 0.6)  # Changed from 'friendly'
    return MockIndividual(
        name="Mike",
        emotional_state=state,
        traits={"extraversion": 0.7, "agreeableness": 0.6},
        is_human=True,
        individual_type="human",
    )


@pytest.fixture
def mock_individual_anxious() -> MockIndividual:
    """Create an anxious mock individual."""
    state = EmotionalState()
    state.change_emotion("anxious", 0.8)
    state.change_emotion("insecure", 0.6)
    return MockIndividual(
        name="Alex",
        emotional_state=state,
        traits={"neuroticism": 0.7},
        is_human=False,
    )
