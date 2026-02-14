"""Tests for the dashboard view."""

from __future__ import annotations


class TestDashboard:
    """Smoke tests for the dashboard route."""

    def test_index_returns_200(self, client) -> None:
        """GET / should render the dashboard."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_contains_stats(self, client) -> None:
        """Dashboard page should include key stat sections."""
        resp = client.get("/")
        html = resp.data.decode()
        # The template should render the stats we seeded (2 individuals, 1 situation)
        assert "Individuals" in html or "individuals" in html.lower()

    def test_index_with_no_api(self, app) -> None:
        """Dashboard should render gracefully even when API returns None."""
        from unittest.mock import patch

        with patch("personaut.server.ui.views.api_helpers.api_get", return_value=None):
            client = app.test_client()
            resp = client.get("/")
            assert resp.status_code == 200
