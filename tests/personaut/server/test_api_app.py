"""Tests for FastAPI application — app factory, error handlers, lifespan, health."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from personaut.server.api.app import (
    AppState,
    create_app,
    generic_error_handler,
    get_app_state,
    personaut_error_handler,
    validation_error_handler,
)
from personaut.types.exceptions import (
    PersonautError,
    TrustThresholdError,
    ValidationError,
)


def _app_module():
    """Get the actual module object, not the `app` attribute."""
    return sys.modules["personaut.server.api.app"]


class TestAppState:
    """Tests for AppState."""

    def test_init(self) -> None:
        state = AppState()
        assert state.individuals == {}
        assert state.situations == {}
        assert state.relationships == {}
        assert state.sessions == {}
        assert state.storage is None
        assert state.persistence is None


class TestGetAppState:
    """Tests for get_app_state."""

    def test_raises_when_uninitialized(self) -> None:
        mod = _app_module()
        original = mod._app_state
        try:
            mod._app_state = None
            with pytest.raises(RuntimeError, match="not initialized"):
                get_app_state()
        finally:
            mod._app_state = original

    def test_returns_state_when_initialized(self) -> None:
        mod = _app_module()
        original = mod._app_state
        try:
            mod._app_state = AppState()
            state = get_app_state()
            assert isinstance(state, AppState)
        finally:
            mod._app_state = original


class TestCreateApp:
    """Tests for create_app factory."""

    def test_creates_fastapi_app(self) -> None:
        app = create_app(title="Test API", version="1.0.0")
        assert isinstance(app, FastAPI)
        assert app.title == "Test API"
        assert app.version == "1.0.0"

    def test_custom_cors_origins(self) -> None:
        app = create_app(cors_origins=["http://localhost:3000"])
        assert isinstance(app, FastAPI)

    def test_debug_mode(self) -> None:
        app = create_app(debug=True)
        assert app.debug is True


class TestErrorHandlers:
    """Tests for error handler functions."""

    @pytest.mark.asyncio
    async def test_personaut_error_400(self) -> None:
        request = MagicMock()
        exc = PersonautError("Something went wrong")
        response = await personaut_error_handler(request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_trust_threshold_error_403(self) -> None:
        request = MagicMock()
        exc = TrustThresholdError(required=0.8, actual=0.3)
        response = await personaut_error_handler(request, exc)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_validation_error_422(self) -> None:
        request = MagicMock()
        exc = ValidationError("Invalid data")
        response = await personaut_error_handler(request, exc)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validation_error_handler_with_errors(self) -> None:
        request = MagicMock()
        exc = MagicMock()
        exc.errors.return_value = [
            {"loc": ["body", "name"], "msg": "field required", "input": None},
        ]
        response = await validation_error_handler(request, exc)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validation_error_handler_no_errors(self) -> None:
        request = MagicMock()
        exc = Exception("plain error")
        response = await validation_error_handler(request, exc)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generic_error_handler(self) -> None:
        request = MagicMock()
        exc = Exception("unexpected")
        response = await generic_error_handler(request, exc)
        assert response.status_code == 500


class TestHealthEndpoint:
    """Integration test for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        app = create_app(version="1.2.3")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "1.2.3"


class TestLifespan:
    """Tests for lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_memory_mode(self) -> None:
        """In-memory mode should work without a database file."""
        with patch.dict(os.environ, {"PERSONAUT_STORAGE_TYPE": "memory"}):
            app = create_app()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/health")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lifespan_sqlite_mode(self, tmp_path) -> None:
        """SQLite mode should create db and hydrate state."""
        db_path = str(tmp_path / "test.db")
        with patch.dict(
            os.environ,
            {
                "PERSONAUT_STORAGE_TYPE": "sqlite",
                "PERSONAUT_STORAGE_PATH": db_path,
            },
        ):
            app = create_app()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/health")
                assert response.status_code == 200
