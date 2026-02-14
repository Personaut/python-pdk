"""Test configuration and shared fixtures for Personaut PDK."""

from __future__ import annotations

import pytest


# =============================================================================
# Core Fixtures
# =============================================================================


@pytest.fixture
def sample_emotional_state_data() -> dict[str, float]:
    """Sample emotional state data for testing.

    Returns:
        Dictionary mapping emotion names to values.
    """
    return {
        "anxious": 0.6,
        "hopeful": 0.4,
        "friendly": 0.7,
        "curious": 0.5,
    }


@pytest.fixture
def sample_trait_data() -> list[dict[str, float | str]]:
    """Sample trait data for testing.

    Returns:
        List of trait dictionaries with name and value.
    """
    return [
        {"name": "warmth", "value": 0.8},
        {"name": "dominance", "value": 0.4},
        {"name": "emotional_stability", "value": 0.6},
    ]


# =============================================================================
# Marker Configuration
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
