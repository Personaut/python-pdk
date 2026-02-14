"""Integration tests for FastAPI API routes.

Uses a monkeypatched get_app_state to return a fresh AppState per test,
avoiding the module-level _app_state lifecycle issue.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from personaut.server.api.app import AppState


@pytest.fixture
async def client():
    """Async HTTP client with routes and a fresh in-memory AppState."""
    state = AppState()

    # Patch get_app_state so every route handler gets our fresh state
    with (
        patch("personaut.server.api.app.get_app_state", return_value=state),
        patch("personaut.server.api.routes.individuals.get_app_state", return_value=state),
        patch("personaut.server.api.routes.situations.get_app_state", return_value=state),
        patch("personaut.server.api.routes.relationships.get_app_state", return_value=state),
        patch("personaut.server.api.routes.sessions.get_app_state", return_value=state),
        patch("personaut.server.api.routes.emotions.get_app_state", return_value=state),
        patch("personaut.server.api.routes.memories.get_app_state", return_value=state),
        patch("personaut.server.api.routes.masks.get_app_state", return_value=state),
        patch("personaut.server.api.routes.triggers.get_app_state", return_value=state),
    ):
        app = FastAPI()

        from personaut.server.api.routes import (
            emotions,
            individuals,
            masks,
            memories,
            relationships,
            sessions,
            situations,
            triggers,
        )

        app.include_router(individuals.router, prefix="/api/individuals")
        app.include_router(situations.router, prefix="/api/situations")
        app.include_router(relationships.router, prefix="/api/relationships")
        app.include_router(sessions.router, prefix="/api/sessions")
        app.include_router(emotions.router)
        app.include_router(memories.router)
        app.include_router(masks.router)
        app.include_router(triggers.router)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


# ── Individuals ─────────────────────────────────────────────────────


class TestIndividualRoutes:
    @pytest.mark.asyncio
    async def test_list_empty(self, client) -> None:
        resp = await client.get("/api/individuals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_individual(self, client) -> None:
        resp = await client.post(
            "/api/individuals",
            json={
                "name": "Sarah",
                "description": "A test individual",
                "individual_type": "npc",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Sarah"
        assert data["id"].startswith("ind_")

    @pytest.mark.asyncio
    async def test_get_individual(self, client) -> None:
        resp = await client.post("/api/individuals", json={"name": "Mike"})
        ind_id = resp.json()["id"]
        resp = await client.get(f"/api/individuals/{ind_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Mike"

    @pytest.mark.asyncio
    async def test_get_individual_not_found(self, client) -> None:
        resp = await client.get("/api/individuals/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_individual(self, client) -> None:
        resp = await client.post("/api/individuals", json={"name": "Alex"})
        ind_id = resp.json()["id"]
        resp = await client.patch(
            f"/api/individuals/{ind_id}",
            json={
                "name": "Alexander",
                "description": "Updated",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Alexander"

    @pytest.mark.asyncio
    async def test_update_not_found(self, client) -> None:
        resp = await client.patch("/api/individuals/nonexistent", json={"name": "X"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_individual(self, client) -> None:
        resp = await client.post("/api/individuals", json={"name": "Del"})
        ind_id = resp.json()["id"]
        resp = await client.delete(f"/api/individuals/{ind_id}")
        assert resp.status_code == 204
        resp = await client.get(f"/api/individuals/{ind_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client) -> None:
        resp = await client.delete("/api/individuals/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_pagination(self, client) -> None:
        for name in ["A", "B", "C"]:
            await client.post("/api/individuals", json={"name": name})
        resp = await client.get("/api/individuals?page=1&page_size=2")
        data = resp.json()
        assert data["total"] == 3
        assert len(data["individuals"]) == 2

    @pytest.mark.asyncio
    async def test_portrait_no_features(self, client) -> None:
        resp = await client.post("/api/individuals", json={"name": "NoFeat"})
        ind_id = resp.json()["id"]
        resp = await client.post(f"/api/individuals/{ind_id}/portrait")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_portrait_not_found(self, client) -> None:
        resp = await client.post("/api/individuals/nonexistent/portrait")
        assert resp.status_code == 404


# ── Situations ──────────────────────────────────────────────────────


class TestSituationRoutes:
    @pytest.mark.asyncio
    async def test_list_empty(self, client) -> None:
        resp = await client.get("/api/situations")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_create_situation(self, client) -> None:
        resp = await client.post(
            "/api/situations",
            json={
                "description": "Coffee shop",
                "modality": "in_person",
                "location": "Starbucks",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["id"].startswith("sit_")

    @pytest.mark.asyncio
    async def test_get_situation(self, client) -> None:
        resp = await client.post("/api/situations", json={"description": "Test"})
        sit_id = resp.json()["id"]
        resp = await client.get(f"/api/situations/{sit_id}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_not_found(self, client) -> None:
        resp = await client.get("/api/situations/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_situation(self, client) -> None:
        resp = await client.post("/api/situations", json={"description": "Del"})
        sit_id = resp.json()["id"]
        resp = await client.delete(f"/api/situations/{sit_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client) -> None:
        resp = await client.delete("/api/situations/nonexistent")
        assert resp.status_code == 404


# ── Relationships ───────────────────────────────────────────────────


class TestRelationshipRoutes:
    async def _two_ind(self, client):
        r1 = await client.post("/api/individuals", json={"name": "Alice"})
        r2 = await client.post("/api/individuals", json={"name": "Bob"})
        return r1.json()["id"], r2.json()["id"]

    @pytest.mark.asyncio
    async def test_list_empty(self, client) -> None:
        resp = await client.get("/api/relationships")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_create_relationship(self, client) -> None:
        a, b = await self._two_ind(client)
        resp = await client.post(
            "/api/relationships",
            json={
                "individual_ids": [a, b],
                "relationship_type": "friend",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["relationship_type"] == "friend"

    @pytest.mark.asyncio
    async def test_get_relationship(self, client) -> None:
        a, b = await self._two_ind(client)
        resp = await client.post(
            "/api/relationships",
            json={
                "individual_ids": [a, b],
            },
        )
        rel_id = resp.json()["id"]
        resp = await client.get(f"/api/relationships/{rel_id}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_not_found(self, client) -> None:
        resp = await client.get("/api/relationships/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_relationship(self, client) -> None:
        a, b = await self._two_ind(client)
        resp = await client.post(
            "/api/relationships",
            json={
                "individual_ids": [a, b],
            },
        )
        rel_id = resp.json()["id"]
        resp = await client.delete(f"/api/relationships/{rel_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client) -> None:
        resp = await client.delete("/api/relationships/nonexistent")
        assert resp.status_code == 404


# ── Sessions ────────────────────────────────────────────────────────


class TestSessionRoutes:
    async def _setup(self, client):
        r1 = await client.post("/api/individuals", json={"name": "Ind"})
        ind_id = r1.json()["id"]
        r2 = await client.post("/api/situations", json={"description": "Sit"})
        sit_id = r2.json()["id"]
        return ind_id, sit_id

    @pytest.mark.asyncio
    async def test_list_empty(self, client) -> None:
        resp = await client.get("/api/sessions")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_create_session(self, client) -> None:
        ind_id, sit_id = await self._setup(client)
        resp = await client.post(
            "/api/sessions",
            json={
                "situation_id": sit_id,
                "individual_ids": [ind_id],
            },
        )
        assert resp.status_code == 201
        assert resp.json()["id"].startswith("sess_")

    @pytest.mark.asyncio
    async def test_create_session_missing_situation(self, client) -> None:
        resp = await client.post(
            "/api/sessions",
            json={
                "situation_id": "nope",
                "individual_ids": ["nope"],
            },
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session(self, client) -> None:
        ind_id, sit_id = await self._setup(client)
        resp = await client.post(
            "/api/sessions",
            json={
                "situation_id": sit_id,
                "individual_ids": [ind_id],
            },
        )
        sess_id = resp.json()["id"]
        resp = await client.get(f"/api/sessions/{sess_id}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_not_found(self, client) -> None:
        resp = await client.get("/api/sessions/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_session(self, client) -> None:
        ind_id, sit_id = await self._setup(client)
        resp = await client.post(
            "/api/sessions",
            json={
                "situation_id": sit_id,
                "individual_ids": [ind_id],
            },
        )
        sess_id = resp.json()["id"]
        resp = await client.delete(f"/api/sessions/{sess_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client) -> None:
        resp = await client.delete("/api/sessions/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_end_session(self, client) -> None:
        """DELETE marks a session as ended (end_session handler returns 204)."""
        ind_id, sit_id = await self._setup(client)
        resp = await client.post(
            "/api/sessions",
            json={
                "situation_id": sit_id,
                "individual_ids": [ind_id],
            },
        )
        sess_id = resp.json()["id"]
        resp = await client.delete(f"/api/sessions/{sess_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, client) -> None:
        ind_id, sit_id = await self._setup(client)
        resp = await client.post(
            "/api/sessions",
            json={
                "situation_id": sit_id,
                "individual_ids": [ind_id],
            },
        )
        sess_id = resp.json()["id"]
        resp = await client.get(f"/api/sessions/{sess_id}/messages")
        assert resp.status_code == 200
        assert resp.json()["messages"] == []

    @pytest.mark.asyncio
    async def test_get_messages_not_found(self, client) -> None:
        resp = await client.get("/api/sessions/nonexistent/messages")
        assert resp.status_code == 404


# ── Emotions ────────────────────────────────────────────────────────


class TestEmotionRoutes:
    async def _create_ind(self, client, emotions=None):
        resp = await client.post("/api/individuals", json={"name": "Emo"})
        ind_id = resp.json()["id"]
        if emotions:
            await client.patch(
                f"/api/individuals/{ind_id}/emotions",
                json={"emotions": emotions},
            )
        return ind_id

    @pytest.mark.asyncio
    async def test_get_emotions(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.get(f"/api/individuals/{ind_id}/emotions")
        assert resp.status_code == 200
        assert "emotions" in resp.json()

    @pytest.mark.asyncio
    async def test_get_emotions_not_found(self, client) -> None:
        resp = await client.get("/api/individuals/nonexistent/emotions")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_emotions(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.patch(
            f"/api/individuals/{ind_id}/emotions",
            json={"emotions": {"joy": 0.8, "sadness": 0.2}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["emotions"]["joy"] == 0.8

    @pytest.mark.asyncio
    async def test_update_emotions_with_fill(self, client) -> None:
        ind_id = await self._create_ind(client, {"joy": 0.5, "anger": 0.5})
        resp = await client.patch(
            f"/api/individuals/{ind_id}/emotions",
            json={"emotions": {"joy": 0.9}, "fill": 0.1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["emotions"]["joy"] == 0.9
        assert data["emotions"]["anger"] == 0.1

    @pytest.mark.asyncio
    async def test_update_emotions_not_found(self, client) -> None:
        resp = await client.patch(
            "/api/individuals/nonexistent/emotions",
            json={"emotions": {"joy": 0.5}},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_reset_emotions(self, client) -> None:
        ind_id = await self._create_ind(client, {"joy": 0.8, "anger": 0.6})
        resp = await client.post(f"/api/individuals/{ind_id}/emotions/reset?value=0.0")
        assert resp.status_code == 200
        data = resp.json()
        for v in data["emotions"].values():
            assert v == 0.0

    @pytest.mark.asyncio
    async def test_reset_emotions_not_found(self, client) -> None:
        resp = await client.post("/api/individuals/nonexistent/emotions/reset?value=0.0")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_emotion_history(self, client) -> None:
        ind_id = await self._create_ind(client)
        # Create history by updating emotions
        await client.patch(
            f"/api/individuals/{ind_id}/emotions",
            json={"emotions": {"joy": 0.5}},
        )
        resp = await client.get(f"/api/individuals/{ind_id}/emotions/history?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["individual_id"] == ind_id

    @pytest.mark.asyncio
    async def test_emotion_history_not_found(self, client) -> None:
        resp = await client.get("/api/individuals/nonexistent/emotions/history")
        assert resp.status_code == 404


# ── Masks ───────────────────────────────────────────────────────────


class TestMaskRoutes:
    async def _create_ind(self, client):
        resp = await client.post("/api/individuals", json={"name": "Masked"})
        return resp.json()["id"]

    @pytest.mark.asyncio
    async def test_list_masks_empty(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.get(f"/api/individuals/{ind_id}/masks")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_list_masks_not_found(self, client) -> None:
        resp = await client.get("/api/individuals/nonexistent/masks")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_mask(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/masks",
            json={
                "name": "Professional",
                "description": "Work mask",
                "emotional_modifications": {"joy": 0.2},
                "trigger_situations": ["meeting"],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Professional"
        assert data["id"].startswith("mask_")

    @pytest.mark.asyncio
    async def test_create_mask_not_found(self, client) -> None:
        resp = await client.post(
            "/api/individuals/nonexistent/masks",
            json={
                "name": "X",
            },
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_mask(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/masks",
            json={
                "name": "Formal",
            },
        )
        mask_id = resp.json()["id"]
        resp = await client.get(f"/api/individuals/{ind_id}/masks/{mask_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Formal"

    @pytest.mark.asyncio
    async def test_get_mask_not_found(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.get(f"/api/individuals/{ind_id}/masks/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_mask(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/masks",
            json={
                "name": "ToDelete",
            },
        )
        mask_id = resp.json()["id"]
        resp = await client.delete(f"/api/individuals/{ind_id}/masks/{mask_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_mask_not_found(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.delete(f"/api/individuals/{ind_id}/masks/nonexistent")
        assert resp.status_code == 404


# ── Memories ────────────────────────────────────────────────────────


class TestMemoryRoutes:
    async def _create_ind(self, client):
        resp = await client.post("/api/individuals", json={"name": "MemInd"})
        return resp.json()["id"]

    @pytest.mark.asyncio
    async def test_list_memories_empty(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.get(f"/api/individuals/{ind_id}/memories")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_list_memories_not_found(self, client) -> None:
        resp = await client.get("/api/individuals/nonexistent/memories")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_memory(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/memories",
            json={
                "description": "First day at school",
                "salience": 0.8,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "First day at school"
        assert data["id"].startswith("mem_")

    @pytest.mark.asyncio
    async def test_create_memory_not_found(self, client) -> None:
        resp = await client.post(
            "/api/individuals/nonexistent/memories",
            json={
                "description": "Whatever",
            },
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_memory(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/memories",
            json={
                "description": "Graduation day",
            },
        )
        mem_id = resp.json()["id"]
        resp = await client.get(f"/api/individuals/{ind_id}/memories/{mem_id}")
        assert resp.status_code == 200
        assert resp.json()["description"] == "Graduation day"

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.get(f"/api/individuals/{ind_id}/memories/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_memory(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/memories",
            json={
                "description": "To delete",
            },
        )
        mem_id = resp.json()["id"]
        resp = await client.delete(f"/api/individuals/{ind_id}/memories/{mem_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.delete(f"/api/individuals/{ind_id}/memories/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_search_memories(self, client) -> None:
        ind_id = await self._create_ind(client)
        await client.post(
            f"/api/individuals/{ind_id}/memories",
            json={
                "description": "Had coffee at the cafe",
            },
        )
        await client.post(
            f"/api/individuals/{ind_id}/memories",
            json={
                "description": "Walked to the park",
            },
        )
        resp = await client.post(
            f"/api/individuals/{ind_id}/memories/search",
            json={"query": "coffee"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert "coffee" in data["results"][0]["description"]

    @pytest.mark.asyncio
    async def test_search_memories_no_results(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/memories/search",
            json={"query": "nonexistent"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_search_memories_not_found(self, client) -> None:
        resp = await client.post(
            "/api/individuals/nonexistent/memories/search",
            json={"query": "test"},
        )
        assert resp.status_code == 404


# ── Triggers ────────────────────────────────────────────────────────


class TestTriggerRoutes:
    async def _create_ind(self, client):
        resp = await client.post("/api/individuals", json={"name": "TrigInd"})
        return resp.json()["id"]

    @pytest.mark.asyncio
    async def test_list_triggers_empty(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.get(f"/api/individuals/{ind_id}/triggers")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_list_triggers_not_found(self, client) -> None:
        resp = await client.get("/api/individuals/nonexistent/triggers")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_trigger(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/triggers",
            json={
                "description": "Joy spike trigger",
                "trigger_type": "emotional",
                "rules": [{"field": "joy", "threshold": 0.8, "operator": ">"}],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "Joy spike trigger"
        assert data["id"].startswith("trig_")

    @pytest.mark.asyncio
    async def test_create_trigger_not_found(self, client) -> None:
        resp = await client.post(
            "/api/individuals/nonexistent/triggers",
            json={
                "description": "X",
                "trigger_type": "emotional",
            },
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_trigger(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/triggers",
            json={
                "description": "Test trigger",
                "trigger_type": "emotional",
            },
        )
        trig_id = resp.json()["id"]
        resp = await client.get(f"/api/individuals/{ind_id}/triggers/{trig_id}")
        assert resp.status_code == 200
        assert resp.json()["description"] == "Test trigger"

    @pytest.mark.asyncio
    async def test_get_trigger_not_found(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.get(f"/api/individuals/{ind_id}/triggers/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_toggle_trigger(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/triggers",
            json={
                "description": "Toggle me",
                "trigger_type": "emotional",
            },
        )
        trig_id = resp.json()["id"]
        assert resp.json()["active"] is True
        resp = await client.patch(f"/api/individuals/{ind_id}/triggers/{trig_id}/toggle")
        assert resp.status_code == 200
        assert resp.json()["active"] is False
        # Toggle back
        resp = await client.patch(f"/api/individuals/{ind_id}/triggers/{trig_id}/toggle")
        assert resp.json()["active"] is True

    @pytest.mark.asyncio
    async def test_toggle_trigger_not_found(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.patch(f"/api/individuals/{ind_id}/triggers/nonexistent/toggle")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_trigger(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.post(
            f"/api/individuals/{ind_id}/triggers",
            json={
                "description": "To delete",
                "trigger_type": "situational",
            },
        )
        trig_id = resp.json()["id"]
        resp = await client.delete(f"/api/individuals/{ind_id}/triggers/{trig_id}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_trigger_not_found(self, client) -> None:
        ind_id = await self._create_ind(client)
        resp = await client.delete(f"/api/individuals/{ind_id}/triggers/nonexistent")
        assert resp.status_code == 404
