"""Tests for WebSocket functionality."""

from __future__ import annotations


class TestConnectionManager:
    """Tests for ConnectionManager."""

    def test_create_manager(self) -> None:
        """Test creating a connection manager."""
        from personaut.server.api.routes.websocket import ConnectionManager

        manager = ConnectionManager()
        assert manager.active_connections == {}
        assert manager.subscriptions == {}

    def test_get_connection_count_empty(self) -> None:
        """Test connection count with no connections."""
        from personaut.server.api.routes.websocket import ConnectionManager

        manager = ConnectionManager()
        assert manager.get_connection_count() == 0

    def test_get_session_connections_empty(self) -> None:
        """Test session connection count with no connections."""
        from personaut.server.api.routes.websocket import ConnectionManager

        manager = ConnectionManager()
        assert manager.get_session_connections("test_session") == 0


class TestWebSocketRouter:
    """Tests for WebSocket router registration."""

    def test_router_exists(self) -> None:
        """Test that the router is properly defined."""
        from personaut.server.api.routes.websocket import router

        assert router is not None

    def test_get_connection_manager(self) -> None:
        """Test getting the global connection manager."""
        from personaut.server.api.routes.websocket import (
            get_connection_manager,
            manager,
        )

        assert get_connection_manager() is manager


class TestNotificationFunctions:
    """Tests for notification functions exist."""

    def test_notify_funcs_exist(self) -> None:
        """Test notification functions are exported."""
        from personaut.server.api.routes.websocket import (
            notify_emotional_state_change,
            notify_new_message,
            notify_session_ended,
            notify_trigger_activation,
        )

        # Just verify they're callable
        assert callable(notify_emotional_state_change)
        assert callable(notify_trigger_activation)
        assert callable(notify_new_message)
        assert callable(notify_session_ended)


class TestWebSocketExports:
    """Tests for module exports."""

    def test_all_exports(self) -> None:
        """Test all expected items are exported."""
        from personaut.server.api.routes import websocket

        assert hasattr(websocket, "router")
        assert hasattr(websocket, "manager")
        assert hasattr(websocket, "get_connection_manager")
        assert hasattr(websocket, "ConnectionManager")
