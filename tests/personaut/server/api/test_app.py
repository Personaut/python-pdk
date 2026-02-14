"""Tests for FastAPI application."""

from __future__ import annotations

import pytest


class TestAppCreation:
    """Tests for application creation."""

    def test_create_app(self) -> None:
        """Test creating the FastAPI app."""
        from personaut.server.api.app import create_app

        app = create_app()
        assert app.title == "Personaut API"
        assert app.version == "0.1.0"

    def test_create_app_custom_title(self) -> None:
        """Test creating app with custom title."""
        from personaut.server.api.app import create_app

        app = create_app(title="Custom API", version="1.0.0")
        assert app.title == "Custom API"
        assert app.version == "1.0.0"

    def test_create_app_debug_mode(self) -> None:
        """Test creating app in debug mode."""
        from personaut.server.api.app import create_app

        app = create_app(debug=True)
        assert app.debug is True

    def test_app_has_health_endpoint(self) -> None:
        """Test app has health check endpoint."""
        from personaut.server.api.app import create_app

        app = create_app()
        routes = [route.path for route in app.routes]
        assert "/api/health" in routes

    def test_app_has_docs_endpoints(self) -> None:
        """Test app has documentation endpoints."""
        from personaut.server.api.app import create_app

        app = create_app()
        assert app.docs_url == "/api/docs"
        assert app.redoc_url == "/api/redoc"
        assert app.openapi_url == "/api/openapi.json"


class TestAppState:
    """Tests for application state."""

    def test_app_state_creation(self) -> None:
        """Test creating app state."""
        from personaut.server.api.app import AppState

        state = AppState()
        assert state.individuals == {}
        assert state.situations == {}
        assert state.relationships == {}
        assert state.sessions == {}

    def test_get_app_state_before_init_raises(self) -> None:
        """Test getting state before initialization raises error."""
        import sys

        # Import the module first to ensure it's loaded
        from personaut.server.api.app import get_app_state

        # Access the actual module through sys.modules
        app_module = sys.modules["personaut.server.api.app"]

        # Ensure state is None
        original_state = app_module._app_state
        app_module._app_state = None

        try:
            with pytest.raises(RuntimeError, match="not initialized"):
                get_app_state()
        finally:
            app_module._app_state = original_state


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_default_cors_allows_all(self) -> None:
        """Test default CORS allows all origins."""
        from personaut.server.api.app import create_app

        app = create_app()
        # Check middleware is configured
        assert len(app.user_middleware) > 0

    def test_custom_cors_origins(self) -> None:
        """Test custom CORS origins."""
        from personaut.server.api.app import create_app

        app = create_app(cors_origins=["http://localhost:3000"])
        assert len(app.user_middleware) > 0


class TestRouterRegistration:
    """Tests for router registration."""

    def test_individuals_router_registered(self) -> None:
        """Test individuals router is registered."""
        from personaut.server.api.app import create_app

        app = create_app()
        routes = [route.path for route in app.routes if hasattr(route, "path")]
        assert any("/api/individuals" in route for route in routes)

    def test_situations_router_registered(self) -> None:
        """Test situations router is registered."""
        from personaut.server.api.app import create_app

        app = create_app()
        routes = [route.path for route in app.routes if hasattr(route, "path")]
        assert any("/api/situations" in route for route in routes)

    def test_relationships_router_registered(self) -> None:
        """Test relationships router is registered."""
        from personaut.server.api.app import create_app

        app = create_app()
        routes = [route.path for route in app.routes if hasattr(route, "path")]
        assert any("/api/relationships" in route for route in routes)

    def test_sessions_router_registered(self) -> None:
        """Test sessions router is registered."""
        from personaut.server.api.app import create_app

        app = create_app()
        routes = [route.path for route in app.routes if hasattr(route, "path")]
        assert any("/api/sessions" in route for route in routes)
