"""Tests for the situations view."""

from __future__ import annotations


class TestSituationsListView:
    """Tests for GET /situations/."""

    def test_list_returns_200(self, client) -> None:
        resp = client.get("/situations/")
        assert resp.status_code == 200

    def test_list_renders_page(self, client) -> None:
        resp = client.get("/situations/")
        html = resp.data.decode()
        assert "Situations" in html or "situations" in html.lower()


class TestSituationsCreateView:
    """Tests for GET/POST /situations/create."""

    def test_create_get_returns_200(self, client) -> None:
        resp = client.get("/situations/create")
        assert resp.status_code == 200

    def test_create_form_contains_modalities(self, client) -> None:
        resp = client.get("/situations/create")
        html = resp.data.decode()
        assert "in_person" in html or "In Person" in html

    def test_create_post_redirects(self, client, mock_router) -> None:
        mock_router.post_routes["/situations"] = {
            "id": "sit_new",
            "description": "New place",
        }
        resp = client.post(
            "/situations/create",
            data={
                "description": "A new place",
                "modality": "in_person",
                "location": "Test Location",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_create_post_with_context(self, client, mock_router) -> None:
        """Context fields from the form should be collected."""
        mock_router.post_routes["/situations"] = {"id": "sit_ctx"}
        resp = client.post(
            "/situations/create",
            data={
                "description": "Context test",
                "modality": "text_message",
                "ctx_time_of_day": "evening",
                "ctx_weather": "sunny",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        # Verify the API was called with context data
        post_calls = [(path, data) for path, data in mock_router.post_calls if path == "/situations"]
        assert len(post_calls) >= 1
        assert post_calls[0][1]["context"]["time_of_day"] == "evening"


class TestSituationsDetailView:
    """Tests for GET /situations/<id>."""

    def test_detail_returns_200(self, client) -> None:
        resp = client.get("/situations/sit_test_001")
        assert resp.status_code == 200

    def test_detail_renders_page(self, client) -> None:
        """Detail page should render (content depends on template)."""
        resp = client.get("/situations/sit_test_001")
        html = resp.data.decode()
        assert len(html) > 200  # Not a blank page

    def test_detail_not_found(self, client) -> None:
        resp = client.get("/situations/nonexistent_id")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "not found" in html.lower()


class TestSituationsEditView:
    """Tests for GET/POST /situations/<id>/edit."""

    def test_edit_get_returns_200(self, client) -> None:
        resp = client.get("/situations/sit_test_001/edit")
        assert resp.status_code == 200

    def test_edit_post_redirects(self, client) -> None:
        resp = client.post(
            "/situations/sit_test_001/edit",
            data={
                "description": "Updated",
                "modality": "text_message",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_edit_nonexistent_shows_not_found(self, client) -> None:
        resp = client.get("/situations/nonexistent/edit")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "not found" in html.lower()
