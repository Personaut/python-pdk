"""Tests for the Flask UI app factory and registration."""

from __future__ import annotations

import pytest


class TestCreateUIApp:
    """Verify app creation and basic wiring."""

    def test_create_app(self, app) -> None:
        """App factory should produce a Flask app."""
        assert app is not None
        assert app.config["TESTING"] is True

    def test_api_base_url_config(self, app) -> None:
        """API_BASE_URL should be set from the factory argument."""
        assert app.config["API_BASE_URL"] == "http://mock:8000/api"

    def test_secret_key_set(self, app) -> None:
        """A secret key should always be generated."""
        assert app.config["SECRET_KEY"]

    def test_health_endpoint(self, client) -> None:
        """GET /health should return 200 with JSON status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["ui"] is True


class TestBlueprintRegistration:
    """All expected blueprints should be registered."""

    EXPECTED_BLUEPRINTS = [
        "dashboard",
        "individuals",
        "situations",
        "relationships",
        "chat",
        "simulations",
    ]

    @pytest.mark.parametrize("bp_name", EXPECTED_BLUEPRINTS)
    def test_blueprint_registered(self, app, bp_name: str) -> None:
        assert bp_name in app.blueprints, f"Blueprint '{bp_name}' not registered"
