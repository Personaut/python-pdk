"""Integration tests: FastAPI backend ↔ Flask UI views.

These tests spin up the real FastAPI ``create_app()`` using httpx's
``ASGITransport`` (no network, in-process) and verify the full CRUD
lifecycle through the actual API routes.

The FastAPI app is configured with in-memory storage (no SQLite) so
tests are fast, isolated, and repeatable.
"""

from __future__ import annotations

import sys

import httpx
import pytest
import pytest_asyncio  # noqa: F401 – ensures the plugin is available
from httpx import ASGITransport


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _force_memory_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the FastAPI app uses in-memory storage, not SQLite."""
    monkeypatch.setenv("PERSONAUT_STORAGE_TYPE", "memory")


@pytest.fixture()
def fastapi_app():
    """Create a fresh FastAPI application with initialized state.

    The ASGITransport does not trigger the lifespan context manager, so
    we manually initialise the global ``_app_state`` that the route
    handlers depend on.  We access the module via ``sys.modules`` to
    guarantee we write to the exact same dict that ``get_app_state()``
    reads from.
    """
    from personaut.server.api.app import AppState, create_app

    # Get the real module object (same __dict__ as get_app_state.__globals__)
    app_mod = sys.modules["personaut.server.api.app"]

    # Initialise global state (mirrors what lifespan() does)
    state = AppState()
    app_mod.__dict__["_app_state"] = state

    fastapi = create_app(debug=True)

    yield fastapi

    # Cleanup: reset the global state so tests are isolated
    app_mod.__dict__["_app_state"] = None


@pytest.fixture()
def client(fastapi_app) -> httpx.AsyncClient:
    """Provide an async httpx client that talks to the real FastAPI app."""
    transport = ASGITransport(app=fastapi_app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


# ═══════════════════════════════════════════════════════════════════════════
# Health check
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


# ═══════════════════════════════════════════════════════════════════════════
# Individuals CRUD
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_individual(client: httpx.AsyncClient) -> None:
    payload = {"name": "Alice", "description": "Test individual"}
    resp = await client.post("/api/individuals", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alice"
    assert data["id"].startswith("ind_")


@pytest.mark.asyncio
async def test_list_individuals_empty(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/individuals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["individuals"] == []


@pytest.mark.asyncio
async def test_individual_lifecycle(client: httpx.AsyncClient) -> None:
    """Full CRUD: create → read → update → list → delete → verify gone."""
    # Create
    create_resp = await client.post(
        "/api/individuals",
        json={
            "name": "Bob",
            "description": "A friendly barista",
            "initial_emotions": {"cheerful": 0.7, "content": 0.5},
            "initial_traits": {"warmth": 0.8, "openness": 0.6},
        },
    )
    assert create_resp.status_code == 201
    ind = create_resp.json()
    ind_id = ind["id"]
    assert ind["name"] == "Bob"
    assert ind["emotional_state"]["cheerful"] == 0.7

    # Read
    get_resp = await client.get(f"/api/individuals/{ind_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Bob"

    # Update
    patch_resp = await client.patch(
        f"/api/individuals/{ind_id}",
        json={"name": "Robert", "description": "A senior barista"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Robert"
    assert patch_resp.json()["description"] == "A senior barista"

    # List
    list_resp = await client.get("/api/individuals")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # Delete
    del_resp = await client.delete(f"/api/individuals/{ind_id}")
    assert del_resp.status_code == 204

    # Verify gone
    gone_resp = await client.get(f"/api/individuals/{ind_id}")
    assert gone_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_individual(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/individuals/ind_doesnotexist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_individual_with_metadata(client: httpx.AsyncClient) -> None:
    payload = {
        "name": "Charlie",
        "metadata": {"occupation": "teacher", "interests": "reading"},
    }
    resp = await client.post("/api/individuals", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["metadata"]["occupation"] == "teacher"


# ═══════════════════════════════════════════════════════════════════════════
# Situations CRUD
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_situation(client: httpx.AsyncClient) -> None:
    payload = {
        "description": "A quiet coffee shop on a rainy afternoon",
        "modality": "in_person",
        "location": "Brew & Bean Café",
    }
    resp = await client.post("/api/situations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "A quiet coffee shop on a rainy afternoon"
    assert data["id"].startswith("sit_")


@pytest.mark.asyncio
async def test_situation_lifecycle(client: httpx.AsyncClient) -> None:
    """Full CRUD: create → read → update → list → delete → verify gone."""
    # Create
    create_resp = await client.post(
        "/api/situations",
        json={
            "description": "Office meeting room",
            "modality": "in_person",
            "location": "Conference Room B",
        },
    )
    assert create_resp.status_code == 201
    sit = create_resp.json()
    sit_id = sit["id"]

    # Read
    get_resp = await client.get(f"/api/situations/{sit_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["location"] == "Conference Room B"

    # Update
    patch_resp = await client.patch(
        f"/api/situations/{sit_id}",
        json={"description": "Updated: Executive meeting room"},
    )
    assert patch_resp.status_code == 200
    assert "Executive" in patch_resp.json()["description"]

    # List
    list_resp = await client.get("/api/situations")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # Delete
    del_resp = await client.delete(f"/api/situations/{sit_id}")
    assert del_resp.status_code == 204

    # Verify gone
    gone_resp = await client.get(f"/api/situations/{sit_id}")
    assert gone_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_situation(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/situations/sit_doesnotexist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_situation_modality(client: httpx.AsyncClient) -> None:
    """Test modality operations."""
    # Create a situation first
    create_resp = await client.post(
        "/api/situations",
        json={
            "description": "Phone call with client",
            "modality": "phone_call",
        },
    )
    sit_id = create_resp.json()["id"]

    # Get modality config
    mod_resp = await client.get(f"/api/situations/{sit_id}/modality")
    assert mod_resp.status_code == 200
    config = mod_resp.json()
    assert config["modality"] == "phone_call"
    assert config["has_audio_cues"] is True
    assert config["has_visual_cues"] is False


# ═══════════════════════════════════════════════════════════════════════════
# Cross-entity: create individuals + situations together
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_multiple_entities(client: httpx.AsyncClient) -> None:
    """Create multiple individuals and situations, verify counts."""
    for i in range(3):
        resp = await client.post(
            "/api/individuals",
            json={"name": f"Person {i}"},
        )
        assert resp.status_code == 201

    for i in range(2):
        resp = await client.post(
            "/api/situations",
            json={"description": f"Situation {i}"},
        )
        assert resp.status_code == 201

    ind_resp = await client.get("/api/individuals")
    assert ind_resp.json()["total"] == 3

    sit_resp = await client.get("/api/situations")
    assert sit_resp.json()["total"] == 2


@pytest.mark.asyncio
async def test_individual_with_emotions_and_traits(client: httpx.AsyncClient) -> None:
    """Verify that emotional state and trait profile are stored correctly."""
    emotions = {"cheerful": 0.8, "anxious": 0.2, "content": 0.6}
    traits = {"warmth": 0.9, "openness": 0.7, "conscientiousness": 0.5}
    resp = await client.post(
        "/api/individuals",
        json={
            "name": "Diana",
            "initial_emotions": emotions,
            "initial_traits": traits,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["emotional_state"]["cheerful"] == 0.8
    assert data["trait_profile"]["warmth"] == 0.9
