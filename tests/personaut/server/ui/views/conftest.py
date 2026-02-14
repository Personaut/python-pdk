"""Shared fixtures for Flask UI view tests.

Provides:
- ``app`` — a configured Flask application with a mock API backend
- ``client`` — a Flask test client that can make requests without a live server
- ``mock_router`` — canned API responses for the mock backend
- Pre-built response dicts for individuals, situations, sessions, etc.

Key implementation detail:
    Every view module does ``from ... import api_get as _api_get``, which
    creates a *local* function reference.  Patching the source module alone
    won't reach these locals.  We must patch each consuming module's copy.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# Sample data payloads (replicates the FastAPI JSON responses)
# ═══════════════════════════════════════════════════════════════════════════

SAMPLE_INDIVIDUAL = {
    "id": "ind_test_001",
    "name": "Sarah Chen",
    "description": "A friendly barista who loves coffee",
    "trait_profile": {
        "warmth": 0.85,
        "reasoning": 0.6,
        "emotional_stability": 0.7,
        "dominance": 0.4,
        "liveliness": 0.75,
        "rule_consciousness": 0.5,
        "social_boldness": 0.6,
        "sensitivity": 0.65,
        "vigilance": 0.35,
        "abstractedness": 0.5,
        "privateness": 0.3,
        "apprehension": 0.4,
        "openness_to_change": 0.7,
        "self_reliance": 0.55,
        "perfectionism": 0.45,
        "tension": 0.3,
    },
    "emotional_state": {
        "cheerful": 0.7,
        "content": 0.6,
        "hopeful": 0.4,
        "anxious": 0.1,
    },
    "metadata": {
        "occupation": "barista",
        "interests": "coffee, latte art, indie music",
        "speaking_style": "casual and warm",
    },
    "physical_features": {},
    "portrait_url": "",
}

SAMPLE_INDIVIDUAL_MINIMAL = {
    "id": "ind_test_002",
    "name": "Test Character",
    "trait_profile": {},
    "emotional_state": {},
    "metadata": {},
}

SAMPLE_SITUATION = {
    "id": "sit_test_001",
    "description": "A cozy coffee shop on a rainy morning",
    "modality": "in_person",
    "location": "Downtown Café",
    "context": {"time_of_day": "morning", "weather": "rainy"},
}

SAMPLE_SESSION = {
    "id": "sess_test_001",
    "individual_ids": ["ind_test_001"],
    "situation_id": "sit_test_001",
}

SAMPLE_MESSAGE = {
    "id": "msg_test_001",
    "content": "Hello there!",
    "sender_id": None,
    "session_id": "sess_test_001",
}

SAMPLE_MEMORY = {
    "id": "mem_test_001",
    "owner_id": "ind_test_001",
    "description": "Remembers making a perfect latte for a regular",
    "emotional_state": {"proud": 0.6, "cheerful": 0.5},
    "salience": 0.7,
    "metadata": {},
}

SAMPLE_MASK = {
    "id": "mask_test_001",
    "name": "Professional",
    "description": "A polished workplace persona",
    "trigger_situations": ["work", "office", "meeting"],
    "emotional_modifications": {"cheerful": -0.1, "content": 0.1},
}

SAMPLE_TRIGGER = {
    "id": "trig_test_001",
    "description": "Gets anxious when someone is rude",
    "trigger_type": "emotional",
    "active": True,
}


# ═══════════════════════════════════════════════════════════════════════════
# Mock API helper — routes API calls to pre-built responses
# ═══════════════════════════════════════════════════════════════════════════


class MockAPIRouter:
    """Routes ``api_get`` / ``api_post`` / etc. calls to canned responses.

    Acts as a thin in-process mock for the FastAPI backend.
    """

    def __init__(self) -> None:
        self.get_routes: dict[str, Any] = {}
        self.post_routes: dict[str, Any] = {}
        self.patch_routes: dict[str, Any] = {}
        self.delete_routes: set[str] = set()
        self.post_calls: list[tuple[str, Any]] = []
        self.patch_calls: list[tuple[str, Any]] = []

    def seed_defaults(self) -> None:
        """Populate with the standard sample data."""
        self.get_routes = {
            "/individuals": {
                "individuals": [SAMPLE_INDIVIDUAL, SAMPLE_INDIVIDUAL_MINIMAL],
                "total": 2,
            },
            "/individuals?page_size=100": {
                "individuals": [SAMPLE_INDIVIDUAL, SAMPLE_INDIVIDUAL_MINIMAL],
                "total": 2,
            },
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}": SAMPLE_INDIVIDUAL,
            f"/individuals/{SAMPLE_INDIVIDUAL_MINIMAL['id']}": SAMPLE_INDIVIDUAL_MINIMAL,
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/memories": {
                "memories": [SAMPLE_MEMORY],
            },
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/masks": {
                "masks": [SAMPLE_MASK],
            },
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/triggers": {
                "triggers": [SAMPLE_TRIGGER],
            },
            f"/individuals/{SAMPLE_INDIVIDUAL_MINIMAL['id']}/memories": {"memories": []},
            f"/individuals/{SAMPLE_INDIVIDUAL_MINIMAL['id']}/masks": {"masks": []},
            f"/individuals/{SAMPLE_INDIVIDUAL_MINIMAL['id']}/triggers": {"triggers": []},
            "/situations": {
                "situations": [SAMPLE_SITUATION],
                "total": 1,
            },
            "/situations?page_size=100": {
                "situations": [SAMPLE_SITUATION],
                "total": 1,
            },
            f"/situations/{SAMPLE_SITUATION['id']}": SAMPLE_SITUATION,
            "/sessions": {
                "sessions": [SAMPLE_SESSION],
                "total": 1,
            },
            f"/sessions/{SAMPLE_SESSION['id']}": SAMPLE_SESSION,
            f"/sessions/{SAMPLE_SESSION['id']}/messages": {
                "messages": [SAMPLE_MESSAGE],
            },
            "/relationships": {"total": 0, "relationships": []},
        }

        # Default POST responses
        self.post_routes = {
            "/sessions": SAMPLE_SESSION,
            f"/sessions/{SAMPLE_SESSION['id']}/messages": SAMPLE_MESSAGE,
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/memories": SAMPLE_MEMORY,
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/masks": SAMPLE_MASK,
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/triggers": SAMPLE_TRIGGER,
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/memories/search": {
                "query": "test",
                "results": [],
                "total": 0,
            },
        }

        self.patch_routes = {
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/triggers/{SAMPLE_TRIGGER['id']}/toggle": {
                "id": SAMPLE_TRIGGER["id"],
                "active": False,
            },
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/emotions": {"ok": True},
        }

        self.delete_routes = {
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/memories/{SAMPLE_MEMORY['id']}",
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/masks/{SAMPLE_MASK['id']}",
            f"/individuals/{SAMPLE_INDIVIDUAL['id']}/triggers/{SAMPLE_TRIGGER['id']}",
        }

    def api_get(self, path: str, *, timeout: int = 5) -> Any:
        return self.get_routes.get(path)

    def api_post(self, path: str, data: dict[str, Any], *, timeout: int = 5) -> Any:
        self.post_calls.append((path, data))
        return self.post_routes.get(path)

    def api_patch(self, path: str, data: dict[str, Any], *, timeout: int = 5) -> Any:
        self.patch_calls.append((path, data))
        return self.patch_routes.get(path, data)

    def api_delete(self, path: str, *, timeout: int = 5) -> bool:
        return path in self.delete_routes


# ═══════════════════════════════════════════════════════════════════════════
# Modules that import api_helpers functions as local names
# ═══════════════════════════════════════════════════════════════════════════

# Every view module that does ``from ... import api_get as _api_get``
# needs its local reference patched.
_MODULES_USING_API_GET = [
    "personaut.server.ui.views.dashboard",
    "personaut.server.ui.views.individuals",
    "personaut.server.ui.views.situations",
    "personaut.server.ui.views.chat",
    "personaut.server.ui.views.chat_engine",
    "personaut.server.ui.views.simulations",
]

_MODULES_USING_API_POST = [
    "personaut.server.ui.views.individuals",
    "personaut.server.ui.views.situations",
    "personaut.server.ui.views.chat",
]

_MODULES_USING_API_PATCH = [
    "personaut.server.ui.views.individuals",
    "personaut.server.ui.views.situations",
    "personaut.server.ui.views.chat",
]

_MODULES_USING_API_DELETE = [
    "personaut.server.ui.views.chat",
]


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def mock_router() -> MockAPIRouter:
    """A fresh MockAPIRouter seeded with default data."""
    router = MockAPIRouter()
    router.seed_defaults()
    return router


@pytest.fixture()
def app(mock_router: MockAPIRouter):
    """Create a Flask test application with mocked API backend.

    Patches *every* consumer module's local ``_api_get`` / ``_api_post`` /
    ``_api_patch`` / ``_api_delete`` so that no real HTTP calls are made.
    """
    from personaut.server.ui.app import create_ui_app

    flask_app = create_ui_app(api_base_url="http://mock:8000/api")
    flask_app.config["TESTING"] = True

    # Build the patch list — one patch for each (module, function) pair
    patches = []

    for mod in _MODULES_USING_API_GET:
        patches.append(patch(f"{mod}._api_get", side_effect=mock_router.api_get))

    for mod in _MODULES_USING_API_POST:
        patches.append(patch(f"{mod}._api_post", side_effect=mock_router.api_post))

    for mod in _MODULES_USING_API_PATCH:
        patches.append(patch(f"{mod}._api_patch", side_effect=mock_router.api_patch))

    for mod in _MODULES_USING_API_DELETE:
        patches.append(patch(f"{mod}._api_delete", side_effect=mock_router.api_delete))

    # Also patch the source module (for any code that calls it directly)
    patches.append(patch("personaut.server.ui.views.api_helpers.api_get", side_effect=mock_router.api_get))
    patches.append(patch("personaut.server.ui.views.api_helpers.api_post", side_effect=mock_router.api_post))
    patches.append(patch("personaut.server.ui.views.api_helpers.api_patch", side_effect=mock_router.api_patch))
    patches.append(patch("personaut.server.ui.views.api_helpers.api_delete", side_effect=mock_router.api_delete))

    # Start all patches
    for p in patches:
        p.start()

    yield flask_app

    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def sample_individual() -> dict:
    """Return a copy of the sample individual data."""
    return dict(SAMPLE_INDIVIDUAL)


@pytest.fixture()
def sample_situation() -> dict:
    """Return a copy of the sample situation data."""
    return dict(SAMPLE_SITUATION)


@pytest.fixture()
def sample_session() -> dict:
    """Return a copy of the sample session data."""
    return dict(SAMPLE_SESSION)
