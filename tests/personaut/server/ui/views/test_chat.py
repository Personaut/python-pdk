"""Tests for the chat view routes."""

from __future__ import annotations

import json
from unittest.mock import patch


class TestChatSelectSession:
    """Tests for GET /chat/."""

    def test_select_returns_200(self, client) -> None:
        resp = client.get("/chat/")
        assert resp.status_code == 200

    def test_select_shows_sessions(self, client) -> None:
        resp = client.get("/chat/")
        html = resp.data.decode()
        # Should list available sessions
        assert "sess_test_001" in html or "session" in html.lower()


class TestChatNewSession:
    """Tests for GET/POST /chat/new."""

    def test_new_get_returns_200(self, client) -> None:
        resp = client.get("/chat/new")
        assert resp.status_code == 200

    def test_new_shows_individuals_and_situations(self, client) -> None:
        resp = client.get("/chat/new")
        html = resp.data.decode()
        assert "Sarah Chen" in html
        # Should list situations too
        assert "coffee shop" in html.lower() or "sit_test_001" in html

    def test_new_post_creates_session_and_redirects(self, client) -> None:
        resp = client.post(
            "/chat/new",
            data={
                "individual": "ind_test_001",
                "situation": "sit_test_001",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/chat/" in resp.headers.get("Location", "")

    def test_new_post_with_speaker_profile(self, client) -> None:
        """Should save custom speaker profile."""
        resp = client.post(
            "/chat/new",
            data={
                "individual": "ind_test_001",
                "situation": "sit_test_001",
                "new_speaker_title": "Boss",
                "new_speaker_context": "You are their direct supervisor",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_new_post_missing_fields_redirects_to_select(self, client) -> None:
        """Missing individual/situation should redirect back."""
        resp = client.post("/chat/new", data={}, follow_redirects=False)
        assert resp.status_code == 302
        loc = resp.headers.get("Location", "")
        assert "/chat" in loc


class TestChatSessionView:
    """Tests for GET /chat/<id>."""

    def test_session_view_returns_200(self, client) -> None:
        resp = client.get("/chat/sess_test_001")
        assert resp.status_code == 200

    def test_session_shows_individual_name(self, client) -> None:
        resp = client.get("/chat/sess_test_001")
        html = resp.data.decode()
        assert "Sarah Chen" in html

    def test_session_shows_messages(self, client) -> None:
        resp = client.get("/chat/sess_test_001")
        html = resp.data.decode()
        assert "Hello there!" in html


class TestChatSendMessage:
    """Tests for POST /chat/<session_id>/send."""

    def test_send_empty_returns_400(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/send",
            json={"content": ""},
        )
        assert resp.status_code == 400

    def test_send_message_returns_reply(self, client, mock_router) -> None:
        """Should generate a reply (fallback since no LLM is configured)."""
        # Patch the engine's get_llm to return None (fallback mode)
        with patch("personaut.server.ui.views.chat_engine.get_llm", return_value=None):
            # Also patch analyze_emotions to avoid side effects
            with patch(
                "personaut.server.ui.views.chat_engine.analyze_emotions",
                return_value={},
            ):
                resp = client.post(
                    "/chat/sess_test_001/send",
                    json={"content": "Hey, how is it going?"},
                )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reply" in data
        assert "reply_sender" in data
        assert data["reply_sender"] == "Sarah Chen"
        assert len(data["reply"]) > 0

    def test_send_message_includes_radar(self, client, mock_router) -> None:
        """Response should include updated emotion radar data."""
        with (
            patch("personaut.server.ui.views.chat_engine.get_llm", return_value=None),
            patch(
                "personaut.server.ui.views.chat_engine.analyze_emotions",
                return_value={},
            ),
        ):
            resp = client.post(
                "/chat/sess_test_001/send",
                json={"content": "What do you recommend?"},
            )
        data = resp.get_json()
        assert "radar" in data
        assert "categories" in data["radar"]
        assert "values" in data["radar"]


class TestChatGetMessages:
    """Tests for GET /chat/<id>/messages."""

    def test_get_messages(self, client) -> None:
        resp = client.get("/chat/sess_test_001/messages")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "messages" in data


class TestChatMemoryRoutes:
    """Tests for memory management proxy routes."""

    def test_add_memory(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/memories/add",
            json={"description": "A new memory", "salience": 0.5},
        )
        assert resp.status_code == 200

    def test_remove_memory(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/memories/mem_test_001/delete",
        )
        assert resp.status_code == 200

    def test_search_memories(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/memories/search",
            json={"query": "coffee"},
        )
        assert resp.status_code == 200


class TestChatMaskRoutes:
    """Tests for mask management proxy routes."""

    def test_add_mask(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/masks/add",
            json={"name": "New Mask", "description": "test"},
        )
        assert resp.status_code == 200

    def test_remove_mask(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/masks/mask_test_001/delete",
        )
        assert resp.status_code == 200


class TestChatTriggerRoutes:
    """Tests for trigger management proxy routes."""

    def test_add_trigger(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/triggers/add",
            json={"description": "New trigger", "trigger_type": "emotional"},
        )
        assert resp.status_code == 200

    def test_toggle_trigger(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/triggers/trig_test_001/toggle",
        )
        assert resp.status_code == 200

    def test_remove_trigger(self, client) -> None:
        resp = client.post(
            "/chat/sess_test_001/triggers/trig_test_001/delete",
        )
        assert resp.status_code == 200
