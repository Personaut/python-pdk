"""Extended tests for LiveInteractionServer/Client — targeting uncovered branches."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from personaut.server.server import LiveInteractionClient, LiveInteractionServer


class TestServerExtended:
    """Additional tests for server uncovered methods."""

    def test_add_situation_with_override(self) -> None:
        """Should use id_override for situation."""
        server = LiveInteractionServer()

        @dataclass
        class Sit:
            id: str = "original"
            description: str = "test"

        result = server.add_situation(Sit(), id_override="custom_sit")
        assert result == "custom_sit"
        assert "custom_sit" in server.situations

    def test_add_situation_generates_id(self) -> None:
        """Should generate UUID-based ID when no ID available."""
        server = LiveInteractionServer()
        result = server.add_situation("just a string")
        assert result.startswith("sit_")

    def test_add_relationship_with_override(self) -> None:
        """Should use id_override for relationship."""
        server = LiveInteractionServer()

        @dataclass
        class Rel:
            id: str = "original"

        result = server.add_relationship(Rel(), id_override="custom_rel")
        assert result == "custom_rel"

    def test_add_relationship_generates_id(self) -> None:
        """Should generate UUID-based ID when no ID available."""
        server = LiveInteractionServer()
        result = server.add_relationship("just a string")
        assert result.startswith("rel_")

    def test_stop_with_api_server(self) -> None:
        """Stop should signal API server to exit."""
        server = LiveInteractionServer()
        server._running = True
        mock_api = MagicMock()
        server._api_server = mock_api
        server.stop()
        assert mock_api.should_exit is True
        assert server._api_server is None

    def test_stop_with_api_thread(self) -> None:
        """Stop should join API thread."""
        server = LiveInteractionServer()
        server._running = True
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        server._api_thread = mock_thread
        server.stop()
        mock_thread.join.assert_called_once_with(timeout=5.0)
        assert server._api_thread is None

    def test_stop_with_ui_thread(self) -> None:
        """Stop should clear UI thread."""
        server = LiveInteractionServer()
        server._running = True
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        server._ui_thread = mock_thread
        server.stop()
        assert server._ui_thread is None


class TestClientExtended:
    """Additional tests for client uncovered methods."""

    @pytest.fixture
    def client_with_session(self) -> LiveInteractionClient:
        """Create a client with a mocked session."""
        client = LiveInteractionClient()
        mock_session = MagicMock()
        client._session = mock_session
        return client

    def test_list_individuals(self, client_with_session: LiveInteractionClient) -> None:
        """list_individuals should call GET /individuals."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"individuals": [{"id": "1", "name": "Sarah"}]}
        client_with_session._session.get.return_value = mock_response

        result = client_with_session.list_individuals()
        client_with_session._session.get.assert_called_once_with("/individuals")
        assert result == [{"id": "1", "name": "Sarah"}]

    def test_get_individual(self, client_with_session: LiveInteractionClient) -> None:
        """get_individual should call GET /individuals/:id."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "1", "name": "Sarah"}
        client_with_session._session.get.return_value = mock_response

        result = client_with_session.get_individual("1")
        client_with_session._session.get.assert_called_once_with("/individuals/1")
        assert result["name"] == "Sarah"

    def test_create_individual(self, client_with_session: LiveInteractionClient) -> None:
        """create_individual should call POST /individuals."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "1"}
        client_with_session._session.post.return_value = mock_response

        result = client_with_session.create_individual(name="Sarah")
        client_with_session._session.post.assert_called_once_with("/individuals", json={"name": "Sarah"})
        assert result["id"] == "1"

    def test_update_emotions(self, client_with_session: LiveInteractionClient) -> None:
        """update_emotions should call PATCH with emotions data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"emotions": {"proud": 0.8}}
        client_with_session._session.patch.return_value = mock_response

        result = client_with_session.update_emotions("1", {"proud": 0.8})
        expected_url = "/individuals/1/emotions"
        expected_json = {"emotions": {"proud": 0.8}}
        client_with_session._session.patch.assert_called_once_with(expected_url, json=expected_json)
        assert "emotions" in result

    def test_update_emotions_with_fill(self, client_with_session: LiveInteractionClient) -> None:
        """update_emotions with fill should include fill parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        client_with_session._session.patch.return_value = mock_response

        client_with_session.update_emotions("1", {"proud": 0.8}, fill=0.0)
        call_args = client_with_session._session.patch.call_args
        json_data = call_args[1]["json"]
        assert json_data["fill"] == 0.0
        assert json_data["emotions"] == {"proud": 0.8}

    def test_create_session(self, client_with_session: LiveInteractionClient) -> None:
        """create_session should call POST /sessions."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"session_id": "s1"}
        client_with_session._session.post.return_value = mock_response

        result = client_with_session.create_session("sit_1", ["ind_1"], human_id="h1")
        expected_json = {
            "situation_id": "sit_1",
            "individual_ids": ["ind_1"],
            "human_id": "h1",
        }
        client_with_session._session.post.assert_called_once_with("/sessions", json=expected_json)
        assert result["session_id"] == "s1"

    def test_send_message(self, client_with_session: LiveInteractionClient) -> None:
        """send_message should call POST /sessions/:id/messages."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"content": "Hi back"}
        client_with_session._session.post.return_value = mock_response

        result = client_with_session.send_message("s1", "Hello", sender_id="ind_1")
        expected_url = "/sessions/s1/messages"
        expected_json = {"content": "Hello", "sender_id": "ind_1"}
        client_with_session._session.post.assert_called_once_with(expected_url, json=expected_json)
        assert result["content"] == "Hi back"

    def test_get_messages(self, client_with_session: LiveInteractionClient) -> None:
        """get_messages should call GET /sessions/:id/messages."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messages": [{"content": "Hi"}]}
        client_with_session._session.get.return_value = mock_response

        result = client_with_session.get_messages("s1")
        client_with_session._session.get.assert_called_once_with("/sessions/s1/messages")
        assert len(result) == 1
        assert result[0]["content"] == "Hi"

    def test_close_without_session(self) -> None:
        """Close without session should be safe."""
        client = LiveInteractionClient()
        client.close()
        assert client._session is None

    def test_close_with_session(self) -> None:
        """Close should close and clear session."""
        client = LiveInteractionClient()
        mock_session = MagicMock()
        client._session = mock_session
        client.close()
        mock_session.close.assert_called_once()
        assert client._session is None
